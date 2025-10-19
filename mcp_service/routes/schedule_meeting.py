"""
Meeting Scheduling Route
Handles scheduling meetings via Google Calendar API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
try:
    from pydantic import EmailStr
except ImportError:
    from email_validator import EmailStr
from typing import Optional, List, Dict, Any
import logging
import uuid
from datetime import datetime, timedelta

from ..utils.google_calendar import GoogleCalendarClient
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

class ScheduleMeetingRequest(BaseModel):
    customer_email: EmailStr = Field(..., description="Customer email for invitation")
    meeting_type: str = Field(..., pattern="^(support_followup|technical_review|escalation_call)$", description="Type of meeting")
    duration_minutes: int = Field(30, ge=15, le=120, description="Meeting duration in minutes")
    preferred_times: Optional[str] = Field(None, description="Preferred meeting times")
    ticket_id: Optional[str] = Field(None, description="Related ticket ID")
    meeting_description: Optional[str] = Field(None, description="Meeting description")
    attendees: Optional[List[EmailStr]] = Field(default_factory=list, description="Additional attendees")
    timezone: Optional[str] = Field("UTC", description="Customer timezone")

class ScheduleMeetingResponse(BaseModel):
    meeting_id: str
    calendar_event_id: str
    meeting_url: str
    scheduled_time: datetime
    duration_minutes: int
    attendees: List[str]
    status: str

@router.post("/schedule_meeting", response_model=ScheduleMeetingResponse)
async def schedule_support_meeting(
    request: ScheduleMeetingRequest,
    supabase=Depends(get_supabase_client)
):
    """
    Schedule meeting via Google Calendar
    
    This endpoint creates a calendar event and sends invitations
    to the customer and support team members.
    """
    try:
        logger.info(f"Scheduling meeting: type={request.meeting_type}, customer={request.customer_email}")
        
        # Initialize Google Calendar client
        calendar_client = GoogleCalendarClient()
        
        # Determine meeting time
        meeting_time = await determine_meeting_time(
            preferred_times=request.preferred_times,
            duration_minutes=request.duration_minutes,
            timezone=request.timezone
        )
        
        # Prepare meeting data
        meeting_data = {
            "summary": get_meeting_title(request.meeting_type, request.ticket_id),
            "description": get_meeting_description(request.meeting_type, request.meeting_description, request.ticket_id),
            "start_time": meeting_time,
            "duration_minutes": request.duration_minutes,
            "attendees": [request.customer_email] + request.attendees,
            "timezone": request.timezone,
            "meeting_type": request.meeting_type
        }
        
        # Create calendar event
        calendar_result = await calendar_client.create_meeting(meeting_data)
        
        # Generate meeting ID
        meeting_id = str(uuid.uuid4())
        
        # Log meeting scheduling
        await log_meeting_scheduled(
            supabase=supabase,
            meeting_id=meeting_id,
            request_data=request.dict(),
            calendar_result=calendar_result
        )
        
        response = ScheduleMeetingResponse(
            meeting_id=meeting_id,
            calendar_event_id=calendar_result["event_id"],
            meeting_url=calendar_result["meeting_url"],
            scheduled_time=datetime.fromisoformat(calendar_result["start_time"]),
            duration_minutes=request.duration_minutes,
            attendees=meeting_data["attendees"],
            status="scheduled"
        )
        
        logger.info(f"Meeting scheduled successfully: {meeting_id}")
        return response
        
    except Exception as e:
        logger.error(f"Meeting scheduling failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule meeting: {str(e)}"
        )

@router.post("/reschedule_meeting")
async def reschedule_meeting(
    meeting_id: str,
    new_time: datetime,
    reason: Optional[str] = None,
    supabase=Depends(get_supabase_client)
):
    """
    Reschedule an existing meeting
    
    Updates the calendar event with a new time and notifies attendees.
    """
    try:
        logger.info(f"Rescheduling meeting: {meeting_id}")
        
        # Get meeting details from database
        meeting_result = supabase.table("support_interactions")\
            .select("*")\
            .eq("meeting_id", meeting_id)\
            .execute()
        
        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        meeting_data = meeting_result.data[0]
        calendar_event_id = meeting_data.get("calendar_event_id")
        
        if not calendar_event_id:
            raise HTTPException(status_code=400, detail="Calendar event ID not found")
        
        # Initialize Google Calendar client
        calendar_client = GoogleCalendarClient()
        
        # Update calendar event
        update_result = await calendar_client.update_meeting(
            event_id=calendar_event_id,
            new_start_time=new_time,
            reason=reason
        )
        
        # Update database record
        update_data = {
            "scheduled_time": new_time.isoformat(),
            "reschedule_reason": reason,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("support_interactions")\
            .update(update_data)\
            .eq("meeting_id", meeting_id)\
            .execute()
        
        logger.info(f"Meeting rescheduled successfully: {meeting_id}")
        return {
            "meeting_id": meeting_id,
            "new_time": new_time,
            "status": "rescheduled",
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"Meeting rescheduling failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reschedule meeting: {str(e)}"
        )

@router.delete("/cancel_meeting/{meeting_id}")
async def cancel_meeting(
    meeting_id: str,
    reason: Optional[str] = None,
    supabase=Depends(get_supabase_client)
):
    """
    Cancel a scheduled meeting
    
    Cancels the calendar event and notifies attendees.
    """
    try:
        logger.info(f"Canceling meeting: {meeting_id}")
        
        # Get meeting details
        meeting_result = supabase.table("support_interactions")\
            .select("*")\
            .eq("meeting_id", meeting_id)\
            .execute()
        
        if not meeting_result.data:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        meeting_data = meeting_result.data[0]
        calendar_event_id = meeting_data.get("calendar_event_id")
        
        if calendar_event_id:
            # Initialize Google Calendar client
            calendar_client = GoogleCalendarClient()
            
            # Cancel calendar event
            await calendar_client.cancel_meeting(calendar_event_id, reason)
        
        # Update database record
        update_data = {
            "status": "cancelled",
            "cancellation_reason": reason,
            "cancelled_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("support_interactions")\
            .update(update_data)\
            .eq("meeting_id", meeting_id)\
            .execute()
        
        logger.info(f"Meeting cancelled successfully: {meeting_id}")
        return {
            "meeting_id": meeting_id,
            "status": "cancelled",
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"Meeting cancellation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel meeting: {str(e)}"
        )

async def determine_meeting_time(
    preferred_times: Optional[str],
    duration_minutes: int,
    timezone: str
) -> datetime:
    """Determine the best meeting time based on preferences"""
    try:
        now = datetime.utcnow()
        
        if preferred_times == "business_hours":
            # Schedule for next business day at 10 AM
            days_ahead = 1
            while (now + timedelta(days=days_ahead)).weekday() > 4:  # Skip weekends
                days_ahead += 1
            meeting_time = (now + timedelta(days=days_ahead)).replace(hour=10, minute=0, second=0, microsecond=0)
        
        elif preferred_times == "within_2_hours":
            # Schedule 2 hours from now
            meeting_time = now + timedelta(hours=2)
            # Round to next 30-minute mark
            if meeting_time.minute < 30:
                meeting_time = meeting_time.replace(minute=30, second=0, microsecond=0)
            else:
                meeting_time = meeting_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        elif preferred_times == "next_available":
            # Schedule for next hour
            meeting_time = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        
        else:
            # Default to 24 hours from now
            meeting_time = (now + timedelta(hours=24)).replace(minute=0, second=0, microsecond=0)
        
        return meeting_time
        
    except Exception as e:
        logger.error(f"Meeting time determination failed: {e}")
        # Fallback to 24 hours from now
        return (datetime.utcnow() + timedelta(hours=24)).replace(minute=0, second=0, microsecond=0)

def get_meeting_title(meeting_type: str, ticket_id: Optional[str]) -> str:
    """Generate meeting title based on type"""
    titles = {
        "support_followup": "Support Follow-up Meeting",
        "technical_review": "Technical Review Session",
        "escalation_call": "Escalation Call"
    }
    
    base_title = titles.get(meeting_type, "Support Meeting")
    
    if ticket_id:
        return f"{base_title} - Ticket #{ticket_id}"
    
    return base_title

def get_meeting_description(meeting_type: str, custom_description: Optional[str], ticket_id: Optional[str]) -> str:
    """Generate meeting description"""
    descriptions = {
        "support_followup": "Follow-up meeting to discuss your support request and ensure resolution.",
        "technical_review": "Technical review session to dive deeper into the technical aspects of your issue.",
        "escalation_call": "Escalation call to address your concern with senior technical staff."
    }
    
    base_description = descriptions.get(meeting_type, "Support meeting to discuss your request.")
    
    if custom_description:
        base_description += f"\n\nAdditional details: {custom_description}"
    
    if ticket_id:
        base_description += f"\n\nRelated ticket: #{ticket_id}"
    
    base_description += "\n\nPlease join the meeting at the scheduled time. If you need to reschedule, please contact support."
    
    return base_description

async def log_meeting_scheduled(supabase, meeting_id: str, request_data: dict, calendar_result: dict):
    """Log meeting scheduling to Supabase"""
    try:
        log_data = {
            "id": str(uuid.uuid4()),
            "interaction_type": "meeting_scheduled",
            "meeting_id": meeting_id,
            "customer_email": request_data["customer_email"],
            "meeting_type": request_data["meeting_type"],
            "scheduled_time": calendar_result["start_time"],
            "duration_minutes": request_data["duration_minutes"],
            "calendar_event_id": calendar_result["event_id"],
            "meeting_url": calendar_result["meeting_url"],
            "attendees": request_data.get("attendees", []),
            "ticket_id": request_data.get("ticket_id"),
            "calendar_response": calendar_result,
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("support_interactions").insert(log_data).execute()
        logger.info(f"Meeting scheduling logged: {meeting_id}")
        
    except Exception as e:
        logger.error(f"Failed to log meeting scheduling: {e}")