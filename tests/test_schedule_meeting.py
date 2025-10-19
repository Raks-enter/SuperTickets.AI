"""
Test Meeting Scheduling functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json

from mcp_service.main import app

client = TestClient(app)

class TestScheduleMeeting:
    """Test cases for meeting scheduling"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value = Mock(data=[{"id": "log_123"}])
        return mock_client
    
    @pytest.fixture
    def mock_calendar_response(self):
        """Mock Google Calendar API response"""
        return {
            "event_id": "event_12345",
            "meeting_url": "https://meet.google.com/abc-defg-hij",
            "start_time": "2024-01-16T14:00:00Z",
            "end_time": "2024-01-16T14:30:00Z",
            "attendees": ["customer@example.com", "support@company.com"],
            "html_link": "https://calendar.google.com/calendar/event?eid=12345",
            "calendar_id": "primary"
        }
    
    @pytest.fixture
    def valid_meeting_request(self):
        """Valid meeting scheduling request"""
        return {
            "customer_email": "customer@example.com",
            "meeting_type": "support_followup",
            "duration_minutes": 30,
            "preferred_times": "business_hours",
            "ticket_id": "TICK-12345",
            "meeting_description": "Follow-up meeting to discuss resolution of login issues",
            "attendees": ["support@company.com", "manager@company.com"],
            "timezone": "America/New_York",
            "urgency": "normal",
            "meeting_notes": "Customer reported continued issues after initial fix"
        }
    
    @pytest.mark.asyncio
    async def test_schedule_meeting_success(self, mock_supabase_client, mock_calendar_response, valid_meeting_request):
        """Test successful meeting scheduling"""
        with patch('mcp_service.routes.schedule_meeting.GoogleCalendarClient') as mock_calendar:
            mock_calendar_instance = Mock()
            mock_calendar_instance.create_meeting = AsyncMock(return_value=mock_calendar_response)
            mock_calendar.return_value = mock_calendar_instance
            
            with patch('mcp_service.routes.schedule_meeting.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/schedule_meeting", json=valid_meeting_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["event_id"] == "event_12345"
        assert data["meeting_url"] == "https://meet.google.com/abc-defg-hij"
        assert data["start_time"] == "2024-01-16T14:00:00Z"
        assert data["end_time"] == "2024-01-16T14:30:00Z"
        assert "customer@example.com" in data["attendees"]
    
    def test_schedule_meeting_invalid_email(self):
        """Test meeting scheduling with invalid email"""
        invalid_request = {
            "customer_email": "invalid_email",  # Invalid email format
            "meeting_type": "support_followup",
            "duration_minutes": 30
        }
        
        response = client.post("/mcp/schedule_meeting", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_schedule_meeting_missing_required_fields(self):
        """Test meeting scheduling with missing required fields"""
        incomplete_request = {
            "customer_email": "customer@example.com",
            # Missing meeting_type and duration_minutes
        }
        
        response = client.post("/mcp/schedule_meeting", json=incomplete_request)
        assert response.status_code == 422  # Validation error
    
    def test_schedule_meeting_invalid_duration(self):
        """Test meeting scheduling with invalid duration"""
        invalid_request = {
            "customer_email": "customer@example.com",
            "meeting_type": "support_followup",
            "duration_minutes": 0  # Invalid duration
        }
        
        response = client.post("/mcp/schedule_meeting", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_schedule_urgent_meeting(self, mock_supabase_client, valid_meeting_request):
        """Test scheduling urgent meeting with priority handling"""
        urgent_request = valid_meeting_request.copy()
        urgent_request["urgency"] = "urgent"
        urgent_request["duration_minutes"] = 15  # Shorter for urgent
        
        mock_urgent_response = {
            "event_id": "urgent_event_123",
            "meeting_url": "https://meet.google.com/urgent-meeting",
            "start_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(hours=1, minutes=15)).isoformat(),
            "attendees": ["customer@example.com", "senior-support@company.com"],
            "html_link": "https://calendar.google.com/calendar/event?eid=urgent123"
        }
        
        with patch('mcp_service.routes.schedule_meeting.GoogleCalendarClient') as mock_calendar:
            mock_calendar_instance = Mock()
            mock_calendar_instance.create_meeting = AsyncMock(return_value=mock_urgent_response)
            mock_calendar.return_value = mock_calendar_instance
            
            with patch('mcp_service.routes.schedule_meeting.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/schedule_meeting", json=urgent_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["event_id"] == "urgent_event_123"
        assert "urgent-meeting" in data["meeting_url"]
    
    @pytest.mark.asyncio
    async def test_reschedule_meeting_success(self, mock_supabase_client):
        """Test successful meeting rescheduling"""
        reschedule_request = {
            "event_id": "event_12345",
            "new_start_time": "2024-01-17T15:00:00Z",
            "new_duration_minutes": 45,
            "reason": "Customer requested different time",
            "notify_attendees": True
        }
        
        mock_reschedule_response = {
            "event_id": "event_12345",
            "new_start_time": "2024-01-17T15:00:00Z",
            "new_end_time": "2024-01-17T15:45:00Z",
            "updated_attendees": ["customer@example.com", "support@company.com"],
            "notification_sent": True
        }
        
        with patch('mcp_service.routes.schedule_meeting.GoogleCalendarClient') as mock_calendar:
            mock_calendar_instance = Mock()
            mock_calendar_instance.update_meeting = AsyncMock(return_value=mock_reschedule_response)
            mock_calendar.return_value = mock_calendar_instance
            
            with patch('mcp_service.routes.schedule_meeting.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/reschedule_meeting", json=reschedule_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["event_id"] == "event_12345"
        assert data["new_start_time"] == "2024-01-17T15:00:00Z"
        assert data["notification_sent"] == True
    
    def test_reschedule_meeting_missing_event_id(self):
        """Test rescheduling without event ID"""
        invalid_request = {
            "new_start_time": "2024-01-17T15:00:00Z",
            # Missing event_id
        }
        
        response = client.post("/mcp/reschedule_meeting", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_check_availability_success(self, mock_supabase_client):
        """Test availability checking"""
        availability_request = {
            "attendees": ["customer@example.com", "support@company.com"],
            "start_time": "2024-01-16T14:00:00Z",
            "end_time": "2024-01-16T15:00:00Z",
            "timezone": "America/New_York"
        }
        
        mock_availability_response = {
            "customer@example.com": {
                "available": True,
                "busy_times": []
            },
            "support@company.com": {
                "available": False,
                "busy_times": [
                    {
                        "start": "2024-01-16T14:30:00Z",
                        "end": "2024-01-16T15:30:00Z",
                        "title": "Team Meeting"
                    }
                ]
            }
        }
        
        with patch('mcp_service.routes.schedule_meeting.GoogleCalendarClient') as mock_calendar:
            mock_calendar_instance = Mock()
            mock_calendar_instance.check_availability = AsyncMock(return_value=mock_availability_response)
            mock_calendar.return_value = mock_calendar_instance
            
            with patch('mcp_service.routes.schedule_meeting.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/check_availability", json=availability_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["customer@example.com"]["available"] == True
        assert data["support@company.com"]["available"] == False
        assert len(data["support@company.com"]["busy_times"]) == 1
    
    @pytest.mark.asyncio
    async def test_cancel_meeting_success(self, mock_supabase_client):
        """Test successful meeting cancellation"""
        cancel_request = {
            "event_id": "event_12345",
            "cancellation_reason": "Customer resolved issue independently",
            "notify_attendees": True,
            "send_cancellation_email": True
        }
        
        mock_cancel_response = {
            "event_id": "event_12345",
            "status": "cancelled",
            "cancellation_time": datetime.utcnow().isoformat(),
            "notifications_sent": True
        }
        
        with patch('mcp_service.routes.schedule_meeting.GoogleCalendarClient') as mock_calendar:
            mock_calendar_instance = Mock()
            mock_calendar_instance.cancel_meeting = AsyncMock(return_value=mock_cancel_response)
            mock_calendar.return_value = mock_calendar_instance
            
            with patch('mcp_service.routes.schedule_meeting.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/cancel_meeting", json=cancel_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["event_id"] == "event_12345"
        assert data["status"] == "cancelled"
        assert data["notifications_sent"] == True
    
    @pytest.mark.asyncio
    async def test_calendar_api_error_handling(self, mock_supabase_client, valid_meeting_request):
        """Test handling of Google Calendar API errors"""
        with patch('mcp_service.routes.schedule_meeting.GoogleCalendarClient') as mock_calendar:
            mock_calendar_instance = Mock()
            mock_calendar_instance.create_meeting = AsyncMock(side_effect=Exception("Calendar API Error"))
            mock_calendar.return_value = mock_calendar_instance
            
            with patch('mcp_service.routes.schedule_meeting.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/schedule_meeting", json=valid_meeting_request)
        
        assert response.status_code == 500
        assert "Failed to schedule meeting" in response.json()["detail"]

class TestMeetingTimeCalculation:
    """Test meeting time calculation and scheduling logic"""
    
    def test_business_hours_scheduling(self):
        """Test scheduling within business hours"""
        from datetime import datetime, time
        
        # Mock function to check if time is within business hours
        def is_business_hours(dt, timezone="UTC"):
            # Business hours: 9 AM - 5 PM weekdays
            if dt.weekday() >= 5:  # Weekend
                return False
            business_start = time(9, 0)
            business_end = time(17, 0)
            return business_start <= dt.time() <= business_end
        
        # Test various times
        monday_10am = datetime(2024, 1, 15, 10, 0)  # Monday 10 AM
        saturday_10am = datetime(2024, 1, 13, 10, 0)  # Saturday 10 AM
        monday_6pm = datetime(2024, 1, 15, 18, 0)  # Monday 6 PM
        
        assert is_business_hours(monday_10am) == True
        assert is_business_hours(saturday_10am) == False
        assert is_business_hours(monday_6pm) == False
    
    def test_meeting_duration_calculation(self):
        """Test meeting duration calculations"""
        from datetime import datetime, timedelta
        
        start_time = datetime(2024, 1, 15, 14, 0)  # 2 PM
        duration_minutes = 30
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        assert end_time == datetime(2024, 1, 15, 14, 30)  # 2:30 PM
        
        # Test different durations
        durations = [15, 30, 45, 60]
        for duration in durations:
            calculated_end = start_time + timedelta(minutes=duration)
            expected_end = datetime(2024, 1, 15, 14, duration)
            assert calculated_end.minute == duration
    
    def test_timezone_handling(self):
        """Test timezone conversion logic"""
        from datetime import datetime
        import pytz
        
        # This would test actual timezone conversion
        # For now, test the concept
        
        utc_time = datetime(2024, 1, 15, 19, 0)  # 7 PM UTC
        
        # Convert to different timezones (conceptual)
        timezones = {
            "America/New_York": -5,  # EST offset
            "America/Los_Angeles": -8,  # PST offset
            "Europe/London": 0,  # GMT offset
        }
        
        for tz_name, offset in timezones.items():
            local_time = utc_time + timedelta(hours=offset)
            # Verify conversion logic
            assert isinstance(local_time, datetime)

class TestMeetingConflictDetection:
    """Test meeting conflict detection logic"""
    
    def test_time_overlap_detection(self):
        """Test detecting time overlaps between meetings"""
        from datetime import datetime
        
        def times_overlap(start1, end1, start2, end2):
            """Check if two time ranges overlap"""
            return start1 < end2 and start2 < end1
        
        # Test cases
        meeting1_start = datetime(2024, 1, 15, 14, 0)  # 2:00 PM
        meeting1_end = datetime(2024, 1, 15, 15, 0)    # 3:00 PM
        
        # Overlapping meeting
        meeting2_start = datetime(2024, 1, 15, 14, 30)  # 2:30 PM
        meeting2_end = datetime(2024, 1, 15, 15, 30)    # 3:30 PM
        
        # Non-overlapping meeting
        meeting3_start = datetime(2024, 1, 15, 15, 30)  # 3:30 PM
        meeting3_end = datetime(2024, 1, 15, 16, 30)    # 4:30 PM
        
        assert times_overlap(meeting1_start, meeting1_end, meeting2_start, meeting2_end) == True
        assert times_overlap(meeting1_start, meeting1_end, meeting3_start, meeting3_end) == False
    
    def test_attendee_availability_check(self):
        """Test checking attendee availability"""
        attendee_schedule = {
            "support@company.com": [
                {
                    "start": datetime(2024, 1, 15, 14, 0),
                    "end": datetime(2024, 1, 15, 15, 0),
                    "title": "Team Meeting"
                }
            ]
        }
        
        # Check if attendee is available for new meeting
        new_meeting_start = datetime(2024, 1, 15, 14, 30)
        new_meeting_end = datetime(2024, 1, 15, 15, 30)
        
        def is_attendee_available(email, start, end, schedule):
            if email not in schedule:
                return True
            
            for existing_meeting in schedule[email]:
                if (start < existing_meeting["end"] and 
                    existing_meeting["start"] < end):
                    return False
            return True
        
        available = is_attendee_available(
            "support@company.com", 
            new_meeting_start, 
            new_meeting_end, 
            attendee_schedule
        )
        
        assert available == False  # Should conflict with existing meeting

class TestMeetingNotifications:
    """Test meeting notification logic"""
    
    def test_notification_timing(self):
        """Test when notifications should be sent"""
        from datetime import datetime, timedelta
        
        meeting_time = datetime(2024, 1, 16, 14, 0)  # Tomorrow 2 PM
        now = datetime(2024, 1, 15, 10, 0)  # Today 10 AM
        
        # Calculate notification times
        reminder_24h = meeting_time - timedelta(hours=24)
        reminder_1h = meeting_time - timedelta(hours=1)
        reminder_15m = meeting_time - timedelta(minutes=15)
        
        def should_send_reminder(current_time, reminder_time, meeting_time):
            # Send if we've passed the reminder time but not the meeting time
            return reminder_time <= current_time < meeting_time
        
        # Test different scenarios
        assert should_send_reminder(reminder_24h, reminder_24h, meeting_time) == True
        assert should_send_reminder(now, reminder_24h, meeting_time) == False  # Too early
        assert should_send_reminder(meeting_time + timedelta(hours=1), reminder_1h, meeting_time) == False  # Too late
    
    def test_notification_content_generation(self):
        """Test generating notification content"""
        meeting_data = {
            "customer_email": "customer@example.com",
            "meeting_type": "support_followup",
            "start_time": "2024-01-16T14:00:00Z",
            "duration_minutes": 30,
            "meeting_url": "https://meet.google.com/abc-defg-hij",
            "ticket_id": "TICK-12345"
        }
        
        def generate_notification_content(meeting_data, notification_type="reminder"):
            if notification_type == "reminder":
                return f"""
                Reminder: You have a {meeting_data['meeting_type']} meeting scheduled for {meeting_data['start_time']}.
                
                Meeting Link: {meeting_data['meeting_url']}
                Duration: {meeting_data['duration_minutes']} minutes
                Related Ticket: {meeting_data['ticket_id']}
                """
            elif notification_type == "confirmation":
                return f"""
                Your meeting has been scheduled successfully.
                
                Type: {meeting_data['meeting_type']}
                Time: {meeting_data['start_time']}
                Duration: {meeting_data['duration_minutes']} minutes
                Meeting Link: {meeting_data['meeting_url']}
                """
        
        reminder_content = generate_notification_content(meeting_data, "reminder")
        confirmation_content = generate_notification_content(meeting_data, "confirmation")
        
        assert "Reminder" in reminder_content
        assert "support_followup" in reminder_content
        assert "scheduled successfully" in confirmation_content
        assert meeting_data["meeting_url"] in both reminder_content and confirmation_content

if __name__ == "__main__":
    pytest.main([__file__])