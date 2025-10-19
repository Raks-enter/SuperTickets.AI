"""
Email Reading and Parsing Routes
Handles reading emails from Gmail and parsing them for AI processing
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import uuid
from datetime import datetime, timedelta
import re
import json

from ..utils.gmail_client import GmailClient
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

class EmailMessage(BaseModel):
    id: str
    thread_id: str
    subject: str
    sender: str
    sender_email: str
    date: str
    body: str
    snippet: str
    labels: List[str]
    is_unread: bool
    parsed_content: Optional[Dict[str, Any]] = None

class EmailReadRequest(BaseModel):
    query: Optional[str] = Field("is:unread", description="Gmail search query")
    max_results: Optional[int] = Field(50, description="Maximum number of emails to retrieve")
    label_ids: Optional[List[str]] = Field(None, description="Specific label IDs to filter")
    parse_content: Optional[bool] = Field(True, description="Whether to parse email content for AI processing")

class EmailReadResponse(BaseModel):
    total_messages: int
    messages: List[EmailMessage]
    query_used: str
    retrieved_at: datetime

class EmailParseResponse(BaseModel):
    message_id: str
    customer_info: Dict[str, Any]
    issue_summary: str
    issue_category: str
    priority_level: str
    extracted_data: Dict[str, Any]
    suggested_actions: List[str]

@router.post("/read_emails", response_model=EmailReadResponse)
async def read_company_emails(
    request: EmailReadRequest,
    supabase=Depends(get_supabase_client)
):
    """
    Read emails from company Gmail account
    
    This endpoint retrieves emails from the connected Gmail account
    and optionally parses them for AI processing.
    """
    try:
        logger.info(f"Reading emails with query: '{request.query}', max: {request.max_results}")
        
        # Initialize Gmail client
        gmail_client = GmailClient()
        
        # Get messages from Gmail
        raw_messages = await gmail_client.get_messages(
            query=request.query,
            max_results=request.max_results,
            label_ids=request.label_ids
        )
        
        # Process and parse messages
        processed_messages = []
        for raw_msg in raw_messages:
            try:
                # Convert to EmailMessage format
                email_msg = EmailMessage(
                    id=raw_msg["id"],
                    thread_id=raw_msg["thread_id"],
                    subject=raw_msg["subject"],
                    sender=raw_msg["sender"],
                    sender_email=extract_email_address(raw_msg["sender"]),
                    date=raw_msg["date"],
                    body=raw_msg["body"],
                    snippet=raw_msg["snippet"],
                    labels=raw_msg["labels"],
                    is_unread="UNREAD" in raw_msg["labels"]
                )
                
                # Parse content for AI processing if requested
                if request.parse_content:
                    parsed_content = await parse_email_content(email_msg)
                    email_msg.parsed_content = parsed_content
                
                processed_messages.append(email_msg)
                
                # Log email retrieval
                await log_email_retrieved(supabase, email_msg)
                
            except Exception as e:
                logger.error(f"Failed to process message {raw_msg.get('id', 'unknown')}: {e}")
                continue
        
        response = EmailReadResponse(
            total_messages=len(processed_messages),
            messages=processed_messages,
            query_used=request.query,
            retrieved_at=datetime.utcnow()
        )
        
        logger.info(f"Successfully retrieved {len(processed_messages)} emails")
        return response
        
    except Exception as e:
        logger.error(f"Email reading failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read emails: {str(e)}"
        )

@router.get("/unread_emails", response_model=EmailReadResponse)
async def get_unread_emails(
    max_results: int = Query(50, description="Maximum number of emails to retrieve"),
    parse_content: bool = Query(True, description="Whether to parse email content"),
    supabase=Depends(get_supabase_client)
):
    """
    Get unread emails from company inbox
    
    Convenience endpoint to quickly get unread emails for processing.
    """
    request = EmailReadRequest(
        query="is:unread label:inbox",
        max_results=max_results,
        parse_content=parse_content
    )
    
    return await read_company_emails(request, supabase)

@router.get("/recent_emails", response_model=EmailReadResponse)
async def get_recent_emails(
    hours: int = Query(24, description="Number of hours to look back"),
    max_results: int = Query(100, description="Maximum number of emails to retrieve"),
    parse_content: bool = Query(True, description="Whether to parse email content"),
    supabase=Depends(get_supabase_client)
):
    """
    Get recent emails from the last N hours
    
    Useful for checking recent customer communications.
    """
    # Calculate date for Gmail query
    cutoff_date = datetime.utcnow() - timedelta(hours=hours)
    date_str = cutoff_date.strftime("%Y/%m/%d")
    
    request = EmailReadRequest(
        query=f"after:{date_str}",
        max_results=max_results,
        parse_content=parse_content
    )
    
    return await read_company_emails(request, supabase)

@router.post("/parse_email/{message_id}", response_model=EmailParseResponse)
async def parse_single_email(
    message_id: str,
    supabase=Depends(get_supabase_client)
):
    """
    Parse a specific email for AI processing
    
    Analyzes email content to extract customer information,
    issue details, and suggested actions.
    """
    try:
        logger.info(f"Parsing email: {message_id}")
        
        # Get Gmail client
        gmail_client = GmailClient()
        
        # Get specific message
        raw_messages = await gmail_client.get_messages(query=f"rfc822msgid:{message_id}")
        
        if not raw_messages:
            raise HTTPException(status_code=404, detail="Email not found")
        
        raw_msg = raw_messages[0]
        
        # Convert to EmailMessage
        email_msg = EmailMessage(
            id=raw_msg["id"],
            thread_id=raw_msg["thread_id"],
            subject=raw_msg["subject"],
            sender=raw_msg["sender"],
            sender_email=extract_email_address(raw_msg["sender"]),
            date=raw_msg["date"],
            body=raw_msg["body"],
            snippet=raw_msg["snippet"],
            labels=raw_msg["labels"],
            is_unread="UNREAD" in raw_msg["labels"]
        )
        
        # Parse email content
        parsed_content = await parse_email_content(email_msg)
        
        # Create detailed parse response
        parse_response = EmailParseResponse(
            message_id=message_id,
            customer_info=parsed_content["customer_info"],
            issue_summary=parsed_content["issue_summary"],
            issue_category=parsed_content["issue_category"],
            priority_level=parsed_content["priority_level"],
            extracted_data=parsed_content["extracted_data"],
            suggested_actions=parsed_content["suggested_actions"]
        )
        
        # Log parsing activity
        await log_email_parsed(supabase, email_msg, parsed_content)
        
        logger.info(f"Email parsed successfully: {message_id}")
        return parse_response
        
    except Exception as e:
        logger.error(f"Email parsing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse email: {str(e)}"
        )

@router.post("/mark_as_read/{message_id}")
async def mark_email_as_read(
    message_id: str,
    supabase=Depends(get_supabase_client)
):
    """
    Mark an email as read in Gmail
    """
    try:
        gmail_client = GmailClient()
        await gmail_client.mark_as_read(message_id)
        
        # Log the action
        await log_email_action(supabase, message_id, "marked_as_read")
        
        return {"status": "success", "message": "Email marked as read"}
        
    except Exception as e:
        logger.error(f"Failed to mark email as read: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark email as read: {str(e)}"
        )

@router.post("/add_label/{message_id}")
async def add_label_to_email(
    message_id: str,
    label_name: str,
    supabase=Depends(get_supabase_client)
):
    """
    Add a label to an email (e.g., 'processed', 'ticket-created')
    """
    try:
        gmail_client = GmailClient()
        
        # Create label if it doesn't exist
        try:
            label_id = await gmail_client.create_label(label_name)
        except:
            # Label might already exist, try to find it
            # This is a simplified approach - in production you'd want to list labels first
            label_id = label_name
        
        # Add label to message
        await gmail_client.add_label_to_message(message_id, label_id)
        
        # Log the action
        await log_email_action(supabase, message_id, f"label_added:{label_name}")
        
        return {"status": "success", "message": f"Label '{label_name}' added to email"}
        
    except Exception as e:
        logger.error(f"Failed to add label to email: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add label to email: {str(e)}"
        )

# Helper Functions

def extract_email_address(sender_string: str) -> str:
    """Extract email address from sender string"""
    try:
        # Handle formats like "John Doe <john@example.com>" or just "john@example.com"
        email_match = re.search(r'<([^>]+)>', sender_string)
        if email_match:
            return email_match.group(1)
        
        # If no angle brackets, assume the whole string is the email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', sender_string)
        if email_match:
            return email_match.group(0)
        
        return sender_string  # Fallback
        
    except Exception as e:
        logger.error(f"Failed to extract email address from '{sender_string}': {e}")
        return sender_string

async def parse_email_content(email_msg: EmailMessage) -> Dict[str, Any]:
    """
    Parse email content for AI processing
    
    This function analyzes the email content to extract:
    - Customer information
    - Issue summary and category
    - Priority level
    - Relevant data points
    - Suggested actions
    """
    try:
        # Extract customer info
        customer_info = {
            "name": extract_customer_name(email_msg.sender),
            "email": email_msg.sender_email,
            "company": extract_company_from_email(email_msg.sender_email),
            "previous_interactions": 0  # Would be looked up from database
        }
        
        # Analyze email content
        body_lower = email_msg.body.lower()
        subject_lower = email_msg.subject.lower()
        
        # Determine issue category
        issue_category = categorize_issue(email_msg.subject, email_msg.body)
        
        # Determine priority level
        priority_level = determine_priority(email_msg.subject, email_msg.body)
        
        # Extract issue summary
        issue_summary = extract_issue_summary(email_msg.body)
        
        # Extract relevant data
        extracted_data = {
            "phone_numbers": extract_phone_numbers(email_msg.body),
            "order_numbers": extract_order_numbers(email_msg.body),
            "product_names": extract_product_mentions(email_msg.body),
            "error_messages": extract_error_messages(email_msg.body),
            "urls": extract_urls(email_msg.body),
            "dates": extract_dates(email_msg.body)
        }
        
        # Generate suggested actions
        suggested_actions = generate_suggested_actions(issue_category, priority_level, extracted_data)
        
        return {
            "customer_info": customer_info,
            "issue_summary": issue_summary,
            "issue_category": issue_category,
            "priority_level": priority_level,
            "extracted_data": extracted_data,
            "suggested_actions": suggested_actions,
            "parsed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to parse email content: {e}")
        return {
            "customer_info": {"name": "Unknown", "email": email_msg.sender_email},
            "issue_summary": email_msg.snippet,
            "issue_category": "general",
            "priority_level": "medium",
            "extracted_data": {},
            "suggested_actions": ["manual_review"],
            "parsed_at": datetime.utcnow().isoformat(),
            "parse_error": str(e)
        }

def extract_customer_name(sender: str) -> str:
    """Extract customer name from sender field"""
    try:
        # Handle "John Doe <john@example.com>" format
        name_match = re.match(r'^([^<]+)<', sender)
        if name_match:
            return name_match.group(1).strip().strip('"')
        
        # If no name found, use email prefix
        email = extract_email_address(sender)
        return email.split('@')[0].replace('.', ' ').title()
        
    except Exception:
        return "Unknown Customer"

def extract_company_from_email(email: str) -> str:
    """Extract company name from email domain"""
    try:
        domain = email.split('@')[1]
        company = domain.split('.')[0]
        return company.title()
    except Exception:
        return "Unknown Company"

def categorize_issue(subject: str, body: str) -> str:
    """Categorize the issue based on content"""
    content = (subject + " " + body).lower()
    
    # Define category keywords
    categories = {
        "billing": ["bill", "charge", "payment", "invoice", "refund", "subscription"],
        "technical": ["error", "bug", "crash", "not working", "broken", "issue", "problem"],
        "account": ["login", "password", "access", "account", "profile", "settings"],
        "product": ["feature", "how to", "tutorial", "guide", "documentation"],
        "shipping": ["delivery", "shipping", "order", "tracking", "package"],
        "cancellation": ["cancel", "unsubscribe", "delete", "remove", "stop"]
    }
    
    for category, keywords in categories.items():
        if any(keyword in content for keyword in keywords):
            return category
    
    return "general"

def determine_priority(subject: str, body: str) -> str:
    """Determine priority level based on content"""
    content = (subject + " " + body).lower()
    
    # High priority indicators
    high_priority = ["urgent", "emergency", "critical", "asap", "immediately", "down", "outage"]
    if any(word in content for word in high_priority):
        return "high"
    
    # Low priority indicators
    low_priority = ["question", "how to", "when you have time", "not urgent"]
    if any(word in content for word in low_priority):
        return "low"
    
    return "medium"

def extract_issue_summary(body: str) -> str:
    """Extract a concise summary of the issue"""
    try:
        # Take first few sentences or first paragraph
        sentences = body.split('.')[:3]
        summary = '. '.join(sentences).strip()
        
        # Limit length
        if len(summary) > 200:
            summary = summary[:200] + "..."
        
        return summary if summary else "No clear issue description found"
        
    except Exception:
        return "Unable to extract issue summary"

def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text"""
    phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
    matches = re.findall(phone_pattern, text)
    return [f"({match[0]}) {match[1]}-{match[2]}" for match in matches]

