"""
Google Calendar Client
Handles meeting scheduling via Google Calendar API
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GoogleCalendarClient:
    """Google Calendar API client for meeting scheduling"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH", "./credentials/calendar_credentials.json")
        self.token_path = os.getenv("GOOGLE_CALENDAR_TOKEN_PATH", "./credentials/calendar_token.json")
        
        self.service = self._authenticate()
        logger.info("Google Calendar client initialized")
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
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
                        raise FileNotFoundError(f"Calendar credentials file not found: {self.credentials_path}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            
            return build('calendar', 'v3', credentials=creds)
            
        except Exception as e:
            logger.error(f"Calendar authentication failed: {e}")
            raise
    
    async def create_meeting(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create calendar event for meeting"""
        try:
            # Parse meeting time
            start_time = datetime.fromisoformat(meeting_data["start_time"])
            end_time = start_time + timedelta(minutes=meeting_data["duration_minutes"])
            
            # Get timezone
            timezone = meeting_data.get("timezone", "UTC")
            tz = pytz.timezone(timezone)
            
            # Create event
            event = {
                'summary': meeting_data["summary"],
                'description': meeting_data["description"],
                'start': {
                    'dateTime': start_time.replace(tzinfo=tz).isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_time.replace(tzinfo=tz).isoformat(),
                    'timeZone': timezone,
                },
                'attendees': [
                    {'email': email} for email in meeting_data["attendees"]
                ],
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"meeting-{int(datetime.now().timestamp())}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},       # 30 minutes before
                    ],
                },
                'guestsCanModify': False,
                'guestsCanInviteOthers': False,
                'guestsCanSeeOtherGuests': True
            }
            
            # Create event
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1,
                sendUpdates='all'
            ).execute()
            
            # Extract meeting URL
            meeting_url = self._extract_meeting_url(created_event)
            
            result = {
                "event_id": created_event['id'],
                "meeting_url": meeting_url,
                "start_time": created_event['start']['dateTime'],
                "end_time": created_event['end']['dateTime'],
                "attendees": [att.get('email') for att in created_event.get('attendees', [])],
                "html_link": created_event['htmlLink']
            }
            
            logger.info(f"Calendar event created: {result['event_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            raise
    
    async def update_meeting(
        self, 
        event_id: str, 
        new_start_time: datetime, 
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update existing calendar event"""
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Calculate new end time (preserve duration)
            original_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            original_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
            duration = original_end - original_start
            
            new_end_time = new_start_time + duration
            
            # Update event
            event['start']['dateTime'] = new_start_time.isoformat()
            event['end']['dateTime'] = new_end_time.isoformat()
            
            if reason:
                event['description'] = f"{event.get('description', '')}\n\nRescheduled: {reason}"
            
            # Update event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Calendar event updated: {event_id}")
            return {
                "event_id": updated_event['id'],
                "new_start_time": updated_event['start']['dateTime'],
                "new_end_time": updated_event['end']['dateTime']
            }
            
        except Exception as e:
            logger.error(f"Failed to update calendar event: {e}")
            raise
    
    async def cancel_meeting(self, event_id: str, reason: Optional[str] = None):
        """Cancel calendar event"""
        try:
            if reason:
                # Add cancellation reason to description
                event = self.service.events().get(
                    calendarId='primary',
                    eventId=event_id
                ).execute()
                
                event['description'] = f"{event.get('description', '')}\n\nCancelled: {reason}"
                event['status'] = 'cancelled'
                
                self.service.events().update(
                    calendarId='primary',
                    eventId=event_id,
                    body=event,
                    sendUpdates='all'
                ).execute()
            else:
                # Delete event
                self.service.events().delete(
                    calendarId='primary',
                    eventId=event_id,
                    sendUpdates='all'
                ).execute()
            
            logger.info(f"Calendar event cancelled: {event_id}")
            
        except Exception as e:
            logger.error(f"Failed to cancel calendar event: {e}")
            raise
    
    async def check_availability(
        self, 
        attendee_emails: List[str], 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """Check availability of attendees"""
        try:
            # Format time for API
            time_min = start_time.isoformat() + 'Z'
            time_max = end_time.isoformat() + 'Z'
            
            # Check free/busy status
            body = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": email} for email in attendee_emails]
            }
            
            freebusy_result = self.service.freebusy().query(body=body).execute()
            
            availability = {}
            for email in attendee_emails:
                busy_times = freebusy_result['calendars'].get(email, {}).get('busy', [])
                availability[email] = {
                    "available": len(busy_times) == 0,
                    "busy_times": busy_times
                }
            
            logger.info(f"Checked availability for {len(attendee_emails)} attendees")
            return availability
            
        except Exception as e:
            logger.error(f"Failed to check availability: {e}")
            raise
    
    async def find_available_slots(
        self, 
        attendee_emails: List[str], 
        duration_minutes: int,
        preferred_date: datetime,
        business_hours_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Find available meeting slots"""
        try:
            available_slots = []
            
            # Check availability for the next 7 days
            for day_offset in range(7):
                check_date = preferred_date + timedelta(days=day_offset)
                
                if business_hours_only:
                    # Check business hours (9 AM - 5 PM)
                    start_hour = 9
                    end_hour = 17
                else:
                    # Check extended hours (8 AM - 8 PM)
                    start_hour = 8
                    end_hour = 20
                
                for hour in range(start_hour, end_hour):
                    slot_start = check_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    slot_end = slot_start + timedelta(minutes=duration_minutes)
                    
                    # Skip if slot extends beyond business hours
                    if slot_end.hour >= end_hour:
                        continue
                    
                    # Check availability
                    availability = await self.check_availability(
                        attendee_emails, slot_start, slot_end
                    )
                    
                    # Check if all attendees are available
                    all_available = all(
                        att_info["available"] for att_info in availability.values()
                    )
                    
                    if all_available:
                        available_slots.append({
                            "start_time": slot_start.isoformat(),
                            "end_time": slot_end.isoformat(),
                            "duration_minutes": duration_minutes,
                            "all_attendees_available": True
                        })
                    
                    # Limit to 10 slots
                    if len(available_slots) >= 10:
                        break
                
                if len(available_slots) >= 10:
                    break
            
            logger.info(f"Found {len(available_slots)} available slots")
            return available_slots
            
        except Exception as e:
            logger.error(f"Failed to find available slots: {e}")
            return []
    
    def _extract_meeting_url(self, event: Dict[str, Any]) -> str:
        """Extract meeting URL from calendar event"""
        try:
            # Try to get Google Meet link
            conference_data = event.get('conferenceData', {})
            entry_points = conference_data.get('entryPoints', [])
            
            for entry_point in entry_points:
                if entry_point.get('entryPointType') == 'video':
                    return entry_point.get('uri', '')
            
            # Fallback to HTML link
            return event.get('htmlLink', '')
            
        except Exception as e:
            logger.error(f"Failed to extract meeting URL: {e}")
            return ""
    
    async def get_calendar_events(
        self, 
        start_date: datetime, 
        end_date: datetime,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get calendar events in date range"""
        try:
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            logger.info(f"Retrieved {len(events)} calendar events")
            return events
            
        except Exception as e:
            logger.error(f"Failed to get calendar events: {e}")
            raise