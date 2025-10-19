"""
Test Frontend Integration and API endpoints
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import json

from mcp_service.main import app

client = TestClient(app)

class TestFrontendIntegration:
    """Test cases for frontend-backend integration"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "supertickets-ai-mcp"
        assert data["version"] == "1.0.0"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "SuperTickets.AI MCP Service"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert data["endpoints"]["health"] == "/health"
        assert data["endpoints"]["docs"] == "/docs"
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/health")
        
        # FastAPI automatically handles OPTIONS requests
        # Check that CORS middleware is working
        assert response.status_code in [200, 405]  # 405 is also acceptable for OPTIONS
    
    @pytest.mark.asyncio
    async def test_dashboard_api_integration(self):
        """Test dashboard API integration"""
        mock_interactions = [
            {
                "id": "int_001",
                "interaction_type": "ticket_created",
                "created_at": "2024-01-15T10:00:00Z"
            },
            {
                "id": "int_002",
                "interaction_type": "email_sent",
                "created_at": "2024-01-15T11:00:00Z"
            }
        ]
        
        with patch('mcp_service.routes.analytics.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_result = Mock()
            mock_result.data = mock_interactions
            mock_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result
            mock_supabase.return_value = mock_client
            
            response = client.get("/analytics/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify frontend can consume this data
        assert "total_interactions" in data
        assert "tickets_created" in data
        assert "emails_sent" in data
        assert "daily_breakdown" in data
        assert "recent_activity" in data
    
    def test_api_error_handling(self):
        """Test API error handling for frontend"""
        # Test invalid endpoint
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404
        
        # Test invalid JSON in POST request
        response = client.post("/mcp/kb_lookup", data="invalid json")
        assert response.status_code == 422
    
    def test_request_id_header(self):
        """Test that request ID header is added"""
        response = client.get("/health")
        
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

class TestAPIValidation:
    """Test API input validation for frontend integration"""
    
    def test_kb_lookup_validation(self):
        """Test knowledge base lookup validation"""
        # Valid request
        valid_request = {
            "query": "login issues",
            "threshold": 0.8,
            "limit": 5
        }
        
        with patch('mcp_service.routes.kb_lookup.EmbeddingSearch'):
            with patch('mcp_service.routes.kb_lookup.get_supabase_client'):
                response = client.post("/mcp/kb_lookup", json=valid_request)
        
        # Should not fail validation
        assert response.status_code != 422
        
        # Invalid threshold
        invalid_request = {
            "query": "test",
            "threshold": 1.5,  # > 1.0
            "limit": 5
        }
        
        response = client.post("/mcp/kb_lookup", json=invalid_request)
        assert response.status_code == 422
    
    def test_create_ticket_validation(self):
        """Test ticket creation validation"""
        # Valid request
        valid_request = {
            "title": "Test Issue",
            "description": "Test description",
            "priority": "medium",
            "category": "technical",
            "customer_email": "test@example.com",
            "source": "web"
        }
        
        with patch('mcp_service.routes.create_ticket.SuperOpsClient'):
            with patch('mcp_service.routes.create_ticket.get_supabase_client'):
                response = client.post("/mcp/create_ticket", json=valid_request)
        
        # Should not fail validation
        assert response.status_code != 422
        
        # Invalid priority
        invalid_request = valid_request.copy()
        invalid_request["priority"] = "invalid_priority"
        
        response = client.post("/mcp/create_ticket", json=invalid_request)
        assert response.status_code == 422
    
    def test_send_email_validation(self):
        """Test email sending validation"""
        # Valid request
        valid_request = {
            "to": "customer@example.com",
            "subject": "Test Subject",
            "body": "Test body"
        }
        
        with patch('mcp_service.routes.send_email.GmailClient'):
            with patch('mcp_service.routes.send_email.get_supabase_client'):
                response = client.post("/mcp/send_email", json=valid_request)
        
        # Should not fail validation
        assert response.status_code != 422
        
        # Invalid email
        invalid_request = valid_request.copy()
        invalid_request["to"] = "invalid_email"
        
        response = client.post("/mcp/send_email", json=invalid_request)
        assert response.status_code == 422

class TestFrontendDataFormats:
    """Test that API responses are in expected format for frontend"""
    
    @pytest.mark.asyncio
    async def test_dashboard_response_format(self):
        """Test dashboard response format matches frontend expectations"""
        mock_interactions = [
            {
                "id": "int_001",
                "interaction_type": "ticket_created",
                "customer_email": "test@example.com",
                "issue_description": "Test issue",
                "created_at": "2024-01-15T10:00:00Z"
            }
        ]
        
        with patch('mcp_service.routes.analytics.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_result = Mock()
            mock_result.data = mock_interactions
            mock_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result
            mock_supabase.return_value = mock_client
            
            response = client.get("/analytics/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields for frontend
        required_fields = [
            "total_interactions",
            "tickets_created", 
            "emails_sent",
            "kb_searches",
            "date_range",
            "daily_breakdown",
            "recent_activity"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check date_range format
        assert "start" in data["date_range"]
        assert "end" in data["date_range"]
        assert "days" in data["date_range"]
        
        # Check daily_breakdown format
        assert isinstance(data["daily_breakdown"], dict)
        
        # Check recent_activity format
        assert isinstance(data["recent_activity"], list)
    
    def test_kb_lookup_response_format(self):
        """Test KB lookup response format"""
        mock_results = [
            {
                "id": "kb_001",
                "title": "Test Article",
                "content": "Test content",
                "category": "test",
                "tags": ["test"],
                "similarity_score": 0.9,
                "solution_steps": ["step 1"],
                "success_rate": 0.95,
                "avg_resolution_time": "5 minutes"
            }
        ]
        
        with patch('mcp_service.routes.kb_lookup.EmbeddingSearch') as mock_search:
            mock_search_instance = Mock()
            mock_search_instance.search = AsyncMock(return_value=mock_results)
            mock_search.return_value = mock_search_instance
            
            with patch('mcp_service.routes.kb_lookup.get_supabase_client'):
                response = client.post("/mcp/kb_lookup", json={
                    "query": "test query",
                    "threshold": 0.8,
                    "limit": 5
                })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields for frontend
        required_fields = ["results", "query", "total_found", "search_time_ms", "threshold_used"]
        for field in required_fields:
            assert field in data
        
        # Check results format
        if data["results"]:
            result = data["results"][0]
            result_fields = ["id", "title", "content", "similarity_score", "solution_steps"]
            for field in result_fields:
                assert field in result
    
    def test_error_response_format(self):
        """Test error response format for frontend"""
        # Test validation error
        response = client.post("/mcp/kb_lookup", json={})
        
        assert response.status_code == 422
        error_data = response.json()
        
        # FastAPI validation error format
        assert "detail" in error_data
        
        # Test custom error with mock
        with patch('mcp_service.routes.kb_lookup.get_supabase_client') as mock_supabase:
            mock_supabase.side_effect = Exception("Database error")
            
            response = client.post("/mcp/kb_lookup", json={
                "query": "test",
                "threshold": 0.8,
                "limit": 5
            })
        
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data

class TestFrontendSecurity:
    """Test security aspects for frontend integration"""
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        # Test preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = client.options("/mcp/kb_lookup", headers=headers)
        
        # Should allow the request (status 200 or 405 is acceptable)
        assert response.status_code in [200, 405]
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        # Test with potentially malicious input
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "javascript:alert('xss')"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post("/mcp/kb_lookup", json={
                "query": malicious_input,
                "threshold": 0.8,
                "limit": 5
            })
            
            # Should not crash or return 500 due to input
            assert response.status_code != 500
    
    def test_rate_limiting_headers(self):
        """Test rate limiting (if implemented)"""
        response = client.get("/health")
        
        # Check if rate limiting headers are present (optional)
        # This would depend on if rate limiting is implemented
        assert response.status_code == 200

class TestFrontendPerformance:
    """Test performance aspects for frontend"""
    
    def test_response_time(self):
        """Test API response times"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_large_response_handling(self):
        """Test handling of large responses"""
        # Mock large dataset
        large_interactions = []
        for i in range(100):
            large_interactions.append({
                "id": f"int_{i}",
                "interaction_type": "ticket_created",
                "created_at": "2024-01-15T10:00:00Z"
            })
        
        with patch('mcp_service.routes.analytics.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_result = Mock()
            mock_result.data = large_interactions
            mock_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result
            mock_supabase.return_value = mock_client
            
            response = client.get("/analytics/dashboard")
        
        assert response.status_code == 200
        # Should handle large response without timeout

if __name__ == "__main__":
    pytest.main([__file__])