"""
Test Knowledge Base Lookup functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import json

from mcp_service.main import app
from mcp_service.routes.kb_lookup import KBLookupRequest, KBLookupResponse
from mcp_service.utils.embedding_search import EmbeddingSearch

client = TestClient(app)

class TestKBLookup:
    """Test cases for knowledge base lookup"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        mock_client = Mock()
        mock_client.search_knowledge_base = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def sample_kb_results(self):
        """Sample knowledge base search results"""
        return [
            {
                "id": "kb_001",
                "title": "Login Issues - Password Reset",
                "content": "If you're having trouble logging in, try these steps...",
                "category": "authentication",
                "tags": ["login", "password", "reset"],
                "similarity_score": 0.95,
                "solution_steps": [
                    "Navigate to login page",
                    "Click 'Forgot Password'",
                    "Enter registered email address"
                ],
                "success_rate": 0.95,
                "avg_resolution_time": "5 minutes"
            },
            {
                "id": "kb_002",
                "title": "Two-Factor Authentication Setup",
                "content": "To enable two-factor authentication...",
                "category": "authentication",
                "tags": ["2fa", "security", "authentication"],
                "similarity_score": 0.87,
                "solution_steps": [
                    "Access Account Settings",
                    "Navigate to Security section",
                    "Click 'Enable 2FA'"
                ],
                "success_rate": 0.88,
                "avg_resolution_time": "10 minutes"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_kb_lookup_success(self, mock_supabase_client, sample_kb_results):
        """Test successful knowledge base lookup"""
        # Mock the embedding search
        with patch('mcp_service.routes.kb_lookup.EmbeddingSearch') as mock_embedding_search:
            mock_search_instance = Mock()
            mock_search_instance.search = AsyncMock(return_value=sample_kb_results)
            mock_embedding_search.return_value = mock_search_instance
            
            # Mock the dependency
            with patch('mcp_service.routes.kb_lookup.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/kb_lookup", json={
                    "query": "login problems",
                    "threshold": 0.8,
                    "limit": 5
                })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "login problems"
        assert data["total_found"] == 2
        assert data["threshold_used"] == 0.8
        assert len(data["results"]) == 2
        
        # Check first result
        first_result = data["results"][0]
        assert first_result["id"] == "kb_001"
        assert first_result["title"] == "Login Issues - Password Reset"
        assert first_result["similarity_score"] == 0.95
        assert len(first_result["solution_steps"]) == 3
    
    @pytest.mark.asyncio
    async def test_kb_lookup_no_results(self, mock_supabase_client):
        """Test knowledge base lookup with no results"""
        with patch('mcp_service.routes.kb_lookup.EmbeddingSearch') as mock_embedding_search:
            mock_search_instance = Mock()
            mock_search_instance.search = AsyncMock(return_value=[])
            mock_embedding_search.return_value = mock_search_instance
            
            with patch('mcp_service.routes.kb_lookup.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/kb_lookup", json={
                    "query": "nonexistent issue",
                    "threshold": 0.9,
                    "limit": 5
                })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_found"] == 0
        assert len(data["results"]) == 0
    
    def test_kb_lookup_invalid_request(self):
        """Test knowledge base lookup with invalid request"""
        response = client.post("/mcp/kb_lookup", json={
            "threshold": 0.8,  # Missing required 'query' field
            "limit": 5
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_kb_lookup_invalid_threshold(self):
        """Test knowledge base lookup with invalid threshold"""
        response = client.post("/mcp/kb_lookup", json={
            "query": "test query",
            "threshold": 1.5,  # Invalid threshold > 1.0
            "limit": 5
        })
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_ai_analyze_success(self, mock_supabase_client):
        """Test AI analysis endpoint"""
        mock_analysis_result = {
            "issue_summary": "User cannot log into account",
            "urgency_level": "medium",
            "suggested_category": "authentication",
            "key_points": ["login failure", "password reset needed"],
            "complexity_level": "simple",
            "estimated_resolution_time": "5 minutes",
            "requires_escalation": False
        }
        
        with patch('mcp_service.routes.kb_lookup.BedrockClient') as mock_bedrock:
            mock_bedrock_instance = Mock()
            mock_bedrock_instance.analyze_issue = AsyncMock(return_value=mock_analysis_result)
            mock_bedrock.return_value = mock_bedrock_instance
            
            with patch('mcp_service.routes.kb_lookup.get_supabase_client', return_value=mock_supabase_client):
                response = client.post("/mcp/ai_analyze", json={
                    "issue_text": "I can't log into my account, forgot my password",
                    "context": "email",
                    "analysis_type": "issue_classification"
                })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["issue_summary"] == "User cannot log into account"
        assert data["urgency_level"] == "medium"
        assert data["suggested_category"] == "authentication"
    
    def test_ai_analyze_missing_text(self):
        """Test AI analysis with missing issue text"""
        response = client.post("/mcp/ai_analyze", json={
            "context": "email"
        })
        
        assert response.status_code == 400
        assert "issue_text is required" in response.json()["detail"]

class TestEmbeddingSearch:
    """Test cases for embedding search functionality"""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 1536  # Mock embedding vector
        mock_client.embeddings.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        mock_client = Mock()
        mock_client.search_knowledge_base = AsyncMock()
        return mock_client
    
    @pytest.mark.asyncio
    async def test_create_embedding(self, mock_supabase_client, mock_openai_client):
        """Test embedding creation"""
        with patch('mcp_service.utils.embedding_search.openai.OpenAI', return_value=mock_openai_client):
            embedding_search = EmbeddingSearch(mock_supabase_client)
            
            embedding = await embedding_search.create_embedding("test text")
            
            assert len(embedding) == 1536
            assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_search_with_category_filter(self, mock_supabase_client, mock_openai_client):
        """Test search with category filter"""
        mock_results = [
            {"id": "1", "category": "authentication", "similarity_score": 0.9},
            {"id": "2", "category": "billing", "similarity_score": 0.8}
        ]
        
        mock_supabase_client.search_knowledge_base = AsyncMock(return_value=mock_results)
        
        with patch('mcp_service.utils.embedding_search.openai.OpenAI', return_value=mock_openai_client):
            embedding_search = EmbeddingSearch(mock_supabase_client)
            
            results = await embedding_search.search(
                query="test query",
                category_filter="authentication"
            )
            
            # Should only return authentication category results
            assert len(results) == 1
            assert results[0]["category"] == "authentication"
    
    @pytest.mark.asyncio
    async def test_add_knowledge_entry(self, mock_supabase_client, mock_openai_client):
        """Test adding knowledge entry"""
        mock_supabase_client.insert_knowledge_entry = AsyncMock(return_value={"id": "new_entry"})
        
        with patch('mcp_service.utils.embedding_search.openai.OpenAI', return_value=mock_openai_client):
            embedding_search = EmbeddingSearch(mock_supabase_client)
            
            result = await embedding_search.add_knowledge_entry(
                title="Test Entry",
                content="Test content",
                category="test",
                tags=["test", "example"],
                solution_steps=["step 1", "step 2"],
                success_rate=0.9
            )
            
            assert result["id"] == "new_entry"
            mock_supabase_client.insert_knowledge_entry.assert_called_once()
    
    def test_cosine_similarity(self, mock_supabase_client):
        """Test cosine similarity calculation"""
        embedding_search = EmbeddingSearch(mock_supabase_client)
        
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]
        
        # Identical vectors should have similarity 1.0
        similarity_identical = embedding_search.cosine_similarity(vec1, vec2)
        assert abs(similarity_identical - 1.0) < 0.001
        
        # Orthogonal vectors should have similarity 0.0
        similarity_orthogonal = embedding_search.cosine_similarity(vec1, vec3)
        assert abs(similarity_orthogonal - 0.0) < 0.001

if __name__ == "__main__":
    pytest.main([__file__])