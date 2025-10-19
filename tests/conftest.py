"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock
from typing import Generator, Dict, Any

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test_key"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["OPENAI_API_KEY"] = "test_openai_key"

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    mock_client = Mock()
    
    # Mock table operations
    mock_table = Mock()
    mock_table.insert.return_value.execute.return_value = Mock(data=[{"id": "test_id"}])
    mock_table.select.return_value.eq.return_value.execute.return_value = Mock(data=[])
    mock_table.update.return_value.eq.return_value.execute.return_value = Mock(data=[{"id": "test_id"}])
    
    mock_client.table.return_value = mock_table
    mock_client.search_knowledge_base = AsyncMock(return_value=[])
    mock_client.insert_interaction = AsyncMock(return_value={"id": "test_interaction"})
    mock_client.get_interactions = AsyncMock(return_value=[])
    
    return mock_client

@pytest.fixture
def mock_bedrock_client():
    """Mock AWS Bedrock client for testing"""
    mock_client = Mock()
    mock_client.analyze_issue = AsyncMock(return_value={
        "issue_summary": "Test issue summary",
        "urgency_level": "medium",
        "suggested_category": "technical_issues",
        "key_points": ["test", "points"],
        "complexity_level": "moderate",
        "estimated_resolution_time": "30 minutes",
        "requires_escalation": False
    })
    mock_client.extract_call_info = AsyncMock(return_value={
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "issue_description": "Test issue",
        "urgency_indicators": ["urgent"],
        "resolution_attempted": "password reset",
        "customer_satisfaction": "neutral",
        "follow_up_needed": False,
        "key_points": ["login", "issue"]
    })
    mock_client.analyze_sentiment = AsyncMock(return_value={
        "sentiment_score": 0.0,
        "frustration_level": "medium",
        "urgency_level": "medium",
        "escalation_needed": False,
        "key_emotions": ["frustrated"],
        "urgency_keywords": [],
        "customer_tone_progression": "neutral to frustrated",
        "resolution_satisfaction": "neutral"
    })
    return mock_client

@pytest.fixture
def mock_superops_client():
    """Mock SuperOps client for testing"""
    mock_client = Mock()
    mock_client.create_ticket = AsyncMock(return_value={
        "ticket_id": "TICK-12345",
        "internal_id": "internal_123",
        "ticket_url": "https://superops.com/tickets/TICK-12345",
        "status": "open",
        "priority": "medium",
        "assigned_agent": "Test Agent",
        "created_at": "2024-01-15T10:30:00Z",
        "estimated_resolution_time": "24 hours"
    })
    mock_client.create_callback_task = AsyncMock(return_value={
        "callback_id": "CB-001",
        "title": "Test Callback",
        "scheduled_time": "2024-01-15T12:30:00Z",
        "assigned_agent": "Test Agent",
        "status": "scheduled"
    })
    mock_client.get_ticket = AsyncMock(return_value={
        "id": "internal_123",
        "ticketNumber": "TICK-12345",
        "title": "Test Ticket",
        "status": "open"
    })
    return mock_client

@pytest.fixture
def mock_gmail_client():
    """Mock Gmail client for testing"""
    mock_client = Mock()
    mock_client.send_email = AsyncMock(return_value={
        "message_id": "msg_123",
        "thread_id": "thread_123",
        "status": "sent"
    })
    mock_client.get_messages = AsyncMock(return_value=[
        {
            "id": "msg_123",
            "thread_id": "thread_123",
            "subject": "Test Subject",
            "sender": "test@example.com",
            "body": "Test email body",
            "date": "2024-01-15T10:30:00Z"
        }
    ])
    return mock_client

@pytest.fixture
def mock_calendar_client():
    """Mock Google Calendar client for testing"""
    mock_client = Mock()
    mock_client.create_meeting = AsyncMock(return_value={
        "event_id": "event_123",
        "meeting_url": "https://meet.google.com/test-meeting",
        "start_time": "2024-01-15T14:00:00Z",
        "end_time": "2024-01-15T14:30:00Z",
        "attendees": ["test@example.com"],
        "html_link": "https://calendar.google.com/event/123"
    })
    mock_client.update_meeting = AsyncMock(return_value={
        "event_id": "event_123",
        "new_start_time": "2024-01-15T15:00:00Z",
        "new_end_time": "2024-01-15T15:30:00Z"
    })
    mock_client.check_availability = AsyncMock(return_value={
        "test@example.com": {
            "available": True,
            "busy_times": []
        }
    })
    return mock_client

