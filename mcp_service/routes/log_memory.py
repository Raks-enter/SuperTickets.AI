"""
Memory Logging Route
Handles logging interactions to Supabase memory store
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
try:
    from pydantic import EmailStr
except ImportError:
    from email_validator import EmailStr
from typing import Optional, Dict, Any, List
import logging
import uuid
from datetime import datetime

from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

class LogMemoryRequest(BaseModel):
    interaction_type: str = Field(..., description="Type of interaction")
    customer_email: Optional[EmailStr] = Field(None, description="Customer email")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    issue_description: str = Field(..., description="Description of the issue")
    ai_analysis: Optional[Dict[str, Any]] = Field(None, description="AI analysis results")
    resolution_type: Optional[str] = Field(None, description="How the issue was resolved")
    ticket_id: Optional[str] = Field(None, description="Associated ticket ID")
    sentiment_analysis: Optional[Dict[str, Any]] = Field(None, description="Sentiment analysis results")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")

class LogMemoryResponse(BaseModel):
    log_id: str
    status: str
    logged_at: datetime

@router.post("/log_memory", response_model=LogMemoryResponse)
async def log_interaction_memory(
    request: LogMemoryRequest,
    supabase=Depends(get_supabase_client)
):
    """
    Log interaction to Supabase memory store
    
    This endpoint stores interaction data for future reference,
    analytics, and learning purposes.
    """
    try:
        log_id = str(uuid.uuid4())
        
        logger.info(f"Logging interaction: type={request.interaction_type}, id={log_id}")
        
        # Prepare log data
        log_data = {
            "id": log_id,
            "interaction_type": request.interaction_type,
            "customer_email": request.customer_email,
            "customer_phone": request.customer_phone,
            "issue_description": request.issue_description,
            "ai_analysis": request.ai_analysis,
            "resolution_type": request.resolution_type,
            "ticket_id": request.ticket_id,
            "sentiment_analysis": request.sentiment_analysis,
            "metadata": request.metadata,
            "tags": request.tags,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert into Supabase
        result = supabase.table("support_interactions").insert(log_data).execute()
        
        if not result.data:
            raise Exception("Failed to insert log data")
        
        response = LogMemoryResponse(
            log_id=log_id,
            status="logged",
            logged_at=datetime.utcnow()
        )
        
        logger.info(f"Interaction logged successfully: {log_id}")
        return response
        
    except Exception as e:
        logger.error(f"Memory logging failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log interaction: {str(e)}"
        )

@router.get("/memory_search")
async def search_interaction_memory(
    customer_email: Optional[str] = None,
    customer_phone: Optional[str] = None,
    interaction_type: Optional[str] = None,
    ticket_id: Optional[str] = None,
    days_back: int = 30,
    limit: int = 50,
    supabase=Depends(get_supabase_client)
):
    """
    Search interaction memory for historical data
    
    Retrieves past interactions based on search criteria
    for context and pattern analysis.
    """
    try:
        logger.info(f"Searching memory: email={customer_email}, type={interaction_type}")
        
        # Build query
        query = supabase.table("support_interactions").select("*")
        
        # Apply filters
        if customer_email:
            query = query.eq("customer_email", customer_email)
        
        if customer_phone:
            query = query.eq("customer_phone", customer_phone)
        
        if interaction_type:
            query = query.eq("interaction_type", interaction_type)
        
        if ticket_id:
            query = query.eq("ticket_id", ticket_id)
        
        # Date filter
        from datetime import timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        query = query.gte("created_at", cutoff_date)
        
        # Order and limit
        query = query.order("created_at", desc=True).limit(limit)
        
        # Execute query
        result = query.execute()
        
        interactions = result.data if result.data else []
        
        logger.info(f"Memory search completed: {len(interactions)} results")
        
        return {
            "interactions": interactions,
            "total_found": len(interactions),
            "search_criteria": {
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "interaction_type": interaction_type,
                "ticket_id": ticket_id,
                "days_back": days_back
            }
        }
        
    except Exception as e:
        logger.error(f"Memory search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Memory search failed: {str(e)}"
        )

@router.get("/memory_analytics")
async def get_memory_analytics(
    days_back: int = 30,
    supabase=Depends(get_supabase_client)
):
    """
    Get analytics from interaction memory
    
    Provides insights and statistics about support interactions
    for performance monitoring and improvement.
    """
    try:
        logger.info(f"Generating memory analytics for last {days_back} days")
        
        # Date filter
        from datetime import timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        # Get all interactions in date range
        result = supabase.table("support_interactions")\
            .select("*")\
            .gte("created_at", cutoff_date)\
            .execute()
        
        interactions = result.data if result.data else []
        
        # Calculate analytics
        analytics = calculate_interaction_analytics(interactions)
        
        logger.info("Memory analytics generated successfully")
        return analytics
        
    except Exception as e:
        logger.error(f"Memory analytics failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Memory analytics failed: {str(e)}"
        )

@router.post("/update_interaction")
async def update_interaction_memory(
    interaction_id: str,
    updates: Dict[str, Any],
    supabase=Depends(get_supabase_client)
):
    """
    Update existing interaction record
    
    Allows updating interaction records with additional information
    such as resolution outcomes or follow-up data.
    """
    try:
        logger.info(f"Updating interaction: {interaction_id}")
        
        # Add update timestamp
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        # Update record
        result = supabase.table("support_interactions")\
            .update(updates)\
            .eq("id", interaction_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Interaction not found")
        
        logger.info(f"Interaction updated successfully: {interaction_id}")
        return {
            "interaction_id": interaction_id,
            "status": "updated",
            "updated_at": updates["updated_at"]
        }
        
    except Exception as e:
        logger.error(f"Interaction update failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update interaction: {str(e)}"
        )

def calculate_interaction_analytics(interactions: List[Dict]) -> Dict[str, Any]:
    """Calculate analytics from interaction data"""
    try:
        total_interactions = len(interactions)
        
        if total_interactions == 0:
            return {
                "total_interactions": 0,
                "interaction_types": {},
                "resolution_types": {},
                "avg_sentiment_score": None,
                "ticket_creation_rate": 0,
                "auto_resolution_rate": 0
            }
        
        # Count interaction types
        interaction_types = {}
        resolution_types = {}
        sentiment_scores = []
        tickets_created = 0
        auto_resolved = 0
        
        for interaction in interactions:
            # Interaction types
            int_type = interaction.get("interaction_type", "unknown")
            interaction_types[int_type] = interaction_types.get(int_type, 0) + 1
            
            # Resolution types
            res_type = interaction.get("resolution_type")
            if res_type:
                resolution_types[res_type] = resolution_types.get(res_type, 0) + 1
            
            # Sentiment analysis
            sentiment = interaction.get("sentiment_analysis")
            if sentiment and isinstance(sentiment, dict):
                score = sentiment.get("score")
                if score is not None:
                    sentiment_scores.append(float(score))
            
            # Count tickets and auto-resolutions
            if interaction.get("ticket_id"):
                tickets_created += 1
            
            if res_type in ["knowledge_base_match", "auto_resolved"]:
                auto_resolved += 1
        
        # Calculate rates
        ticket_creation_rate = (tickets_created / total_interactions) * 100
        auto_resolution_rate = (auto_resolved / total_interactions) * 100
        
        # Average sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else None
        
        return {
            "total_interactions": total_interactions,
            "interaction_types": interaction_types,
            "resolution_types": resolution_types,
            "avg_sentiment_score": avg_sentiment,
            "ticket_creation_rate": round(ticket_creation_rate, 2),
            "auto_resolution_rate": round(auto_resolution_rate, 2),
            "sentiment_data": {
                "total_scored": len(sentiment_scores),
                "avg_score": round(avg_sentiment, 3) if avg_sentiment else None,
                "min_score": min(sentiment_scores) if sentiment_scores else None,
                "max_score": max(sentiment_scores) if sentiment_scores else None
            }
        }
        
    except Exception as e:
        logger.error(f"Analytics calculation failed: {e}")
        return {"error": "Failed to calculate analytics"}