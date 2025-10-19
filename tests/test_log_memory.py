"""
Test Memory Logging functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
import json

from mcp_service.main import app

client = TestClient(app)

class TestLogMemory:
    """Test cases for memory logging"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value = Mock(data=[{"id": "log_123"}])
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=[{"id": "log_123"}])
        return mock_client
    
    @pytest.fixture
    def valid_log_request(self):
        """Valid memory log request"""
        return {
            "interaction_type": "email_processed",
            "customer_email": "customer@example.com",
            "customer_phone": "+1234567890",
            "issue_description": "Cannot log into account, password reset not working",
            "ai_analysis": {
                "issue_summary": "Authentication problem with password reset",
                "urgency_level": "medium",
                "suggested_category": "authentication",
                "key_points": ["login failure", "password reset", "account access"],
                "complexity_level": "moderate",
                "estimated_resolution_time": "15 minutes",
                "requires_escalation": False
            },
            "resolution_type": "knowledge_base_match",
            "ticket_id": None,
            "sentiment_analysis": {
                "sentiment_score": -0.2,
                "frustration_level": "medium",
                "urgency_level": "medium",
                "escalation_needed": False,
                "key_emotions": ["frustrated", "confused"],
                "customer_tone_progression": "neutral to frustrated"
            },
            "metadata": {
                "source": "email",
                "processing_time_ms": 1500,
                "kb_search_results": 3,
                "auto_response_sent": True
            },
            "tags": ["authentication", "password", "login", "account_access"]
        }
    
    @pytest.mark.asyncio
    async def test_log_memory_success(self, mock_supabase_client, valid_log_request):
        """Test successful memory logging"""
        with patch('mcp_service.routes.log_memory.get_supabase_client', return_value=mock_supabase_client):
            response = client.post("/mcp/log_memory", json=valid_log_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "log_id" in data
        assert data["status"] == "logged"
        assert "logged_at" in data
        
        # Verify Supabase insert was called
        mock_supabase_client.table.assert_called_with("support_interactions")
    
    def test_log_memory_missing_required_fields(self):
        """Test memory logging with missing required fields"""
        incomplete_request = {
            "interaction_type": "email_processed",
            # Missing issue_description
            "customer_email": "test@example.com"
        }
        
        response = client.post("/mcp/log_memory", json=incomplete_request)
        assert response.status_code == 422  # Validation error
    
    def test_log_memory_invalid_email(self):
        """Test memory logging with invalid email"""
        invalid_request = {
            "interaction_type": "email_processed",
            "customer_email": "invalid_email",  # Invalid email format
            "issue_description": "Test issue"
        }
        
        response = client.post("/mcp/log_memory", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_log_memory_with_ticket_id(self, mock_supabase_client):
        """Test memory logging with associated ticket"""
        ticket_log_request = {
            "interaction_type": "ticket_created",
            "customer_email": "customer@example.com",
            "issue_description": "Complex billing issue requiring escalation",
            "resolution_type": "ticket_created",
            "ticket_id": "TICK-12345",
            "ai_analysis": {
                "requires_escalation": True,
                "complexity_level": "high"
            },
            "tags": ["billing", "escalation", "complex"]
        }
        
        with patch('mcp_service.routes.log_memory.get_supabase_client', return_value=mock_supabase_client):
            response = client.post("/mcp/log_memory", json=ticket_log_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "logged"
    
    @pytest.mark.asyncio
    async def test_memory_search_by_email(self, mock_supabase_client):
        """Test memory search by customer email"""
        sample_interactions = [
            {
                "id": "int_001",
                "interaction_type": "email_processed",
                "customer_email": "customer@example.com",
                "issue_description": "Login issues",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        mock_result = Mock()
        mock_result.data = sample_interactions
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.log_memory.get_supabase_client', return_value=mock_supabase_client):
            response = client.get("/memory_search?customer_email=customer@example.com")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["interactions"]) == 1
        assert data["total_found"] == 1
        assert data["search_criteria"]["customer_email"] == "customer@example.com"
    
    @pytest.mark.asyncio
    async def test_memory_search_by_interaction_type(self, mock_supabase_client):
        """Test memory search by interaction type"""
        sample_interactions = [
            {
                "id": "int_001",
                "interaction_type": "ticket_created",
                "customer_email": "customer1@example.com",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "int_002", 
                "interaction_type": "ticket_created",
                "customer_email": "customer2@example.com",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        mock_result = Mock()
        mock_result.data = sample_interactions
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.log_memory.get_supabase_client', return_value=mock_supabase_client):
            response = client.get("/memory_search?interaction_type=ticket_created")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["interactions"]) == 2
        assert data["search_criteria"]["interaction_type"] == "ticket_created"
    
    @pytest.mark.asyncio
    async def test_memory_search_with_date_filter(self, mock_supabase_client):
        """Test memory search with date filtering"""
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.log_memory.get_supabase_client', return_value=mock_supabase_client):
            response = client.get("/memory_search?days_back=7&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["search_criteria"]["days_back"] == 7
    
    @pytest.mark.asyncio
    async def test_memory_analytics_success(self, mock_supabase_client):
        """Test memory analytics generation"""
        sample_interactions = [
            {
                "interaction_type": "email_processed",
                "resolution_type": "knowledge_base_match",
                "sentiment_analysis": {"score": 0.5},
                "ticket_id": None
            },
            {
                "interaction_type": "ticket_created", 
                "resolution_type": "escalated",
                "sentiment_analysis": {"score": -0.3},
                "ticket_id": "TICK-001"
            },
            {
                "interaction_type": "email_processed",
                "resolution_type": "auto_resolved",
                "sentiment_analysis": {"score": 0.8},
                "ticket_id": None
            }
        ]
        
        mock_result = Mock()
        mock_result.data = sample_interactions
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.log_memory.get_supabase_client', return_value=mock_supabase_client):
            response = client.get("/memory_analytics?days_back=30")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_interactions"] == 3
        assert "interaction_types" in data
        assert "resolution_types" in data
        assert "ticket_creation_rate" in data
        assert "auto_resolution_rate" in data
    
    @pytest.mark.asyncio
    async def test_update_interaction_success(self, mock_supabase_client):
        """Test successful interaction update"""
        update_data = {
            "resolution_type": "resolved",
            "customer_satisfaction": "satisfied",
            "follow_up_needed": False
        }
        
        mock_result = Mock()
        mock_result.data = [{"id": "int_123", **update_data}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.log_memory.get_supabase_client', return_value=mock_supabase_client):
            response = client.post("/update_interaction?interaction_id=int_123", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["interaction_id"] == "int_123"
        assert data["status"] == "updated"
        assert "updated_at" in data
    
    @pytest.mark.asyncio
    async def test_update_interaction_not_found(self, mock_supabase_client):
        """Test updating non-existent interaction"""
        mock_result = Mock()
        mock_result.data = []  # No data returned = not found
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.log_memory.get_supabase_client', return_value=mock_supabase_client):
            response = client.post("/update_interaction?interaction_id=nonexistent", json={"status": "updated"})
        
        assert response.status_code == 404
        assert "Interaction not found" in response.json()["detail"]

class TestAnalyticsCalculations:
    """Test analytics calculation functions"""
    
    def test_calculate_interaction_analytics_empty(self):
        """Test analytics calculation with empty data"""
        from mcp_service.routes.log_memory import calculate_interaction_analytics
        
        result = calculate_interaction_analytics([])
        
        assert result["total_interactions"] == 0
        assert result["interaction_types"] == {}
        assert result["resolution_types"] == {}
        assert result["avg_sentiment_score"] is None
        assert result["ticket_creation_rate"] == 0
        assert result["auto_resolution_rate"] == 0
    
    def test_calculate_interaction_analytics_with_data(self):
        """Test analytics calculation with sample data"""
        from mcp_service.routes.log_memory import calculate_interaction_analytics
        
        interactions = [
            {
                "interaction_type": "email_processed",
                "resolution_type": "knowledge_base_match",
                "sentiment_analysis": {"score": 0.5},
                "ticket_id": None
            },
            {
                "interaction_type": "ticket_created",
                "resolution_type": "escalated", 
                "sentiment_analysis": {"score": -0.2},
                "ticket_id": "TICK-001"
            },
            {
                "interaction_type": "email_processed",
                "resolution_type": "auto_resolved",
                "sentiment_analysis": {"score": 0.8},
                "ticket_id": None
            },
            {
                "interaction_type": "kb_search",
                "resolution_type": None,
                "sentiment_analysis": None,
                "ticket_id": None
            }
        ]
        
        result = calculate_interaction_analytics(interactions)
        
        assert result["total_interactions"] == 4
        assert result["interaction_types"]["email_processed"] == 2
        assert result["interaction_types"]["ticket_created"] == 1
        assert result["interaction_types"]["kb_search"] == 1
        
        assert result["resolution_types"]["knowledge_base_match"] == 1
        assert result["resolution_types"]["auto_resolved"] == 1
        assert result["resolution_types"]["escalated"] == 1
        
        assert result["ticket_creation_rate"] == 25.0  # 1 out of 4
        assert result["auto_resolution_rate"] == 50.0  # 2 out of 4 (kb_match + auto_resolved)
        
        # Average sentiment: (0.5 + (-0.2) + 0.8) / 3 = 0.367
        assert abs(result["avg_sentiment_score"] - 0.367) < 0.01
    
    def test_sentiment_analysis_aggregation(self):
        """Test sentiment analysis aggregation"""
        from mcp_service.routes.log_memory import calculate_interaction_analytics
        
        interactions = [
            {"sentiment_analysis": {"score": 0.9}},
            {"sentiment_analysis": {"score": -0.5}},
            {"sentiment_analysis": {"score": 0.2}},
            {"sentiment_analysis": None},  # Should be ignored
            {"sentiment_analysis": {"score": "invalid"}},  # Should be ignored
        ]
        
        result = calculate_interaction_analytics(interactions)
        
        sentiment_data = result["sentiment_data"]
        assert sentiment_data["total_scored"] == 3
        assert abs(sentiment_data["avg_score"] - 0.2) < 0.01  # (0.9 + (-0.5) + 0.2) / 3
        assert sentiment_data["min_score"] == -0.5
        assert sentiment_data["max_score"] == 0.9

class TestMemorySearchFiltering:
    """Test memory search filtering logic"""
    
    def test_multiple_filter_combination(self):
        """Test combining multiple search filters"""
        # This tests the concept of how filters would be combined
        # In actual implementation, this would be done in SQL
        
        interactions = [
            {
                "customer_email": "customer1@example.com",
                "interaction_type": "ticket_created",
                "ticket_id": "TICK-001"
            },
            {
                "customer_email": "customer1@example.com", 
                "interaction_type": "email_sent",
                "ticket_id": None
            },
            {
                "customer_email": "customer2@example.com",
                "interaction_type": "ticket_created", 
                "ticket_id": "TICK-002"
            }
        ]
        
        # Filter by email AND interaction type
        filtered = [
            i for i in interactions 
            if i["customer_email"] == "customer1@example.com" 
            and i["interaction_type"] == "ticket_created"
        ]
        
        assert len(filtered) == 1
        assert filtered[0]["ticket_id"] == "TICK-001"
    
    def test_date_range_filtering_logic(self):
        """Test date range filtering logic"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        interactions = [
            {"created_at": (now - timedelta(days=1)).isoformat()},
            {"created_at": (now - timedelta(days=5)).isoformat()},
            {"created_at": (now - timedelta(days=10)).isoformat()},
            {"created_at": (now - timedelta(days=40)).isoformat()}
        ]
        
        # Filter last 7 days
        cutoff = (now - timedelta(days=7)).isoformat()
        recent = [i for i in interactions if i["created_at"] >= cutoff]
        
        assert len(recent) == 2  # Only first two should be included

if __name__ == "__main__":
    pytest.main([__file__])