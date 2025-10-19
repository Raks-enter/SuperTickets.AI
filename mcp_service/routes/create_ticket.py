"""
Ticket Creation Route
Handles creating support tickets via SuperOps GraphQL API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
try:
    from pydantic import EmailStr
except ImportError:
    from email_validator import EmailStr
from typing import Optional, Dict, Any
import logging
import uuid
from datetime import datetime

from ..utils.superops_api import SuperOpsClient
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

class CreateTicketRequest(BaseModel):
    title: str = Field(..., description="Ticket title/summary")
    description: str = Field(..., description="Detailed ticket description")
    priority: str = Field(..., pattern="^(low|medium|high|critical)$", description="Ticket priority level")
    category: str = Field(..., description="Issue category")
    customer_email: EmailStr = Field(..., description="Customer email address")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    source: str = Field("email", pattern="^(email|phone_call|chat|web)$", description="Source of the ticket")
    escalate_immediately: bool = Field(False, description="Whether to escalate immediately")
    tags: Optional[list] = Field(default_factory=list, description="Additional tags")
    attachments: Optional[list] = Field(default_factory=list, description="File attachments")

class CreateTicketResponse(BaseModel):
    ticket_id: str
    ticket_url: str
    status: str
    priority: str
    assigned_agent: Optional[str]
    estimated_resolution_time: str
    created_at: datetime

@router.post("/create_ticket", response_model=CreateTicketResponse)
async def create_support_ticket(
    request: CreateTicketRequest,
    supabase=Depends(get_supabase_client)
):
    """
    Create a new support ticket in SuperOps
    
    This endpoint creates a support ticket with the provided information
    and returns the ticket details including ID and tracking URL.
    """
    try:
        logger.info(f"Creating ticket: title='{request.title}', priority={request.priority}")
        
        # Initialize SuperOps client
        superops_client = SuperOpsClient()
        
        # Prepare ticket data
        ticket_data = {
            "title": request.title,
            "description": request.description,
            "priority": request.priority,
            "category": request.category,
            "customer": {
                "email": request.customer_email,
                "phone": request.customer_phone
            },
            "source": request.source,
            "tags": request.tags,
            "escalate_immediately": request.escalate_immediately,
            "attachments": request.attachments
        }
        
        # Create ticket via SuperOps API
        ticket_result = await superops_client.create_ticket(ticket_data)
        
        # Log ticket creation in Supabase
        await log_ticket_creation(
            supabase=supabase,
            ticket_id=ticket_result["ticket_id"],
            request_data=request.dict(),
            superops_response=ticket_result
        )
        
        response = CreateTicketResponse(
            ticket_id=ticket_result["ticket_id"],
            ticket_url=ticket_result["ticket_url"],
            status=ticket_result["status"],
            priority=ticket_result["priority"],
            assigned_agent=ticket_result.get("assigned_agent"),
            estimated_resolution_time=ticket_result["estimated_resolution_time"],
            created_at=datetime.fromisoformat(ticket_result["created_at"])
        )
        
        logger.info(f"Ticket created successfully: {ticket_result['ticket_id']}")
        return response
        
    except Exception as e:
        logger.error(f"Ticket creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create ticket: {str(e)}"
        )

@router.post("/schedule_callback")
async def schedule_customer_callback(
    request: Dict[str, Any],
    supabase=Depends(get_supabase_client)
):
    """
    Schedule a callback for customer follow-up
    
    Creates a callback task in SuperOps for agent follow-up
    with the customer at the specified time.
    """
    try:
        customer_phone = request.get("customer_phone")
        customer_email = request.get("customer_email")
        priority = request.get("priority", "24_hours")
        ticket_id = request.get("ticket_id")
        callback_reason = request.get("callback_reason", "")
        callback_type = request.get("callback_type", "proactive_followup")
        
        if not customer_phone and not customer_email:
            raise HTTPException(
                status_code=400, 
                detail="Either customer_phone or customer_email is required"
            )
        
        logger.info(f"Scheduling callback: priority={priority}, type={callback_type}")
        
        # Initialize SuperOps client
        superops_client = SuperOpsClient()
        
        # Calculate callback time based on priority
        callback_time = calculate_callback_time(priority)
        
        # Create callback task
        callback_data = {
            "type": "callback",
            "priority": priority,
            "scheduled_time": callback_time,
            "customer_phone": customer_phone,
            "customer_email": customer_email,
            "ticket_id": ticket_id,
            "reason": callback_reason,
            "callback_type": callback_type,
            "instructions": f"Follow up with customer regarding {callback_reason}"
        }
        
        callback_result = await superops_client.create_callback_task(callback_data)
        
        # Log callback scheduling
        await log_callback_scheduled(
            supabase=supabase,
            callback_id=callback_result["callback_id"],
            callback_data=callback_data
        )
        
        logger.info(f"Callback scheduled: {callback_result['callback_id']}")
        return callback_result
        
    except Exception as e:
        logger.error(f"Callback scheduling failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule callback: {str(e)}"
        )

async def log_ticket_creation(supabase, ticket_id: str, request_data: dict, superops_response: dict):
    """Log ticket creation to Supabase for tracking"""
    try:
        log_data = {
            "id": str(uuid.uuid4()),
            "interaction_type": "ticket_created",
            "ticket_id": ticket_id,
            "customer_email": request_data["customer_email"],
            "customer_phone": request_data.get("customer_phone"),
            "issue_description": request_data["description"],
            "priority": request_data["priority"],
            "category": request_data["category"],
            "source": request_data["source"],
            "superops_response": superops_response,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("support_interactions").insert(log_data).execute()
        logger.info(f"Ticket creation logged: {ticket_id}")
        
    except Exception as e:
        logger.error(f"Failed to log ticket creation: {e}")

async def log_callback_scheduled(supabase, callback_id: str, callback_data: dict):
    """Log callback scheduling to Supabase"""
    try:
        log_data = {
            "id": str(uuid.uuid4()),
            "interaction_type": "callback_scheduled",
            "callback_id": callback_id,
            "customer_phone": callback_data.get("customer_phone"),
            "customer_email": callback_data.get("customer_email"),
            "ticket_id": callback_data.get("ticket_id"),
            "callback_priority": callback_data["priority"],
            "callback_type": callback_data["callback_type"],
            "scheduled_time": callback_data["scheduled_time"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("support_interactions").insert(log_data).execute()
        logger.info(f"Callback scheduling logged: {callback_id}")
        
    except Exception as e:
        logger.error(f"Failed to log callback scheduling: {e}")

def calculate_callback_time(priority: str) -> str:
    """Calculate callback time based on priority"""
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    
    if priority == "immediate":
        callback_time = now + timedelta(minutes=30)
    elif priority == "within_2_hours":
        callback_time = now + timedelta(hours=2)
    elif priority == "24_hours":
        callback_time = now + timedelta(hours=24)
    elif priority == "next_business_day":
        # Calculate next business day (Monday-Friday)
        days_ahead = 1
        while (now + timedelta(days=days_ahead)).weekday() > 4:  # 0-6, Monday is 0
            days_ahead += 1
        callback_time = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0)
    else:
        callback_time = now + timedelta(hours=24)  # Default to 24 hours
    
    return callback_time.isoformat()