"""
Embedding Search Utility
Handles vector embeddings and similarity search
"""

import os
import logging
from typing import List, Dict, Any, Optional
import openai
import json

logger = logging.getLogger(__name__)

class EmbeddingSearch:
    """Handles vector embeddings and similarity search"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.embedding_model = "text-embedding-ada-002"
        logger.info("Embedding search initialized")
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            raise
    
    async def search(
        self, 
        query: str, 
        threshold: float = 0.8, 
        limit: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using vector similarity"""
        try:
            # Create embedding for query
            query_embedding = await self.create_embedding(query)
            
            # Search using Supabase vector function
            results = await self.supabase.search_knowledge_base(
                embedding=query_embedding,
                threshold=threshold,
                limit=limit
            )
            
            # Filter by category if specified
            if category_filter:
                results = [r for r in results if r.get("category") == category_filter]
            
            # Sort by similarity score
            results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            
            logger.info(f"Vector search completed: {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise
    
    async def add_knowledge_entry(
        self, 
        title: str, 
        content: str, 
        category: str,
        tags: List[str] = None,
        solution_steps: List[str] = None,
        success_rate: float = 0.0,
        avg_resolution_time: str = "Unknown"
    ) -> Dict[str, Any]:
        """Add new entry to knowledge base with embedding"""
        try:
            # Create embedding for the content
            combined_text = f"{title} {content}"
            embedding = await self.create_embedding(combined_text)
            
            # Prepare entry data
            entry_data = {
                "title": title,
                "content": content,
                "embedding": embedding,
                "category": category,
                "tags": tags or [],
                "solution_steps": solution_steps or [],
                "success_rate": success_rate,
                "avg_resolution_time": avg_resolution_time
            }
            
            # Insert into database
            result = await self.supabase.insert_knowledge_entry(entry_data)
            
            logger.info(f"Knowledge entry added: {title}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to add knowledge entry: {e}")
            raise
    
    async def update_knowledge_embeddings(self):
        """Update embeddings for existing knowledge base entries"""
        try:
            # Get all entries without embeddings
            entries = await self.supabase.get_knowledge_entries()
            
            updated_count = 0
            for entry in entries:
                if not entry.get("embedding"):
                    # Create embedding
                    combined_text = f"{entry['title']} {entry['content']}"
                    embedding = await self.create_embedding(combined_text)
                    
                    # Update entry
                    await self.supabase.update_interaction(
                        entry["id"], 
                        {"embedding": embedding}
                    )
                    updated_count += 1
            
            logger.info(f"Updated embeddings for {updated_count} entries")
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to update embeddings: {e}")
            raise
    
    async def search_similar_issues(
        self, 
        issue_description: str, 
        customer_email: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar past issues from the same customer"""
        try:
            # Create embedding for issue
            issue_embedding = await self.create_embedding(issue_description)
            
            # Get customer's past interactions
            past_interactions = await self.supabase.get_interactions(
                customer_email=customer_email,
                limit=50
            )
            
            # Calculate similarity with past issues
            similar_issues = []
            for interaction in past_interactions:
                if interaction.get("issue_description"):
                    # Create embedding for past issue
                    past_embedding = await self.create_embedding(
                        interaction["issue_description"]
                    )
                    
                    # Calculate cosine similarity
                    similarity = self.cosine_similarity(issue_embedding, past_embedding)
                    
                    if similarity > 0.7:  # Threshold for similar issues
                        interaction["similarity_score"] = similarity
                        similar_issues.append(interaction)
            
            # Sort by similarity and return top results
            similar_issues.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar_issues[:limit]
            
        except Exception as e:
            logger.error(f"Similar issues search failed: {e}")
            return []
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"Cosine similarity calculation failed: {e}")
            return 0.0
    
    async def load_knowledge_from_json(self, json_file_path: str):
        """Load knowledge base entries from JSON file"""
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            knowledge_entries = data.get("knowledge_base", {}).get("entries", [])
            
            loaded_count = 0
            for entry in knowledge_entries:
                await self.add_knowledge_entry(
                    title=entry["title"],
                    content=entry["content"],
                    category=entry["category"],
                    tags=entry.get("tags", []),
                    solution_steps=entry.get("solution_steps", []),
                    success_rate=entry.get("success_rate", 0.0),
                    avg_resolution_time=entry.get("avg_resolution_time", "Unknown")
                )
                loaded_count += 1
            
            logger.info(f"Loaded {loaded_count} knowledge entries from JSON")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Failed to load knowledge from JSON: {e}")
            raise