def extract_order_numbers(text: str) -> List[str]:
    """Extract order numbers from text"""
    order_patterns = [
        r'\border\s*#?\s*([A-Z0-9]{6,})\b',
        r'\bord[er]*\s*[#:]?\s*([A-Z0-9]{6,})\b',
        r'\b#([A-Z0-9]{6,})\b'
    ]
    
    orders = []
    for pattern in order_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        orders.extend(matches)
    
    return list(set(orders))  # Remove duplicates

def extract_product_mentions(text: str) -> List[str]:
    """Extract product mentions from text"""
    # This would be customized based on your products
    # For now, look for capitalized words that might be product names
    product_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    matches = re.findall(product_pattern, text)
    
    # Filter out common words that aren't products
    common_words = {"The", "This", "That", "Please", "Thank", "Hello", "Dear", "Best", "Regards"}
    products = [match for match in matches if match not in common_words and len(match) > 2]
    
    return list(set(products))[:5]  # Limit to 5 most likely products

def extract_error_messages(text: str) -> List[str]:
    """Extract error messages from text"""
    error_patterns = [
        r'error[:\s]+([^\n.!?]+)',
        r'exception[:\s]+([^\n.!?]+)',
        r'failed[:\s]+([^\n.!?]+)'
    ]
    
    errors = []
    for pattern in error_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        errors.extend(matches)
    
    return [error.strip() for error in errors if len(error.strip()) > 10]