@pytest.fixture
def mock_embedding_search():
    """Mock embedding search for testing"""
    mock_search = Mock()
    mock_search.create_embedding = AsyncMock(return_value=[0.1] * 1536)
    mock_search.search = AsyncMock(return_value=[
        {
            "id": "kb_001",
            "title": "Test Knowledge Entry",
            "content": "Test content",
            "category": "test",
            "tags": ["test"],
            "similarity_score": 0.9,
            "solution_steps": ["step 1", "step 2"],
            "success_rate": 0.95,
            "avg_resolution_time": "5 minutes"
        }
    ])
    mock_search.add_knowledge_entry = AsyncMock(return_value={"id": "new_entry"})
    return mock_search

@pytest.fixture
def sample_email_data():
    """Sample email data for testing"""
    return {
        "to": "customer@example.com",
        "subject": "Re: Support Request",
        "body": "Thank you for contacting support. Here's the solution...",
        "thread_id": "thread_123",
        "attachments": [],
        "cc": [],
        "bcc": []
    }

@pytest.fixture
def sample_meeting_data():
    """Sample meeting data for testing"""
    return {
        "customer_email": "customer@example.com",
        "meeting_type": "support_followup",
        "duration_minutes": 30,
        "preferred_times": "business_hours",
        "ticket_id": "TICK-12345",
        "meeting_description": "Follow-up meeting for support ticket",
        "attendees": ["support@company.com"],
        "timezone": "UTC"
    }

@pytest.fixture
def sample_interaction_log():
    """Sample interaction log data for testing"""
    return {
        "interaction_type": "email_processed",
        "customer_email": "customer@example.com",
        "issue_description": "Login issues with password reset",
        "ai_analysis": {
            "issue_summary": "Password reset problem",
            "urgency_level": "medium",
            "category": "authentication"
        },
        "resolution_type": "knowledge_base_match",
        "ticket_id": None,
        "sentiment_analysis": {
            "score": 0.2,
            "frustration_level": "medium"
        },
        "metadata": {
            "source": "email",
            "processing_time_ms": 1500
        },
        "tags": ["login", "password", "authentication"]
    }

@pytest.fixture
def sample_knowledge_entries():
    """Sample knowledge base entries for testing"""
    return [
        {
            "id": "kb_001",
            "title": "Password Reset Instructions",
            "content": "To reset your password, follow these steps...",
            "category": "authentication",
            "tags": ["password", "reset", "login"],
            "solution_steps": [
                "Go to login page",
                "Click 'Forgot Password'",
                "Enter email address",
                "Check email for reset link"
            ],
            "success_rate": 0.95,
            "avg_resolution_time": "5 minutes"
        },
        {
            "id": "kb_002",
            "title": "Two-Factor Authentication Setup",
            "content": "To enable 2FA on your account...",
            "category": "security",
            "tags": ["2fa", "security", "authentication"],
            "solution_steps": [
                "Access account settings",
                "Navigate to security section",
                "Enable 2FA",
                "Scan QR code with authenticator app"
            ],
            "success_rate": 0.88,
            "avg_resolution_time": "10 minutes"
        }
    ]

# Test data constants
TEST_CUSTOMER_EMAIL = "test.customer@example.com"
TEST_CUSTOMER_PHONE = "+1234567890"
TEST_TICKET_ID = "TICK-TEST-001"
TEST_AGENT_EMAIL = "agent@company.com"

# Async test helpers
@pytest.fixture
def async_mock():
    """Helper to create async mocks"""
    def _async_mock(*args, **kwargs):
        mock = Mock(*args, **kwargs)
        mock.return_value = AsyncMock()
        return mock
    return _async_mock