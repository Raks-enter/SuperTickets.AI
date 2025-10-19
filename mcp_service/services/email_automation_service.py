"""
Email Automation Service
Handles automatic email monitoring, processing, and response generation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

from ..utils.gmail_client import GmailClient
from ..utils.supabase_client import get_supabase_client
from .bedrock_ai_processor import BedrockAIProcessor

logger = logging.getLogger(__name__)

class EmailAutomationService:
    """Automated email processing service"""
    
    def __init__(self):
        self.gmail_client = None
        self.ai_processor = BedrockAIProcessor()
        self.supabase = None
        self.is_running = False
        self.processed_emails = set()  # Track processed email IDs
        self.check_interval = 30  # Check every 30 seconds
        
    async def initialize(self):
        """Initialize the service"""
        try:
            self.gmail_client = GmailClient()
            self.supabase = get_supabase_client()
            logger.info("Email automation service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize email automation service: {e}")
            return False

    async def start_monitoring(self):
        """Start automatic email monitoring"""
        if self.is_running:
            logger.warning("Email monitoring is already running")
            return
            
        if not await self.initialize():
            raise Exception("Failed to initialize email automation service")
            
        self.is_running = True
        logger.info("Starting email automation monitoring...")
        
        try:
            while self.is_running:
                await self._process_new_emails()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Email monitoring error: {e}")
            self.is_running = False
            raise

    async def stop_monitoring(self):
        """Stop email monitoring"""
        self.is_running = False
        logger.info("Email automation monitoring stopped")

    async def _process_new_emails(self):
        """Process new emails from Gmail"""
        try:
            # Get unread emails from the last hour
            query = "is:unread newer_than:1h"
            emails = await self._fetch_emails(query)
            
            logger.info(f"Found {len(emails)} unread emails to process")
            
            for email in emails:
                email_id = email.get('id')
                
                # Skip if already processed
                if email_id in self.processed_emails:
                    continue
                    
                try:
                    await self._process_single_email(email)
                    self.processed_emails.add(email_id)
                    
                    # Mark as read after processing
                    await self._mark_email_as_read(email_id)
                    
                except Exception as e:
                    logger.error(f"Failed to process email {email_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing new emails: {e}")

    async def _fetch_emails(self, query: str) -> List[Dict]:
        """Fetch emails from Gmail"""
        try:
            # Use Gmail API to search for emails
            results = self.gmail_client.service.users().messages().list(
                userId='me', q=query, maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                # Get full message details
                msg = self.gmail_client.service.users().messages().get(
                    userId='me', id=message['id'], format='full'
                ).execute()
                
                # Parse email content
                email_data = self._parse_email_message(msg)
                if email_data:
                    emails.append(email_data)
                    
            return emails
            
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            return []

    def _parse_email_message(self, message: Dict) -> Optional[Dict]:
        """Parse Gmail message into structured data"""
        try:
            headers = message['payload'].get('headers', [])
            
            # Extract headers
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            message_id = next((h['value'] for h in headers if h['name'] == 'Message-ID'), '')
            
            # Extract body
            body = self._extract_email_body(message['payload'])
            
            return {
                'id': message['id'],
                'thread_id': message['threadId'],
                'subject': subject,
                'sender': sender,
                'date': date,
                'message_id': message_id,
                'body': body,
                'snippet': message.get('snippet', ''),
                'labels': message.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to parse email message: {e}")
            return None

    def _extract_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        try:
            body = ""
            
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            import base64
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
            else:
                if payload['mimeType'] == 'text/plain':
                    data = payload['body'].get('data', '')
                    if data:
                        import base64
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        
            return body.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract email body: {e}")
            return ""

    async def _process_single_email(self, email: Dict):
        """Process a single email with AI analysis and response"""
        try:
            logger.info(f"Processing email: {email['subject']} from {email['sender']}")
            
            # 1. AI Analysis
            analysis = await self.ai_processor.analyze_email(
                email_content=email['body'],
                subject=email['subject'],
                sender=email['sender']
            )
            
            # 2. Search Knowledge Base with AI
            kb_results = await self.ai_processor.search_knowledge_base_ai(
                f"{email['subject']} {email['body']}"
            )
            
            # 3. Create Ticket if needed
            ticket_id = None
            if analysis.ticket_needed:
                ticket_id = await self._create_support_ticket(email, analysis)
            
            # 4. Generate AI Response
            if not analysis.requires_human or kb_results:
                response = await self.ai_processor.generate_response(
                    analysis, email['body'], email['subject'], kb_results
                )
                
                # 5. Send Response
                await self._send_automated_response(email, response, analysis, ticket_id)
            
            # 6. Log Processing
            await self._log_email_processing(email, analysis, ticket_id)
            
            logger.info(f"Email processed successfully: {analysis.category}/{analysis.priority}")
            
        except Exception as e:
            logger.error(f"Failed to process email: {e}")
            raise

    async def _search_knowledge_base(self, content: str, subject: str) -> List[Dict]:
        """Search knowledge base for relevant solutions"""
        try:
            # Combine subject and content for search
            query = f"{subject} {content}"[:200]  # Limit query length
            
            # Simple mock KB search for now - replace with actual implementation
            # This would normally connect to your knowledge base
            mock_results = [
                {
                    "title": "Common Login Issues",
                    "content": "Try clearing your browser cache and cookies, then attempt to log in again.",
                    "similarity": 0.8
                },
                {
                    "title": "Password Reset Guide", 
                    "content": "Use the 'Forgot Password' link on the login page to reset your password.",
                    "similarity": 0.7
                }
            ]
            
            # Filter results based on query relevance
            if any(word in query.lower() for word in ['login', 'password', 'account']):
                return mock_results
            else:
                return []
            
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            return []

    async def _create_support_ticket(self, email: Dict, analysis) -> Optional[str]:
        """Create support ticket for the email"""
        try:
            ticket_data = {
                "id": str(uuid.uuid4()),
                "title": email['subject'],
                "description": email['body'][:1000],  # Limit description length
                "priority": analysis.priority,
                "category": analysis.category,
                "status": "open",
                "customer_email": self._extract_email_address(email['sender']),
                "source": "email_automation",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "email_id": email['id'],
                    "thread_id": email['thread_id'],
                    "ai_analysis": {
                        "category": analysis.category,
                        "priority": analysis.priority,
                        "sentiment": analysis.sentiment,
                        "confidence": analysis.confidence,
                        "keywords": analysis.keywords
                    }
                }
            }
            
            # Insert into Supabase
            result = self.supabase.table("support_tickets").insert(ticket_data).execute()
            
            logger.info(f"Support ticket created: {ticket_data['id']}")
            return ticket_data['id']
            
        except Exception as e:
            logger.error(f"Failed to create support ticket: {e}")
            return None

    async def _send_automated_response(self, email: Dict, response: str, 
                                     analysis, ticket_id: Optional[str]):
        """Send automated response email"""
        try:
            # Extract sender email
            sender_email = self._extract_email_address(email['sender'])
            
            # Prepare response email
            response_subject = f"Re: {email['subject']}"
            
            # Add ticket reference if created
            if ticket_id:
                response += f"\n\nTicket Reference: #{ticket_id[:8]}"
            
            # Send email using Gmail client directly
            email_data = {
                "to": sender_email,
                "subject": response_subject,
                "body": response,
                "thread_id": email['thread_id']
            }
            
            # Send the response
            send_result = await self.gmail_client.send_email(email_data)
            
            # Log the sent email
            await self._log_email_sent(email_data, send_result)
            
            logger.info(f"Automated response sent to {sender_email}")
            
        except Exception as e:
            logger.error(f"Failed to send automated response: {e}")

    async def _mark_email_as_read(self, email_id: str):
        """Mark email as read in Gmail"""
        try:
            self.gmail_client.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")

    def _extract_email_address(self, sender: str) -> str:
        """Extract email address from sender string"""
        import re
        match = re.search(r'<(.+?)>', sender)
        if match:
            return match.group(1)
        elif '@' in sender:
            return sender.strip()
        else:
            return sender

    async def _log_email_processing(self, email: Dict, analysis, ticket_id: Optional[str]):
        """Log email processing for analytics"""
        try:
            log_data = {
                "id": str(uuid.uuid4()),
                "interaction_type": "email_processed",
                "email_id": email['id'],
                "sender_email": self._extract_email_address(email['sender']),
                "subject": email['subject'],
                "category": analysis.category,
                "priority": analysis.priority,
                "sentiment": analysis.sentiment,
                "confidence": analysis.confidence,
                "ticket_created": ticket_id is not None,
                "ticket_id": ticket_id,
                "requires_human": analysis.requires_human,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "keywords": analysis.keywords,
                    "thread_id": email['thread_id']
                }
            }
            
            self.supabase.table("support_interactions").insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to log email processing: {e}")

    async def _log_email_sent(self, email_data: Dict, send_result: Dict):
        """Log sent email for tracking"""
        try:
            log_data = {
                "id": str(uuid.uuid4()),
                "interaction_type": "email_sent",
                "recipient_email": email_data["to"],
                "subject": email_data["subject"],
                "message_id": send_result.get("message_id"),
                "thread_id": send_result.get("thread_id"),
                "source": "automation",
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("support_interactions").insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to log sent email: {e}")

    async def get_status(self) -> Dict:
        """Get automation service status"""
        return {
            "is_running": self.is_running,
            "processed_count": len(self.processed_emails),
            "check_interval": self.check_interval,
            "last_check": datetime.utcnow().isoformat() if self.is_running else None
        }

# Global service instance
email_automation_service = EmailAutomationService()