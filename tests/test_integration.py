"""
Integration Tests for SuperTickets.AI
Tests complete workflows end-to-end
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import json
from datetime import datetime, timedelta

from mcp_service.main import app

client = TestClient(app)

class TestEmailToTicketWorkflow:
    """Test complete email processing to ticket creation workflow"""
    
    @pytest.mark.asyncio
    async def test_email_auto_resolution_workflow(self, mock_supabase_client):
        """Test complete workflow: email -> AI analysis -> KB search -> auto resolution"""
        
        # Mock AI analysis result
        ai_analysis = {
            "issue_summary": "Customer cannot log into account due to forgotten password",
            "urgency_level": "medium",
            "suggested_category": "authentication",
            "key_points": ["login failure", "password forgotten"],
            "complexity_level": "simple",
            "estimated_resolution_time": "5 minutes",
            "requires_escalation": False
        }
        
        # Mock KB search results
        kb_results = [{
            "id": "kb_001",
            "title": "Password Reset Instructions",
            "content": "To reset your password: 1. Go to login page...",
            "category": "authentication",
            "tags": ["password", "reset"],
            "similarity_score": 0.92,
            "solution_steps": ["Navigate to login page", "Click 'Forgot Password'"],
            "success_rate": 0.95,
            "avg_resolution_time": "5 minutes"
        }]
        
        # Step 1: AI Analysis
        with patch('mcp_service.routes.kb_lookup.BedrockClient') as mock_bedrock:
            mock_bedrock_instance = Mock()
            mock_bedrock_instance.analyze_issue = AsyncMock(return_value=ai_analysis)
            mock_bedrock.return_value = mock_bedrock_instance
            
            with patch('mcp_service.routes.kb_lookup.get_supabase_client', return_value=mock_supabase_client):
                ai_response = client.post("/mcp/ai_analyze", json={
                    "issue_text": "I can't log into my account, I think I forgot my password",
                    "context": "email"
                })
        
        assert ai_response.status_code == 200
        
        # Step 2: Knowledge Base Search
        with patch('mcp_service.routes.kb_lookup.EmbeddingSearch') as mock_embedding:
            mock_search_instance = Mock()
            mock_search_instance.search = AsyncMock(return_value=kb_results)
            mock_embedding.return_value = mock_search_instance
            
            with patch('mcp_service.routes.kb_lookup.get_supabase_client', return_value=mock_supabase_client):
                kb_response = client.post("/mcp/kb_lookup", json={
                    "query": "login password reset",
                    "threshold": 0.8
                })
        
        assert kb_response.status_code == 200
        kb_data = kb_response.json()
        assert kb_data["total_found"] == 1
        
        # Step 3: Send Solution Email
        gmail_response = {"message_id": "msg_123", "thread_id": "thread_123", "status": "sent"}
        
        with patch('mcp_service.routes.send_email.GmailClient') as mock_gmail:
            mock_gmail_instance = Mock()
            mock_gmail_instance.send_email = AsyncMock(return_value=gmail_response)
            mock_gmail.return_value = mock_gmail_instance
            
            with patch('mcp_service.routes.send_email.get_supabase_client', return_value=mock_supabase_client):
                email_response = client.post("/mcp/send_email", json={
                    "to": "customer@example.com",
                    "subject": "Re: Login Issue - Solution Provided",
                    "body": kb_results[0]["content"],
                    "template": "solution_response"
                })
        
        assert email_response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__])