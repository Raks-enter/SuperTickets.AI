"""
Email Sending Route
Handles sending emails via Gmail API
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
from datetime import datetime

from ..utils.gmail_client import GmailClient
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

class SendEmailRequest(BaseModel):
    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    thread_id: Optional[str] = Field(None, description="Gmail thread ID for replies")
    template: Optional[str] = Field(None, description="Email template to use")
    attachments: Optional[List[str]] = Field(default_factory=list, description="File paths for attachments")
    cc: Optional[List[EmailStr]] = Field(default_factory=list, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(default_factory=list, description="BCC recipients")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to address")

class SendEmailResponse(BaseModel):
    message_id: str
    thread_id: str
    status: str
    sent_at: datetime
    recipient: str
    subject: str

@router.post("/send_email", response_model=SendEmailResponse)
async def send_email_response(
    request: SendEmailRequest,
    supabase=Depends(get_supabase_client)
):
    """
    Send email response via Gmail API
    
    This endpoint sends emails using the Gmail API with support for
    threading, templates, and attachments.
    """
    try:
        logger.info(f"Sending email to {request.to}: '{request.subject}'")
        
        # Initialize Gmail client
        gmail_client = GmailClient()
        
        # Process email template if specified
        if request.template:
            processed_body = await process_email_template(
                template_name=request.template,
                body=request.body,
                recipient=request.to
            )
        else:
            processed_body = request.body
        
        # Prepare email data
        email_data = {
            "to": request.to,
            "subject": request.subject,
            "body": processed_body,
            "thread_id": request.thread_id,
            "attachments": request.attachments,
            "cc": request.cc,
            "bcc": request.bcc,
            "reply_to": request.reply_to
        }
        
        # Send email via Gmail API
        send_result = await gmail_client.send_email(email_data)
        
        # Log email sending
        await log_email_sent(
            supabase=supabase,
            email_data=email_data,
            send_result=send_result
        )
        
        response = SendEmailResponse(
            message_id=send_result["message_id"],
            thread_id=send_result["thread_id"],
            status="sent",
            sent_at=datetime.utcnow(),
            recipient=request.to,
            subject=request.subject
        )
        
        logger.info(f"Email sent successfully: {send_result['message_id']}")
        return response
        
    except Exception as e:
        logger.error(f"Email sending failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )

@router.post("/send_bulk_email")
async def send_bulk_emails(
    request: Dict[str, Any],
    supabase=Depends(get_supabase_client)
):
    """
    Send bulk emails to multiple recipients
    
    Sends the same email content to multiple recipients with
    personalization support.
    """
    try:
        recipients = request.get("recipients", [])
        subject_template = request.get("subject", "")
        body_template = request.get("body", "")
        template_name = request.get("template")
        
        if not recipients:
            raise HTTPException(status_code=400, detail="recipients list is required")
        
        logger.info(f"Sending bulk email to {len(recipients)} recipients")
        
        gmail_client = GmailClient()
        results = []
        
        for recipient_data in recipients:
            try:
                recipient_email = recipient_data.get("email")
                personalization = recipient_data.get("personalization", {})
                
                # Personalize subject and body
                personalized_subject = personalize_content(subject_template, personalization)
                personalized_body = personalize_content(body_template, personalization)
                
                # Process template if specified
                if template_name:
                    personalized_body = await process_email_template(
                        template_name=template_name,
                        body=personalized_body,
                        recipient=recipient_email,
                        personalization=personalization
                    )
                
                # Send individual email
                email_data = {
                    "to": recipient_email,
                    "subject": personalized_subject,
                    "body": personalized_body
                }
                
                send_result = await gmail_client.send_email(email_data)
                results.append({
                    "recipient": recipient_email,
                    "status": "sent",
                    "message_id": send_result["message_id"]
                })
                
                # Log individual email
                await log_email_sent(supabase, email_data, send_result)
                
            except Exception as e:
                logger.error(f"Failed to send email to {recipient_email}: {e}")
                results.append({
                    "recipient": recipient_email,
                    "status": "failed",
                    "error": str(e)
                })
        
        successful_sends = len([r for r in results if r["status"] == "sent"])
        logger.info(f"Bulk email completed: {successful_sends}/{len(recipients)} sent")
        
        return {
            "total_recipients": len(recipients),
            "successful_sends": successful_sends,
            "failed_sends": len(recipients) - successful_sends,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Bulk email sending failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Bulk email sending failed: {str(e)}"
        )

@router.get("/check-gmail-status")
async def check_gmail_integration_status():
    """
    Check if Gmail integration is properly configured and working
    """
    try:
        gmail_client = GmailClient()
        
        # Try to get user profile to test connection
        profile = gmail_client.service.users().getProfile(userId='me').execute()
        
        # Get basic stats
        stats = {
            "connected": True,
            "email_address": profile.get("emailAddress", "Unknown"),
            "messages_total": profile.get("messagesTotal", 0),
            "threads_total": profile.get("threadsTotal", 0),
            "processed": 0,  # Would come from your analytics
            "auto_responses": 0,  # Would come from your analytics  
            "tickets_created": 0,  # Would come from your analytics
            "response_rate": "0%"  # Would be calculated
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Gmail status check failed: {e}")
        return {
            "connected": False,
            "error": str(e),
            "stats": None
        }

async def process_email_template(
    template_name: str, 
    body: str, 
    recipient: str, 
    personalization: Dict = None
) -> str:
    """Process email template with personalization"""
    try:
        # Load template configuration
        templates = {
            "solution_response": {
                "header": "Hello {customer_name},\n\nThank you for contacting support.",
                "footer": "\n\nBest regards,\nSuperTickets.AI Support Team"
            },
            "ticket_created": {
                "header": "Hello {customer_name},\n\nWe've received your support request.",
                "footer": "\n\nBest regards,\nSuperTickets.AI Support Team\nTicket #{ticket_id}"
            },
            "call_followup_solution": {
                "header": "Hello {customer_name},\n\nThank you for calling our support line.",
                "footer": "\n\nBest regards,\n{agent_name}\nSuperTickets.AI Support Team"
            },
            "call_ticket_confirmation": {
                "header": "Hello {customer_name},\n\nThis confirms your support ticket creation.",
                "footer": "\n\nBest regards,\nSuperTickets.AI Support Team\nTicket #{ticket_id}"
            }
        }
        
        if template_name not in templates:
            return body
        
        template = templates[template_name]
        
        # Apply personalization
        if personalization:
            header = template["header"].format(**personalization)
            footer = template["footer"].format(**personalization)
        else:
            # Use default values
            default_values = {
                "customer_name": "Valued Customer",
                "agent_name": "Support Agent",
                "ticket_id": "TBD"
            }
            header = template["header"].format(**default_values)
            footer = template["footer"].format(**default_values)
        
        return f"{header}\n\n{body}{footer}"
        
    except Exception as e:
        logger.error(f"Template processing failed: {e}")
        return body  # Return original body if template processing fails

def personalize_content(content: str, personalization: Dict) -> str:
    """Personalize content with variable substitution"""
    try:
        if not personalization:
            return content
        
        for key, value in personalization.items():
            placeholder = "{" + key + "}"
            content = content.replace(placeholder, str(value))
        
        return content
        
    except Exception as e:
        logger.error(f"Content personalization failed: {e}")
        return content

async def log_email_sent(supabase, email_data: dict, send_result: dict):
    """Log email sending to Supabase for tracking"""
    try:
        log_data = {
            "id": str(uuid.uuid4()),
            "interaction_type": "email_sent",
            "recipient_email": email_data["to"],
            "subject": email_data["subject"],
            "message_id": send_result["message_id"],
            "thread_id": send_result.get("thread_id"),
            "gmail_response": send_result,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("support_interactions").insert(log_data).execute()
        logger.info(f"Email sending logged: {send_result['message_id']}")
        
    except Exception as e:
        logger.error(f"Failed to log email sending: {e}")

# Email Automation Status (Auto-Running)
import asyncio
from datetime import datetime, timedelta

# Global automation state - starts automatically
automation_state = {
    "is_running": True,  # Auto-start
    "processed_count": 0,
    "check_interval": 30,
    "start_time": datetime.utcnow(),
    "last_check": datetime.utcnow().isoformat()
}

@router.get("/email-automation-status")
async def get_email_automation_status():
    """Get email automation service status"""
    return {
        "is_running": automation_state["is_running"],
        "processed_count": automation_state["processed_count"],
        "check_interval": automation_state["check_interval"],
        "last_check": automation_state["last_check"],
        "uptime": _calculate_uptime() if automation_state["start_time"] else None,
        "gmail_connected": await _check_gmail_connection()
    }

@router.get("/email-automation-stats")
async def get_email_automation_stats():
    """Get detailed automation statistics from real service"""
    try:
        from ..services.email_automation_service import email_automation_service
        
        # Get stats from real automation service
        service_stats = await email_automation_service.get_status()
        
        # Get database stats
        supabase = get_supabase_client()
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        
        # Get processed emails
        processed_result = supabase.table("support_interactions").select("*").eq(
            "interaction_type", "email_processed"
        ).gte("created_at", yesterday).execute()
        
        processed_emails = processed_result.data or []
        
        # Get sent emails
        sent_result = supabase.table("support_interactions").select("*").eq(
            "interaction_type", "email_sent"
        ).gte("created_at", yesterday).execute()
        
        sent_emails = sent_result.data or []
        
        # Get tickets
        tickets_result = supabase.table("support_tickets").select("*").eq(
            "source", "email_automation"
        ).gte("created_at", yesterday).execute()
        
        tickets = tickets_result.data or []
        
        # Calculate categories from real data
        categories = {}
        priorities = {}
        sentiments = {}
        
        for email in processed_emails:
            # Extract metadata if available
            metadata = email.get('metadata', {})
            if isinstance(metadata, dict):
                cat = metadata.get('category', 'general')
                pri = metadata.get('priority', 'medium')
                sent = metadata.get('sentiment', 'neutral')
                
                categories[cat] = categories.get(cat, 0) + 1
                priorities[pri] = priorities.get(pri, 0) + 1
                sentiments[sent] = sentiments.get(sent, 0) + 1
        
        # Calculate response rate
        total_processed = len(processed_emails)
        automated_responses = len(sent_emails)
        response_rate = f"{(automated_responses / total_processed * 100):.1f}%" if total_processed > 0 else "0%"
        
        return {
            "period": "last_24_hours",
            "total_processed": total_processed,
            "tickets_created": len(tickets),
            "automated_responses": automated_responses,
            "response_rate": response_rate,
            "categories": categories,
            "priorities": priorities,
            "sentiments": sentiments,
            "service_status": service_stats
        }
    except Exception as e:
        logger.error(f"Failed to get automation stats: {e}")
        return {
            "period": "last_24_hours",
            "total_processed": 0,
            "tickets_created": 0,
            "automated_responses": 0,
            "response_rate": "0%",
            "categories": {},
            "priorities": {},
            "sentiments": {},
            "service_status": {
                "is_running": False,
                "processed_count": 0,
                "check_interval": 30
            }
        }

async def _check_gmail_connection():
    """Check if Gmail is properly connected"""
    try:
        from ..utils.gmail_client import GmailClient
        gmail_client = GmailClient()
        
        # Try to get user profile to test connection
        profile = gmail_client.service.users().getProfile(userId='me').execute()
        return True
    except Exception as e:
        logger.error(f"Gmail connection check failed: {e}")
        return False

def _calculate_uptime():
    """Calculate uptime in human readable format"""
    if not automation_state["start_time"]:
        return None
    
    uptime_seconds = (datetime.utcnow() - automation_state["start_time"]).total_seconds()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

@router.get("/ai-model-info")
async def get_ai_model_info():
    """Get AI model information"""
    try:
        from ..services.bedrock_ai_processor import BedrockAIProcessor
        
        ai_processor = BedrockAIProcessor()
        model_info = ai_processor.get_model_info()
        
        return {
            "ai_model": model_info,
            "features": [
                "Real-time email analysis",
                "Intelligent categorization", 
                "Sentiment analysis",
                "Intent recognition",
                "Contextual response generation",
                "AI-powered knowledge search"
            ],
            "upgrade": "Upgraded from rule-based to AWS Bedrock Claude 3"
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI model info: {e}")
        return {
            "ai_model": {
                "provider": "AWS Bedrock",
                "model": "Claude 3 Sonnet", 
                "status": "error"
            },
            "error": str(e)
        }