def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def extract_dates(text: str) -> List[str]:
    """Extract dates from text"""
    date_patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b'
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    
    return dates

def generate_suggested_actions(category: str, priority: str, extracted_data: Dict) -> List[str]:
    """Generate suggested actions based on parsed content"""
    actions = []
    
    # Priority-based actions
    if priority == "high":
        actions.append("escalate_to_human")
        actions.append("send_immediate_acknowledgment")
    
    # Category-based actions
    category_actions = {
        "billing": ["check_billing_system", "review_payment_history"],
        "technical": ["search_knowledge_base", "check_system_status"],
        "account": ["verify_account_details", "check_login_logs"],
        "product": ["search_documentation", "provide_tutorial_links"],
        "shipping": ["check_order_status", "provide_tracking_info"],
        "cancellation": ["process_cancellation_request", "send_retention_offer"]
    }
    
    if category in category_actions:
        actions.extend(category_actions[category])
    
    # Data-based actions
    if extracted_data.get("order_numbers"):
        actions.append("lookup_order_details")
    
    if extracted_data.get("error_messages"):
        actions.append("search_error_database")
    
    # Default actions
    if not actions:
        actions = ["search_knowledge_base", "create_support_ticket"]
    
    return actions

# Logging Functions

async def log_email_retrieved(supabase, email_msg: EmailMessage):
    """Log email retrieval to database"""
    try:
        log_data = {
            "id": str(uuid.uuid4()),
            "interaction_type": "email_retrieved",
            "message_id": email_msg.id,
            "sender_email": email_msg.sender_email,
            "subject": email_msg.subject,
            "is_unread": email_msg.is_unread,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("support_interactions").insert(log_data).execute()
        
    except Exception as e:
        logger.error(f"Failed to log email retrieval: {e}")

async def log_email_parsed(supabase, email_msg: EmailMessage, parsed_content: Dict):
    """Log email parsing to database"""
    try:
        log_data = {
            "id": str(uuid.uuid4()),
            "interaction_type": "email_parsed",
            "message_id": email_msg.id,
            "sender_email": email_msg.sender_email,
            "issue_category": parsed_content["issue_category"],
            "priority_level": parsed_content["priority_level"],
            "parsed_content": json.dumps(parsed_content),
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("support_interactions").insert(log_data).execute()
        
    except Exception as e:
        logger.error(f"Failed to log email parsing: {e}")

async def log_email_action(supabase, message_id: str, action: str):
    """Log email action to database"""
    try:
        log_data = {
            "id": str(uuid.uuid4()),
            "interaction_type": "email_action",
            "message_id": message_id,
            "action_taken": action,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("support_interactions").insert(log_data).execute()
        
    except Exception as e:
        logger.error(f"Failed to log email action: {e}")