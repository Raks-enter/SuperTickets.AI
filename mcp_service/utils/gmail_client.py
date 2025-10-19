"""
Gmail API Client
Handles email sending and receiving via Gmail API
"""

import os
import logging
import base64
import email
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GmailClient:
    """Gmail API client for email operations"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send', 
              'https://www.googleapis.com/auth/gmail.readonly',
              'https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self):
        self.credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials/gmail_credentials.json")
        self.token_path = os.getenv("GMAIL_TOKEN_PATH", "./credentials/gmail_token.json")
        
        self.service = self._authenticate()
        logger.info("Gmail client initialized")
    
    def _authenticate(self):
        """Authenticate with Gmail API"""
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(f"Gmail credentials file not found: {self.credentials_path}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            
            return build('gmail', 'v1', credentials=creds)
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            raise
    
    async def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via Gmail API"""
        try:
            # Create message
            message = self._create_message(
                to=email_data["to"],
                subject=email_data["subject"],
                body=email_data["body"],
                cc=email_data.get("cc", []),
                bcc=email_data.get("bcc", []),
                reply_to=email_data.get("reply_to"),
                attachments=email_data.get("attachments", []),
                thread_id=email_data.get("thread_id")
            )
            
            # Send message
            if email_data.get("thread_id"):
                # Reply to existing thread
                sent_message = self.service.users().messages().send(
                    userId='me',
                    body=message,
                    threadId=email_data["thread_id"]
                ).execute()
            else:
                # New message
                sent_message = self.service.users().messages().send(
                    userId='me',
                    body=message
                ).execute()
            
            result = {
                "message_id": sent_message["id"],
                "thread_id": sent_message["threadId"],
                "status": "sent"
            }
            
            logger.info(f"Email sent successfully: {result['message_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    def _create_message(
        self,
        to: str,
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        reply_to: str = None,
        attachments: List[str] = None,
        thread_id: str = None
    ) -> Dict[str, Any]:
        """Create email message"""
        try:
            # Create multipart message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            if reply_to:
                message['reply-to'] = reply_to
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(message, file_path)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            gmail_message = {'raw': raw_message}
            
            if thread_id:
                gmail_message['threadId'] = thread_id
            
            return gmail_message
            
        except Exception as e:
            logger.error(f"Failed to create email message: {e}")
            raise
    
    def _add_attachment(self, message: MIMEMultipart, file_path: str):
        """Add file attachment to message"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            message.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {file_path}: {e}")
    
    async def get_messages(
        self,
        query: str = "",
        max_results: int = 10,
        label_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from Gmail"""
        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                labelIds=label_ids
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get full message details
            full_messages = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                parsed_msg = self._parse_message(msg)
                full_messages.append(parsed_msg)
            
            logger.info(f"Retrieved {len(full_messages)} messages")
            return full_messages
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            raise
    
    def _parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message"""
        try:
            headers = message['payload'].get('headers', [])
            
            # Extract headers
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            return {
                "id": message['id'],
                "thread_id": message['threadId'],
                "subject": subject,
                "sender": sender,
                "date": date,
                "body": body,
                "snippet": message.get('snippet', ''),
                "labels": message.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to parse message: {e}")
            return {}
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract body text from message payload"""
        try:
            body = ""
            
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
            else:
                if payload['mimeType'] == 'text/plain':
                    data = payload['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
            
            return body
            
        except Exception as e:
            logger.error(f"Failed to extract body: {e}")
            return ""
    
    async def mark_as_read(self, message_id: str):
        """Mark message as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info(f"Message marked as read: {message_id}")
            
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")
    
    async def create_label(self, label_name: str) -> str:
        """Create Gmail label"""
        try:
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            logger.info(f"Label created: {label_name}")
            return created_label['id']
            
        except Exception as e:
            logger.error(f"Failed to create label: {e}")
            raise
    
    async def add_label_to_message(self, message_id: str, label_id: str):
        """Add label to message"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            
            logger.info(f"Label added to message: {message_id}")
            
        except Exception as e:
            logger.error(f"Failed to add label to message: {e}")