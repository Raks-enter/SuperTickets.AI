"""
Supabase Client
Handles database operations and vector search
"""

import os
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase client for database operations"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info("Supabase client initialized")
    
    def table(self, table_name: str):
        """Access table operations - delegates to underlying Supabase client"""
        return self.client.table(table_name)
    
    def rpc(self, function_name: str, params: Dict[str, Any] = None):
        """Call remote procedure - delegates to underlying Supabase client"""
        return self.client.rpc(function_name, params or {})
    
    async def insert_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert interaction record"""
        try:
            result = self.client.table("support_interactions").insert(interaction_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to insert interaction: {e}")
            raise
    
    async def get_interactions(
        self, 
        customer_email: Optional[str] = None,
        ticket_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get interaction history"""
        try:
            query = self.client.table("support_interactions").select("*")
            
            if customer_email:
                query = query.eq("customer_email", customer_email)
            
            if ticket_id:
                query = query.eq("ticket_id", ticket_id)
            
            result = query.order("created_at", desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get interactions: {e}")
            raise
    
    async def update_interaction(self, interaction_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update interaction record"""
        try:
            result = self.client.table("support_interactions")\
                .update(updates)\
                .eq("id", interaction_id)\
                .execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to update interaction: {e}")
            raise
    
    async def search_knowledge_base(
        self, 
        embedding: List[float], 
        threshold: float = 0.8, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using vector similarity"""
        try:
            # Use Supabase vector search with pgvector
            result = self.client.rpc(
                "match_knowledge_base",
                {
                    "query_embedding": embedding,
                    "match_threshold": threshold,
                    "match_count": limit
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            raise
    
    async def insert_knowledge_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert new knowledge base entry"""
        try:
            result = self.client.table("knowledge_base").insert(entry_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to insert knowledge entry: {e}")
            raise
    
    async def get_knowledge_entries(
        self, 
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get knowledge base entries"""
        try:
            query = self.client.table("knowledge_base").select("*")
            
            if category:
                query = query.eq("category", category)
            
            result = query.order("created_at", desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get knowledge entries: {e}")
            raise

# Global client instance
_supabase_client: Optional[SupabaseClient] = None

def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client instance"""
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    
    return _supabase_client

def create_supabase_tables():
    """Create required Supabase tables and functions"""
    sql_commands = [
        # Support interactions table
        """
        CREATE TABLE IF NOT EXISTS support_interactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            interaction_type VARCHAR(50) NOT NULL,
            customer_email VARCHAR(255),
            customer_phone VARCHAR(50),
            issue_description TEXT NOT NULL,
            ai_analysis JSONB,
            resolution_type VARCHAR(50),
            ticket_id VARCHAR(100),
            meeting_id VARCHAR(100),
            calendar_event_id VARCHAR(100),
            sentiment_analysis JSONB,
            metadata JSONB,
            tags TEXT[],
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """,
        
        # Knowledge base table
        """
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(500) NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR(1536),
            category VARCHAR(100),
            tags TEXT[],
            solution_steps TEXT[],
            success_rate DECIMAL(3,2) DEFAULT 0.0,
            avg_resolution_time VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """,
        
        # Vector similarity search function
        """
        CREATE OR REPLACE FUNCTION match_knowledge_base(
            query_embedding VECTOR(1536),
            match_threshold FLOAT,
            match_count INT
        )
        RETURNS TABLE(
            id UUID,
            title VARCHAR,
            content TEXT,
            category VARCHAR,
            tags TEXT[],
            solution_steps TEXT[],
            success_rate DECIMAL,
            avg_resolution_time VARCHAR,
            similarity_score FLOAT
        )
        LANGUAGE SQL STABLE
        AS $$
            SELECT
                kb.id,
                kb.title,
                kb.content,
                kb.category,
                kb.tags,
                kb.solution_steps,
                kb.success_rate,
                kb.avg_resolution_time,
                1 - (kb.embedding <=> query_embedding) AS similarity_score
            FROM knowledge_base kb
            WHERE 1 - (kb.embedding <=> query_embedding) > match_threshold
            ORDER BY similarity_score DESC
            LIMIT match_count;
        $$;
        """,
        
        # Indexes for performance
        """
        CREATE INDEX IF NOT EXISTS idx_support_interactions_customer_email 
        ON support_interactions(customer_email);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_support_interactions_ticket_id 
        ON support_interactions(ticket_id);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_support_interactions_created_at 
        ON support_interactions(created_at);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_knowledge_base_category 
        ON knowledge_base(category);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_knowledge_base_embedding 
        ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
        """
    ]
    
    return sql_commands