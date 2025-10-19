"""
Test Email Sending functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import json

from mcp_service.main import app

client = TestClient(app)

class TestSendEmail:
    """Test cases for email sending"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value = Mock(data=[{"id": "log_123"}])
        return mock_client
    
    @pytest.fixture
    def mock_gmail_response(self):
        """Mock Gmail API response"""
        return {
            "message_id": "msg_12345",
            "thread_id": "thread_67890",
            "status": "sent"
        }
    
    @pytest.fixture
    def valid_email_request(self):
        """Valid email sending request"""
        return {
            "to": "customer@example.com",
            "subject": "Re: Your Support Request",
            "body": "Thank you for contacting support. Here's the solution to your issue...",
            "thread_id": None,
            "template": None,
            "attachments": [],
            "cc": [],
            "bcc": [],
            "reply_to": None
        }
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_supabase_client, mock_gmail_response, valid_email_request):
        """Test successful email sending"""
        with patch('mcp_service.routes.send_email.GmailClient') as mock_gmail:
            mock_gmail_instance = Mock()
            mock_gmail_instance.send_email = AsyncMock(return_value=mock_gmail_response)
            mock_gmail.return_value = mock_gmail_instance
            
            with patch('mcp_service.routes.send_email.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/send_email", json=valid_email_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message_id"] == "msg_12345"
        assert data["thread_id"] == "thread_67890"
        assert data["status"] == "sent"
        assert data["recipient"] == "customer@example.com"
        assert data["subject"] == "Re: Your Support Request"
    
    def test_send_email_invalid_recipient(self):
        """Test email sending with invalid recipient"""
        invalid_request = {
            "to": "invalid_email",  # Invalid email format
            "subject": "Test Subject",
            "body": "Test body"
        }
        
        response = client.post("/mcp/send_email", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_send_email_missing_required_fields(self):
        """Test email sending with missing required fields"""
        incomplete_request = {
            "to": "test@example.com",
            # Missing subject and body
        }
        
        response = client.post("/mcp/send_email", json=incomplete_request)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_send_email_with_template(self, mock_supabase_client, mock_gmail_response):
        """Test email sending with template"""
        template_request = {
            "to": "customer@example.com",
            "subject": "Solution for Your Issue",
            "body": "Here's how to resolve your login problem...",
            "template": "solution_response"
        }
        
        with patch('mcp_service.routes.send_email.GmailClient') as mock_gmail:
            mock_gmail_instance = Mock()
            mock_gmail_instance.send_email = AsyncMock(return_value=mock_gmail_response)
            mock_gmail.return_value = mock_gmail_instance
            
            with patch('mcp_service.routes.send_email.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/send_email", json=template_request)
        
        assert response.status_code == 200
        # Verify template processing was called
        mock_gmail_instance.send_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_bulk_email_success(self, mock_supabase_client, mock_gmail_response):
        """Test successful bulk email sending"""
        bulk_request = {
            "recipients": [
                {
                    "email": "customer1@example.com",
                    "personalization": {"customer_name": "John Doe"}
                },
                {
                    "email": "customer2@example.com", 
                    "personalization": {"customer_name": "Jane Smith"}
                }
            ],
            "subject": "Hello {customer_name}",
            "body": "Dear {customer_name}, thank you for your inquiry...",
            "template": None
        }
        
        with patch('mcp_service.routes.send_email.GmailClient') as mock_gmail:
            mock_gmail_instance = Mock()
            mock_gmail_instance.send_email = AsyncMock(return_value=mock_gmail_response)
            mock_gmail.return_value = mock_gmail_instance
            
            with patch('mcp_service.routes.send_email.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/send_bulk_email", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_recipients"] == 2
        assert data["successful_sends"] == 2
        assert data["failed_sends"] == 0
        assert len(data["results"]) == 2
    
    def test_send_bulk_email_empty_recipients(self):
        """Test bulk email with empty recipients list"""
        empty_request = {
            "recipients": [],
            "subject": "Test Subject",
            "body": "Test body"
        }
        
        response = client.post("/mcp/send_bulk_email", json=empty_request)
        assert response.status_code == 400
        assert "recipients list is required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_gmail_status_check_connected(self):
        """Test Gmail status check when connected"""
        mock_profile = {
            "emailAddress": "support@company.com",
            "messagesTotal": 1500,
            "threadsTotal": 800
        }
        
        with patch('mcp_service.routes.send_email.GmailClient') as mock_gmail:
            mock_gmail_instance = Mock()
            mock_gmail_instance.service.users.return_value.getProfile.return_value.execute.return_value = mock_profile
            mock_gmail.return_value = mock_gmail_instance
            
            response = client.get("/mcp/check-gmail-status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["connected"] == True
        assert data["email_address"] == "support@company.com"
        assert data["messages_total"] == 1500
    
    @pytest.mark.asyncio
    async def test_gmail_status_check_disconnected(self):
        """Test Gmail status check when not connected"""
        with patch('mcp_service.routes.send_email.GmailClient') as mock_gmail:
            mock_gmail.side_effect = Exception("Gmail authentication failed")
            
            response = client.get("/mcp/check-gmail-status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["connected"] == False
        assert "error" in data

class TestEmailTemplates:
    """Test email template processing"""
    
    @pytest.mark.asyncio
    async def test_solution_response_template(self):
        """Test solution response template processing"""
        from mcp_service.routes.send_email import process_email_template
        
        result = await process_email_template(
            template_name="solution_response",
            body="Here's how to reset your password...",
            recipient="customer@example.com",
            personalization={"customer_name": "John Doe"}
        )
        
        assert "Hello John Doe" in result
        assert "Thank you for contacting support" in result
        assert "Here's how to reset your password..." in result
        assert "SuperTickets.AI Support Team" in result
    
    @pytest.mark.asyncio
    async def test_ticket_created_template(self):
        """Test ticket created template processing"""
        from mcp_service.routes.send_email import process_email_template
        
        result = await process_email_template(
            template_name="ticket_created",
            body="Your ticket has been created successfully.",
            recipient="customer@example.com",
            personalization={
                "customer_name": "Jane Smith",
                "ticket_id": "TICK-12345"
            }
        )
        
        assert "Hello Jane Smith" in result
        assert "We've received your support request" in result
        assert "Ticket #TICK-12345" in result
    
    @pytest.mark.asyncio
    async def test_unknown_template(self):
        """Test processing with unknown template"""
        from mcp_service.routes.send_email import process_email_template
        
        original_body = "This is the original body"
        result = await process_email_template(
            template_name="unknown_template",
            body=original_body,
            recipient="customer@example.com"
        )
        
        # Should return original body when template is unknown
        assert result == original_body
    
    def test_personalize_content(self):
        """Test content personalization"""
        from mcp_service.routes.send_email import personalize_content
        
        content = "Hello {customer_name}, your ticket {ticket_id} has been updated."
        personalization = {
            "customer_name": "John Doe",
            "ticket_id": "TICK-12345"
        }
        
        result = personalize_content(content, personalization)
        
        assert result == "Hello John Doe, your ticket TICK-12345 has been updated."
    
    def test_personalize_content_missing_values(self):
        """Test content personalization with missing values"""
        from mcp_service.routes.send_email import personalize_content
        
        content = "Hello {customer_name}, your ticket {ticket_id} has been updated."
        personalization = {
            "customer_name": "John Doe"
            # Missing ticket_id
        }
        
        result = personalize_content(content, personalization)
        
        # Should replace available values and leave missing ones as placeholders
        assert "Hello John Doe" in result
        assert "{ticket_id}" in result

if __name__ == "__main__":
    pytest.main([__file__])