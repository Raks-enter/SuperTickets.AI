"""
Test Utility functions and clients
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import os
from datetime import datetime, timedelta

class TestSupabaseClient:
    """Test Supabase client functionality"""
    
    @pytest.fixture
    def mock_supabase_env(self):
        """Mock Supabase environment variables"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test_key'
        }):
            yield
    
    def test_supabase_client_initialization(self, mock_supabase_env):
        """Test Supabase client initialization"""
        with patch('mcp_service.utils.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            
            from mcp_service.utils.supabase_client import get_supabase_client
            
            client = get_supabase_client()
            
            assert client is not None
            mock_create.assert_called_once_with(
                'https://test.supabase.co',
                'test_key'
            )
    
    def test_supabase_client_missing_env(self):
        """Test Supabase client with missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            from mcp_service.utils.supabase_client import get_supabase_client
            
            with pytest.raises(Exception):
                get_supabase_client()

class TestGmailClient:
    """Test Gmail client functionality"""
    
    @pytest.fixture
    def mock_gmail_credentials(self):
        """Mock Gmail credentials"""
        with patch('os.path.exists', return_value=True):
            with patch('mcp_service.utils.gmail_client.Credentials') as mock_creds:
                mock_creds.from_authorized_user_file.return_value = Mock(valid=True)
                yield mock_creds
    
    @pytest.fixture
    def mock_gmail_service(self):
        """Mock Gmail service"""
        with patch('mcp_service.utils.gmail_client.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            yield mock_service
    
    def test_gmail_client_initialization(self, mock_gmail_credentials, mock_gmail_service):
        """Test Gmail client initialization"""
        from mcp_service.utils.gmail_client import GmailClient
        
        client = GmailClient()
        
        assert client.service is not None
    
    @pytest.mark.asyncio
    async def test_gmail_send_email(self, mock_gmail_credentials, mock_gmail_service):
        """Test Gmail email sending"""
        from mcp_service.utils.gmail_client import GmailClient
        
        # Mock the send response
        mock_response = {
            "id": "msg_123",
            "threadId": "thread_456"
        }
        mock_gmail_service.users.return_value.messages.return_value.send.return_value.execute.return_value = mock_response
        
        client = GmailClient()
        
        email_data = {
            "to": "test@example.com",
            "subject": "Test Subject",
            "body": "Test body",
            "cc": [],
            "bcc": [],
            "attachments": []
        }
        
        result = await client.send_email(email_data)
        
        assert result["message_id"] == "msg_123"
        assert result["thread_id"] == "thread_456"
        assert result["status"] == "sent"
    
    @pytest.mark.asyncio
    async def test_gmail_get_messages(self, mock_gmail_credentials, mock_gmail_service):
        """Test Gmail message retrieval"""
        from mcp_service.utils.gmail_client import GmailClient
        
        # Mock messages list response
        mock_list_response = {
            "messages": [{"id": "msg_123"}]
        }
        mock_gmail_service.users.return_value.messages.return_value.list.return_value.execute.return_value = mock_list_response
        
        # Mock individual message response
        mock_message_response = {
            "id": "msg_123",
            "threadId": "thread_456",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Date", "value": "Mon, 15 Jan 2024 10:00:00 +0000"}
                ],
                "mimeType": "text/plain",
                "body": {
                    "data": "VGVzdCBib2R5"  # Base64 encoded "Test body"
                }
            }
        }
        mock_gmail_service.users.return_value.messages.return_value.get.return_value.execute.return_value = mock_message_response
        
        client = GmailClient()
        
        messages = await client.get_messages(query="is:unread", max_results=10)
        
        assert len(messages) == 1
        assert messages[0]["id"] == "msg_123"
        assert messages[0]["subject"] == "Test Subject"
    
    def test_gmail_create_message(self, mock_gmail_credentials, mock_gmail_service):
        """Test Gmail message creation"""
        from mcp_service.utils.gmail_client import GmailClient
        
        client = GmailClient()
        
        message = client._create_message(
            to="test@example.com",
            subject="Test Subject",
            body="Test body"
        )
        
        assert "raw" in message
        assert isinstance(message["raw"], str)

class TestBedrockClient:
    """Test AWS Bedrock client functionality"""
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Mock Bedrock client"""
        with patch('boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_boto3.return_value = mock_client
            yield mock_client
    
    @pytest.mark.asyncio
    async def test_bedrock_analyze_issue(self, mock_bedrock_client):
        """Test Bedrock issue analysis"""
        # Mock Bedrock response
        mock_response = {
            "body": Mock()
        }
        mock_response["body"].read.return_value = b'{"issue_summary": "Login problem", "urgency_level": "medium"}'
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        from mcp_service.utils.bedrock_client import BedrockClient
        
        client = BedrockClient()
        
        result = await client.analyze_issue(
            issue_text="I can't log into my account",
            context="email"
        )
        
        assert "issue_summary" in result
        assert "urgency_level" in result
    
    @pytest.mark.asyncio
    async def test_bedrock_extract_call_info(self, mock_bedrock_client):
        """Test Bedrock call information extraction"""
        mock_response = {
            "body": Mock()
        }
        mock_response["body"].read.return_value = b'{"customer_name": "John Doe", "issue_description": "Login issues"}'
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        from mcp_service.utils.bedrock_client import BedrockClient
        
        client = BedrockClient()
        
        result = await client.extract_call_info(
            transcript="Customer called about login issues...",
            caller_phone="+1234567890"
        )
        
        assert "customer_name" in result
        assert "issue_description" in result

class TestSuperOpsClient:
    """Test SuperOps client functionality"""
    
    @pytest.fixture
    def mock_superops_env(self):
        """Mock SuperOps environment variables"""
        with patch.dict(os.environ, {
            'SUPEROPS_API_URL': 'https://api.superops.com/graphql',
            'SUPEROPS_API_KEY': 'test_api_key'
        }):
            yield
    
    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for SuperOps"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            yield mock_instance
    
    @pytest.mark.asyncio
    async def test_superops_create_ticket(self, mock_superops_env, mock_http_client):
        """Test SuperOps ticket creation"""
        # Mock GraphQL response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "createTicket": {
                    "ticket_id": "TICK-12345",
                    "ticket_url": "https://superops.com/tickets/TICK-12345",
                    "status": "open"
                }
            }
        }
        mock_http_client.post.return_value = mock_response
        
        from mcp_service.utils.superops_api import SuperOpsClient
        
        client = SuperOpsClient()
        
        ticket_data = {
            "title": "Test Issue",
            "description": "Test description",
            "priority": "medium",
            "customer": {
                "email": "customer@example.com"
            }
        }
        
        result = await client.create_ticket(ticket_data)
        
        assert result["ticket_id"] == "TICK-12345"
        assert result["status"] == "open"
    
    @pytest.mark.asyncio
    async def test_superops_create_callback_task(self, mock_superops_env, mock_http_client):
        """Test SuperOps callback task creation"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "createTask": {
                    "callback_id": "CB-001",
                    "status": "scheduled"
                }
            }
        }
        mock_http_client.post.return_value = mock_response
        
        from mcp_service.utils.superops_api import SuperOpsClient
        
        client = SuperOpsClient()
        
        callback_data = {
            "type": "callback",
            "customer_phone": "+1234567890",
            "scheduled_time": "2024-01-16T14:00:00Z"
        }
        
        result = await client.create_callback_task(callback_data)
        
        assert result["callback_id"] == "CB-001"
        assert result["status"] == "scheduled"

class TestEmbeddingSearch:
    """Test embedding search functionality"""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock()]
            mock_response.data[0].embedding = [0.1] * 1536
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for embedding search"""
        mock_client = Mock()
        mock_client.search_knowledge_base = AsyncMock()
        return mock_client
    
    @pytest.mark.asyncio
    async def test_create_embedding(self, mock_openai_client, mock_supabase_client):
        """Test embedding creation"""
        from mcp_service.utils.embedding_search import EmbeddingSearch
        
        search = EmbeddingSearch(mock_supabase_client)
        
        embedding = await search.create_embedding("test text")
        
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_vector_search(self, mock_openai_client, mock_supabase_client):
        """Test vector similarity search"""
        from mcp_service.utils.embedding_search import EmbeddingSearch
        
        # Mock search results
        mock_results = [
            {
                "id": "kb_001",
                "title": "Test Article",
                "similarity_score": 0.95
            }
        ]
        mock_supabase_client.search_knowledge_base.return_value = mock_results
        
        search = EmbeddingSearch(mock_supabase_client)
        
        results = await search.search(
            query="test query",
            threshold=0.8,
            limit=5
        )
        
        assert len(results) == 1
        assert results[0]["similarity_score"] == 0.95
    
    def test_cosine_similarity(self, mock_supabase_client):
        """Test cosine similarity calculation"""
        from mcp_service.utils.embedding_search import EmbeddingSearch
        
        search = EmbeddingSearch(mock_supabase_client)
        
        # Test identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = search.cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001
        
        # Test orthogonal vectors
        vec3 = [0.0, 1.0, 0.0]
        similarity = search.cosine_similarity(vec1, vec3)
        assert abs(similarity - 0.0) < 0.001

