"""
Test Ticket Creation functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
import json

from mcp_service.main import app
from mcp_service.routes.create_ticket import CreateTicketRequest, CreateTicketResponse

client = TestClient(app)

class TestCreateTicket:
    """Test cases for ticket creation"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value = Mock(data=[{"id": "log_123"}])
        return mock_client
    
    @pytest.fixture
    def mock_superops_response(self):
        """Mock SuperOps API response"""
        return {
            "ticket_id": "TICK-12345",
            "internal_id": "internal_123",
            "ticket_url": "https://superops.com/tickets/TICK-12345",
            "status": "open",
            "priority": "medium",
            "assigned_agent": "John Doe",
            "created_at": "2024-01-15T10:30:00Z",
            "estimated_resolution_time": "24 hours"
        }
    
    @pytest.fixture
    def valid_ticket_request(self):
        """Valid ticket creation request"""
        return {
            "title": "Login Issues",
            "description": "User cannot log into their account",
            "priority": "medium",
            "category": "authentication",
            "customer_email": "customer@example.com",
            "customer_phone": "+1234567890",
            "source": "email",
            "escalate_immediately": False,
            "tags": ["login", "authentication"],
            "attachments": []
        }
    
    @pytest.mark.asyncio
    async def test_create_ticket_success(self, mock_supabase_client, mock_superops_response, valid_ticket_request):
        """Test successful ticket creation"""
        with patch('mcp_service.routes.create_ticket.SuperOpsClient') as mock_superops:
            mock_superops_instance = Mock()
            mock_superops_instance.create_ticket = AsyncMock(return_value=mock_superops_response)
            mock_superops.return_value = mock_superops_instance
            
            with patch('mcp_service.routes.create_ticket.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/create_ticket", json=valid_ticket_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["ticket_id"] == "TICK-12345"
        assert data["ticket_url"] == "https://superops.com/tickets/TICK-12345"
        assert data["status"] == "open"
        assert data["priority"] == "medium"
        assert data["assigned_agent"] == "John Doe"
        assert data["estimated_resolution_time"] == "24 hours"
    
    def test_create_ticket_invalid_priority(self):
        """Test ticket creation with invalid priority"""
        invalid_request = {
            "title": "Test Issue",
            "description": "Test description",
            "priority": "invalid_priority",  # Invalid priority
            "category": "technical_issues",
            "customer_email": "test@example.com",
            "source": "email"
        }
        
        response = client.post("/mcp/create_ticket", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_create_ticket_invalid_email(self):
        """Test ticket creation with invalid email"""
        invalid_request = {
            "title": "Test Issue",
            "description": "Test description",
            "priority": "medium",
            "category": "technical_issues",
            "customer_email": "invalid_email",  # Invalid email format
            "source": "email"
        }
        
        response = client.post("/mcp/create_ticket", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_create_ticket_missing_required_fields(self):
        """Test ticket creation with missing required fields"""
        incomplete_request = {
            "title": "Test Issue",
            # Missing description, priority, category, customer_email
            "source": "email"
        }
        
        response = client.post("/mcp/create_ticket", json=incomplete_request)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_ticket_escalation(self, mock_supabase_client, valid_ticket_request):
        """Test ticket creation with immediate escalation"""
        escalated_request = valid_ticket_request.copy()
        escalated_request["escalate_immediately"] = True
        escalated_request["priority"] = "critical"
        
        mock_superops_response = {
            "ticket_id": "TICK-URGENT-001",
            "internal_id": "internal_urgent_123",
            "ticket_url": "https://superops.com/tickets/TICK-URGENT-001",
            "status": "escalated",
            "priority": "critical",
            "assigned_agent": "Senior Agent",
            "created_at": "2024-01-15T10:30:00Z",
            "estimated_resolution_time": "2 hours"
        }
        
        with patch('mcp_service.routes.create_ticket.SuperOpsClient') as mock_superops:
            mock_superops_instance = Mock()
            mock_superops_instance.create_ticket = AsyncMock(return_value=mock_superops_response)
            mock_superops.return_value = mock_superops_instance
            
            with patch('mcp_service.routes.create_ticket.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/create_ticket", json=escalated_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["ticket_id"] == "TICK-URGENT-001"
        assert data["status"] == "escalated"
        assert data["priority"] == "critical"
        assert data["estimated_resolution_time"] == "2 hours"
    
    @pytest.mark.asyncio
    async def test_schedule_callback_success(self, mock_supabase_client):
        """Test successful callback scheduling"""
        callback_request = {
            "customer_phone": "+1234567890",
            "customer_email": "customer@example.com",
            "priority": "within_2_hours",
            "ticket_id": "TICK-12345",
            "callback_reason": "urgent_issue_followup",
            "callback_type": "proactive_followup"
        }
        
        mock_callback_response = {
            "callback_id": "CB-001",
            "title": "Callback: proactive_followup",
            "scheduled_time": "2024-01-15T12:30:00Z",
            "assigned_agent": "Agent Smith",
            "status": "scheduled"
        }
        
        with patch('mcp_service.routes.create_ticket.SuperOpsClient') as mock_superops:
            mock_superops_instance = Mock()
            mock_superops_instance.create_callback_task = AsyncMock(return_value=mock_callback_response)
            mock_superops.return_value = mock_superops_instance
            
            with patch('mcp_service.routes.create_ticket.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/schedule_callback", json=callback_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["callback_id"] == "CB-001"
        assert data["status"] == "scheduled"
        assert data["assigned_agent"] == "Agent Smith"
    
    def test_schedule_callback_missing_contact_info(self):
        """Test callback scheduling without contact information"""
        invalid_request = {
            "priority": "within_2_hours",
            "callback_reason": "followup"
            # Missing both customer_phone and customer_email
        }
        
        response = client.post("/mcp/schedule_callback", json=invalid_request)
        assert response.status_code == 400
        assert "Either customer_phone or customer_email is required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_superops_api_error_handling(self, mock_supabase_client, valid_ticket_request):
        """Test handling of SuperOps API errors"""
        with patch('mcp_service.routes.create_ticket.SuperOpsClient') as mock_superops:
            mock_superops_instance = Mock()
            mock_superops_instance.create_ticket = AsyncMock(side_effect=Exception("SuperOps API Error"))
            mock_superops.return_value = mock_superops_instance
            
            with patch('mcp_service.routes.create_ticket.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/create_ticket", json=valid_ticket_request)
        
        assert response.status_code == 500
        assert "Failed to create ticket" in response.json()["detail"]

class TestCallbackTimeCalculation:
    """Test callback time calculation logic"""
    
    def test_calculate_immediate_callback(self):
        """Test immediate callback time calculation"""
        from mcp_service.routes.create_ticket import calculate_callback_time
        from datetime import datetime, timedelta
        
        callback_time_str = calculate_callback_time("immediate")
        callback_time = datetime.fromisoformat(callback_time_str)
        now = datetime.utcnow()
        
        # Should be within 30-35 minutes from now
        time_diff = callback_time - now
        assert timedelta(minutes=25) <= time_diff <= timedelta(minutes=35)
    
    def test_calculate_2_hour_callback(self):
        """Test 2-hour callback time calculation"""
        from mcp_service.routes.create_ticket import calculate_callback_time
        from datetime import datetime, timedelta
        
        callback_time_str = calculate_callback_time("within_2_hours")
        callback_time = datetime.fromisoformat(callback_time_str)
        now = datetime.utcnow()
        
        # Should be within 1.5-2.5 hours from now
        time_diff = callback_time - now
        assert timedelta(hours=1.5) <= time_diff <= timedelta(hours=2.5)
    
    def test_calculate_business_day_callback(self):
        """Test next business day callback calculation"""
        from mcp_service.routes.create_ticket import calculate_callback_time
        from datetime import datetime
        
        callback_time_str = calculate_callback_time("next_business_day")
        callback_time = datetime.fromisoformat(callback_time_str)
        
        # Should be on a weekday (Monday=0, Sunday=6)
        assert callback_time.weekday() < 5  # Monday to Friday
        # Should be at 9 AM
        assert callback_time.hour == 9
        assert callback_time.minute == 0

if __name__ == "__main__":
    pytest.main([__file__])