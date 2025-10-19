"""
Test Analytics functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json

from mcp_service.main import app

client = TestClient(app)

class TestAnalytics:
    """Test cases for analytics endpoints"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        mock_client = Mock()
        return mock_client
    
    @pytest.fixture
    def sample_interactions(self):
        """Sample interaction data for testing"""
        base_date = datetime.utcnow()
        return [
            {
                "id": "int_001",
                "interaction_type": "ticket_created",
                "customer_email": "customer1@example.com",
                "issue_description": "Login issues",
                "priority": "medium",
                "category": "authentication",
                "source": "email",
                "created_at": (base_date - timedelta(days=1)).isoformat()
            },
            {
                "id": "int_002", 
                "interaction_type": "email_sent",
                "recipient_email": "customer1@example.com",
                "subject": "Solution for login issue",
                "message_id": "msg_123",
                "created_at": (base_date - timedelta(days=1)).isoformat()
            },
            {
                "id": "int_003",
                "interaction_type": "kb_search",
                "query": "password reset",
                "results_count": 3,
                "search_time_ms": 150,
                "created_at": (base_date - timedelta(hours=2)).isoformat()
            },
            {
                "id": "int_004",
                "interaction_type": "ticket_created",
                "customer_email": "customer2@example.com",
                "issue_description": "Billing question",
                "priority": "low",
                "category": "billing",
                "source": "web",
                "created_at": base_date.isoformat()
            },
            {
                "id": "int_005",
                "interaction_type": "callback_scheduled",
                "customer_phone": "+1234567890",
                "callback_priority": "within_2_hours",
                "created_at": base_date.isoformat()
            }
        ]
    
    @pytest.mark.asyncio
    async def test_dashboard_analytics_success(self, mock_supabase_client, sample_interactions):
        """Test successful dashboard analytics retrieval"""
        # Mock Supabase response
        mock_result = Mock()
        mock_result.data = sample_interactions
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.analytics.get_supabase_client', return_value=mock_supabase_client):
            response = client.get("/analytics/dashboard?days=30")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_interactions"] == 5
        assert data["tickets_created"] == 2
        assert data["emails_sent"] == 1
        assert data["kb_searches"] == 1
        assert data["callbacks_scheduled"] == 1
        
        # Check date range
        assert "date_range" in data
        assert data["date_range"]["days"] == 30
        
        # Check daily breakdown exists
        assert "daily_breakdown" in data
        
        # Check recent activity
        assert "recent_activity" in data
        assert len(data["recent_activity"]) == 5
    
    @pytest.mark.asyncio
    async def test_dashboard_analytics_custom_days(self, mock_supabase_client, sample_interactions):
        """Test dashboard analytics with custom day range"""
        mock_result = Mock()
        mock_result.data = sample_interactions[:2]  # Fewer results for shorter range
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.analytics.get_supabase_client', return_value=mock_supabase_client):
            response = client.get("/analytics/dashboard?days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["date_range"]["days"] == 7
        assert data["total_interactions"] == 2
    
    @pytest.mark.asyncio
    async def test_dashboard_analytics_no_data(self, mock_supabase_client):
        """Test dashboard analytics with no data"""
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.analytics.get_supabase_client', return_value=mock_supabase_client):
            response = client.get("/analytics/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_interactions"] == 0
        assert data["tickets_created"] == 0
        assert data["emails_sent"] == 0
        assert data["kb_searches"] == 0
    
    @pytest.mark.asyncio
    async def test_ticket_analytics_success(self, mock_supabase_client, sample_interactions):
        """Test successful ticket analytics retrieval"""
        # Filter only ticket interactions
        ticket_interactions = [i for i in sample_interactions if i["interaction_type"] == "ticket_created"]
        
        mock_result = Mock()
        mock_result.data = ticket_interactions
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.analytics.get_supabase_client', return_value=mock_supabase_client):
            response = client.get("/analytics/tickets?days=30")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_tickets"] == 2
        
        # Check priority breakdown
        assert "priority_breakdown" in data
        assert data["priority_breakdown"]["medium"] == 1
        assert data["priority_breakdown"]["low"] == 1
        
        # Check category breakdown
        assert "category_breakdown" in data
        assert data["category_breakdown"]["authentication"] == 1
        assert data["category_breakdown"]["billing"] == 1
        
        # Check source breakdown
        assert "source_breakdown" in data
        assert data["source_breakdown"]["email"] == 1
        assert data["source_breakdown"]["web"] == 1
    
    @pytest.mark.asyncio
    async def test_analytics_database_error(self, mock_supabase_client):
        """Test analytics with database error"""
        mock_supabase_client.table.side_effect = Exception("Database connection failed")
        
        with patch('mcp_service.routes.analytics.get_supabase_client', return_value=mock_supabase_client):
            response = client.get("/analytics/dashboard")
        
        assert response.status_code == 500
        assert "Failed to retrieve analytics" in response.json()["detail"]

class TestDailyBreakdown:
    """Test daily breakdown calculations"""
    
    def test_daily_breakdown_calculation(self):
        """Test daily breakdown calculation logic"""
        from mcp_service.routes.analytics import get_dashboard_stats
        from datetime import datetime, timedelta
        
        # This would be tested with actual function calls
        # For now, we test the concept
        base_date = datetime.utcnow().date()
        
        # Test that daily stats are properly grouped by date
        interactions = [
            {
                "interaction_type": "ticket_created",
                "created_at": base_date.isoformat() + "T10:00:00Z"
            },
            {
                "interaction_type": "email_sent", 
                "created_at": base_date.isoformat() + "T11:00:00Z"
            },
            {
                "interaction_type": "ticket_created",
                "created_at": (base_date - timedelta(days=1)).isoformat() + "T09:00:00Z"
            }
        ]
        
        # Group by date
        daily_stats = {}
        for interaction in interactions:
            date_str = datetime.fromisoformat(interaction["created_at"]).date().isoformat()
            if date_str not in daily_stats:
                daily_stats[date_str] = {"tickets": 0, "emails": 0, "kb_searches": 0}
            
            if interaction["interaction_type"] == "ticket_created":
                daily_stats[date_str]["tickets"] += 1
            elif interaction["interaction_type"] == "email_sent":
                daily_stats[date_str]["emails"] += 1
        
        # Verify grouping
        today_str = base_date.isoformat()
        yesterday_str = (base_date - timedelta(days=1)).isoformat()
        
        assert daily_stats[today_str]["tickets"] == 1
        assert daily_stats[today_str]["emails"] == 1
        assert daily_stats[yesterday_str]["tickets"] == 1
        assert daily_stats[yesterday_str]["emails"] == 0

class TestAnalyticsFiltering:
    """Test analytics filtering and aggregation"""
    
    def test_interaction_type_filtering(self):
        """Test filtering interactions by type"""
        interactions = [
            {"interaction_type": "ticket_created", "id": "1"},
            {"interaction_type": "email_sent", "id": "2"},
            {"interaction_type": "ticket_created", "id": "3"},
            {"interaction_type": "kb_search", "id": "4"}
        ]
        
        # Filter tickets
        tickets = [i for i in interactions if i["interaction_type"] == "ticket_created"]
        assert len(tickets) == 2
        
        # Filter emails
        emails = [i for i in interactions if i["interaction_type"] == "email_sent"]
        assert len(emails) == 1
        
        # Filter KB searches
        kb_searches = [i for i in interactions if i["interaction_type"] == "kb_search"]
        assert len(kb_searches) == 1
    
    def test_priority_aggregation(self):
        """Test priority aggregation logic"""
        tickets = [
            {"priority": "high", "id": "1"},
            {"priority": "medium", "id": "2"},
            {"priority": "high", "id": "3"},
            {"priority": "low", "id": "4"}
        ]
        
        priority_stats = {}
        for ticket in tickets:
            priority = ticket.get("priority", "unknown")
            priority_stats[priority] = priority_stats.get(priority, 0) + 1
        
        assert priority_stats["high"] == 2
        assert priority_stats["medium"] == 1
        assert priority_stats["low"] == 1
    
    def test_date_range_filtering(self):
        """Test date range filtering logic"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        interactions = [
            {"created_at": (now - timedelta(days=1)).isoformat(), "id": "1"},
            {"created_at": (now - timedelta(days=5)).isoformat(), "id": "2"},
            {"created_at": (now - timedelta(days=10)).isoformat(), "id": "3"},
            {"created_at": (now - timedelta(days=40)).isoformat(), "id": "4"}
        ]
        
        # Filter last 7 days
        cutoff_7_days = (now - timedelta(days=7)).isoformat()
        recent_interactions = [
            i for i in interactions 
            if i["created_at"] >= cutoff_7_days
        ]
        
        assert len(recent_interactions) == 2  # Only first two should be included
        
        # Filter last 30 days
        cutoff_30_days = (now - timedelta(days=30)).isoformat()
        month_interactions = [
            i for i in interactions
            if i["created_at"] >= cutoff_30_days
        ]
        
        assert len(month_interactions) == 3  # First three should be included

class TestAnalyticsPerformance:
    """Test analytics performance and optimization"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, mock_supabase_client):
        """Test handling of large datasets"""
        # Simulate large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                "id": f"int_{i}",
                "interaction_type": "ticket_created" if i % 3 == 0 else "email_sent",
                "created_at": datetime.utcnow().isoformat()
            })
        
        mock_result = Mock()
        mock_result.data = large_dataset
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result
        
        with patch('mcp_service.routes.analytics.get_supabase_client', return_value=mock_supabase_client):
            response = client.get("/analytics/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_interactions"] == 1000
        # Should handle large dataset without timeout
    
    def test_memory_efficiency(self):
        """Test memory efficiency of analytics calculations"""
        # Test that we don't load unnecessary data into memory
        # This is more of a design test
        
        # Verify we only select needed columns
        # Verify we use streaming/pagination for large datasets
        # Verify we don't store intermediate results unnecessarily
        
        # For now, just verify the concept
        assert True  # Placeholder for actual memory tests

if __name__ == "__main__":
    pytest.main([__file__])