class TestCalendarClient:
    """Test Google Calendar client functionality"""
    
    @pytest.fixture
    def mock_calendar_credentials(self):
        """Mock Calendar credentials"""
        with patch('os.path.exists', return_value=True):
            with patch('mcp_service.utils.calendar_client.Credentials') as mock_creds:
                mock_creds.from_authorized_user_file.return_value = Mock(valid=True)
                yield mock_creds
    
    @pytest.fixture
    def mock_calendar_service(self):
        """Mock Calendar service"""
        with patch('mcp_service.utils.calendar_client.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            yield mock_service
    
    @pytest.mark.asyncio
    async def test_calendar_create_meeting(self, mock_calendar_credentials, mock_calendar_service):
        """Test Calendar meeting creation"""
        from mcp_service.utils.calendar_client import GoogleCalendarClient
        
        # Mock event creation response
        mock_event_response = {
            "id": "event_123",
            "htmlLink": "https://calendar.google.com/event/123",
            "start": {"dateTime": "2024-01-16T14:00:00Z"},
            "end": {"dateTime": "2024-01-16T14:30:00Z"},
            "attendees": [{"email": "customer@example.com"}],
            "hangoutLink": "https://meet.google.com/abc-defg-hij"
        }
        mock_calendar_service.events.return_value.insert.return_value.execute.return_value = mock_event_response
        
        client = GoogleCalendarClient()
        
        meeting_data = {
            "customer_email": "customer@example.com",
            "start_time": "2024-01-16T14:00:00Z",
            "duration_minutes": 30,
            "meeting_type": "support_followup"
        }
        
        result = await client.create_meeting(meeting_data)
        
        assert result["event_id"] == "event_123"
        assert result["meeting_url"] == "https://meet.google.com/abc-defg-hij"
    
    @pytest.mark.asyncio
    async def test_calendar_check_availability(self, mock_calendar_credentials, mock_calendar_service):
        """Test Calendar availability checking"""
        from mcp_service.utils.calendar_client import GoogleCalendarClient
        
        # Mock freebusy response
        mock_freebusy_response = {
            "calendars": {
                "customer@example.com": {
                    "busy": []
                },
                "support@company.com": {
                    "busy": [
                        {
                            "start": "2024-01-16T14:30:00Z",
                            "end": "2024-01-16T15:30:00Z"
                        }
                    ]
                }
            }
        }
        mock_calendar_service.freebusy.return_value.query.return_value.execute.return_value = mock_freebusy_response
        
        client = GoogleCalendarClient()
        
        availability_data = {
            "attendees": ["customer@example.com", "support@company.com"],
            "start_time": "2024-01-16T14:00:00Z",
            "end_time": "2024-01-16T15:00:00Z"
        }
        
        result = await client.check_availability(availability_data)
        
        assert result["customer@example.com"]["available"] == True
        assert result["support@company.com"]["available"] == False
        assert len(result["support@company.com"]["busy_times"]) == 1

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_datetime_formatting(self):
        """Test datetime formatting utilities"""
        from datetime import datetime
        
        # Test ISO format
        dt = datetime(2024, 1, 15, 14, 30, 0)
        iso_string = dt.isoformat()
        
        assert iso_string == "2024-01-15T14:30:00"
        
        # Test parsing
        parsed_dt = datetime.fromisoformat(iso_string)
        assert parsed_dt == dt
    
    def test_email_validation(self):
        """Test email validation utility"""
        import re
        
        def is_valid_email(email):
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(pattern, email) is not None
        
        # Valid emails
        assert is_valid_email("user@example.com") == True
        assert is_valid_email("test.email+tag@domain.co.uk") == True
        
        # Invalid emails
        assert is_valid_email("invalid_email") == False
        assert is_valid_email("@domain.com") == False
        assert is_valid_email("user@") == False
    
    def test_phone_number_formatting(self):
        """Test phone number formatting utility"""
        import re
        
        def format_phone_number(phone):
            # Remove all non-digit characters
            digits = re.sub(r'\D', '', phone)
            
            # Format as +1XXXXXXXXXX for US numbers
            if len(digits) == 10:
                return f"+1{digits}"
            elif len(digits) == 11 and digits.startswith('1'):
                return f"+{digits}"
            else:
                return phone  # Return as-is if not standard format
        
        assert format_phone_number("(555) 123-4567") == "+15551234567"
        assert format_phone_number("555-123-4567") == "+15551234567"
        assert format_phone_number("15551234567") == "+15551234567"
    
    def test_text_sanitization(self):
        """Test text sanitization utility"""
        import html
        
        def sanitize_text(text):
            # HTML escape
            escaped = html.escape(text)
            
            # Remove potential script tags (basic)
            import re
            cleaned = re.sub(r'<script.*?</script>', '', escaped, flags=re.IGNORECASE | re.DOTALL)
            
            return cleaned
        
        malicious_input = "<script>alert('xss')</script>Hello"
        sanitized = sanitize_text(malicious_input)
        
        assert "<script>" not in sanitized
        assert "Hello" in sanitized

if __name__ == "__main__":
    pytest.main([__file__])