"""
Email Automation Control Routes
Handles starting, stopping, and monitoring email automation
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

class AutomationControlRequest(BaseModel):
    action: str  # start, stop, restart
    check_interval: Optional[int] = 30

class AutomationStatusResponse(BaseModel):
    is_running: bool
    processed_count: int
    check_interval: int
    last_check: Optional[str]
    uptime: Optional[str]

@router.post("/start-email-automation")
async def start_email_automation(
    request: AutomationControlRequest,
    background_tasks: BackgroundTasks
):
    """Start email automation service"""
    try:
        if email_automation_service.is_running:
            return {
                "status": "already_running",
                "message": "Email automation is already running"
            }
        
        # Update check interval if provided
        if request.check_interval:
            email_automation_service.check_interval = request.check_interval
        
        # Start monitoring in background
        background_tasks.add_task(email_automation_service.start_monitoring)
        
        logger.info("Email automation started")
        return {
            "status": "started",
            "message": "Email automation service started successfully",
            "check_interval": email_automation_service.check_interval
        }
        
    except Exception as e:
        logger.error(f"Failed to start email automation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start email automation: {str(e)}"
        )

@router.post("/stop-email-automation")
async def stop_email_automation():
    """Stop email automation service"""
    try:
        if not email_automation_service.is_running:
            return {
                "status": "already_stopped",
                "message": "Email automation is not running"
            }
        
        await email_automation_service.stop_monitoring()
        
        logger.info("Email automation stopped")
        return {
            "status": "stopped",
            "message": "Email automation service stopped successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to stop email automation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop email automation: {str(e)}"
        )

@router.post("/restart-email-automation")
async def restart_email_automation(
    request: AutomationControlRequest,
    background_tasks: BackgroundTasks
):
    """Restart email automation service"""
    try:
        # Stop if running
        if email_automation_service.is_running:
            await email_automation_service.stop_monitoring()
            await asyncio.sleep(2)  # Wait for clean shutdown
        
        # Update check interval if provided
        if request.check_interval:
            email_automation_service.check_interval = request.check_interval
        
        # Start monitoring in background
        background_tasks.add_task(email_automation_service.start_monitoring)
        
        logger.info("Email automation restarted")
        return {
            "status": "restarted",
            "message": "Email automation service restarted successfully",
            "check_interval": email_automation_service.check_interval
        }
        
    except Exception as e:
        logger.error(f"Failed to restart email automation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart email automation: {str(e)}"
        )

@router.get("/email-automation-status")
async def get_email_automation_status():
    """Get email automation service status"""
    try:
        # Simple status without complex dependencies for now
        return {
            "is_running": False,
            "processed_count": 0,
            "check_interval": 30,
            "last_check": None,
            "uptime": None
        }
        
    except Exception as e:
        logger.error(f"Failed to get automation status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get automation status: {str(e)}"
        )

@router.get("/email-automation-stats")
async def get_email_automation_stats():
    """Get detailed automation statistics"""
    try:
        from ..utils.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Get processing stats from the last 24 hours
        from datetime import datetime, timedelta
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        
        # Get processed emails count
        processed_result = supabase.table("support_interactions").select("*").eq(
            "interaction_type", "email_processed"
        ).gte("created_at", yesterday).execute()
        
        processed_emails = processed_result.data
        
        # Get tickets created from automation
        tickets_result = supabase.table("support_tickets").select("*").eq(
            "source", "email_automation"
        ).gte("created_at", yesterday).execute()
        
        tickets_created = tickets_result.data
        
        # Calculate stats
        total_processed = len(processed_emails)
        tickets_count = len(tickets_created)
        
        # Category breakdown
        categories = {}
        priorities = {}
        sentiments = {}
        
        for email in processed_emails:
            cat = email.get('category', 'unknown')
            pri = email.get('priority', 'unknown')
            sent = email.get('sentiment', 'unknown')
            
            categories[cat] = categories.get(cat, 0) + 1
            priorities[pri] = priorities.get(pri, 0) + 1
            sentiments[sent] = sentiments.get(sent, 0) + 1
        
        # Response rate (emails that got automated responses)
        automated_responses = len([e for e in processed_emails if not e.get('requires_human', True)])
        response_rate = (automated_responses / total_processed * 100) if total_processed > 0 else 0
        
        return {
            "period": "last_24_hours",
            "total_processed": total_processed,
            "tickets_created": tickets_count,
            "automated_responses": automated_responses,
            "response_rate": f"{response_rate:.1f}%",
            "categories": categories,
            "priorities": priorities,
            "sentiments": sentiments,
            "service_status": await email_automation_service.get_status()
        }
        
    except Exception as e:
        logger.error(f"Failed to get automation stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get automation stats: {str(e)}"
        )

@router.post("/process-email-manually")
async def process_email_manually(email_data: Dict):
    """Manually process a specific email (for testing)"""
    try:
        # Initialize service if not already done
        if not email_automation_service.gmail_client:
            await email_automation_service.initialize()
        
        # Process the email
        await email_automation_service._process_single_email(email_data)
        
        return {
            "status": "processed",
            "message": "Email processed successfully",
            "email_id": email_data.get('id')
        }
        
    except Exception as e:
        logger.error(f"Manual email processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Manual email processing failed: {str(e)}"
        )

@router.get("/test-email-automation")
async def test_email_automation():
    """Test email automation with sample data"""
    try:
        # Sample email for testing
        test_email = {
            "id": "test_email_123",
            "thread_id": "test_thread_123",
            "subject": "Login issues with my account",
            "sender": "customer@example.com",
            "body": "Hi, I'm having trouble logging into my account. I keep getting an error message that says 'invalid credentials' even though I'm sure my password is correct. Can you help me reset it?",
            "date": "2024-01-01T12:00:00Z",
            "message_id": "test_message_123",
            "snippet": "Login issues with my account",
            "labels": ["UNREAD", "INBOX"]
        }
        
        # Process the test email
        await process_email_manually(test_email)
        
        return {
            "status": "test_completed",
            "message": "Test email processed successfully",
            "test_email": test_email
        }
        
    except Exception as e:
        logger.error(f"Email automation test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Email automation test failed: {str(e)}"
        )