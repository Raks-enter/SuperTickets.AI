"""
Knowledge Base Lookup Route
Handles vector similarity search in Supabase knowledge base
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import time
import uuid
from datetime import datetime

from ..utils.supabase_client import get_supabase_client
from ..utils.embedding_search import EmbeddingSearch

logger = logging.getLogger(__name__)
router = APIRouter()

class KBLookupRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    threshold: float = Field(0.8, ge=0.0, le=1.0, description="Minimum similarity threshold")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of results")
    context: Optional[str] = Field(None, description="Context for the search (email, call, etc.)")
    category_filter: Optional[str] = Field(None, description="Filter by category")

class KBResult(BaseModel):
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    similarity_score: float
    solution_steps: List[str]
    success_rate: float
    avg_resolution_time: str

class KBLookupResponse(BaseModel):
    results: List[KBResult]
    query: str
    total_found: int
    search_time_ms: int
    threshold_used: float

@router.post("/kb_lookup", response_model=KBLookupResponse)
async def lookup_knowledge_base(
    request: KBLookupRequest,
    supabase=Depends(get_supabase_client)
):
    """
    Search knowledge base using vector similarity
    
    This endpoint performs semantic search on the knowledge base using
    vector embeddings to find the most relevant solutions.
    """
    start_time = time.time()
    
    try:
        logger.info(f"KB lookup request: query='{request.query}', threshold={request.threshold}")
        
        # Initialize embedding search
        embedding_search = EmbeddingSearch(supabase)
        
        # Perform vector search
        search_results = await embedding_search.search(
            query=request.query,
            threshold=request.threshold,
            limit=request.limit,
            category_filter=request.category_filter
        )
        
        # Format results
        kb_results = []
        for result in search_results:
            kb_result = KBResult(
                id=result.get("id", ""),
                title=result.get("title", ""),
                content=result.get("content", ""),
                category=result.get("category", ""),
                tags=result.get("tags", []),
                similarity_score=result.get("similarity_score", 0.0),
                solution_steps=result.get("solution_steps", []),
                success_rate=result.get("success_rate", 0.0),
                avg_resolution_time=result.get("avg_resolution_time", "Unknown")
            )
            kb_results.append(kb_result)
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        response = KBLookupResponse(
            results=kb_results,
            query=request.query,
            total_found=len(kb_results),
            search_time_ms=search_time_ms,
            threshold_used=request.threshold
        )
        
        # Log the KB search for analytics
        await log_kb_search(
            supabase=supabase,
            query=request.query,
            results_count=len(kb_results),
            search_time_ms=search_time_ms,
            context=request.context
        )
        
        logger.info(f"KB lookup completed: {len(kb_results)} results in {search_time_ms}ms")
        return response
        
    except Exception as e:
        logger.error(f"KB lookup failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge base search failed: {str(e)}"
        )

@router.post("/ai_analyze")
async def ai_analyze_issue(
    request: Dict[str, Any],
    supabase=Depends(get_supabase_client)
):
    """
    Analyze issue text using AWS Bedrock AI
    
    This endpoint uses AWS Bedrock to analyze customer issues and
    extract key information for triage.
    """
    try:
        from ..utils.bedrock_client import BedrockClient
        
        issue_text = request.get("issue_text", "")
        context = request.get("context", "")
        analysis_type = request.get("analysis_type", "issue_classification")
        
        if not issue_text:
            raise HTTPException(status_code=400, detail="issue_text is required")
        
        logger.info(f"AI analysis request: type={analysis_type}, text_length={len(issue_text)}")
        
        bedrock_client = BedrockClient()
        analysis_result = await bedrock_client.analyze_issue(
            issue_text=issue_text,
            context=context,
            analysis_type=analysis_type
        )
        
        logger.info("AI analysis completed successfully")
        return analysis_result
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}"
        )

@router.post("/extract_call_info")
async def extract_call_information(
    request: Dict[str, Any],
    supabase=Depends(get_supabase_client)
):
    """
    Extract structured information from call transcript
    
    Uses AI to parse call transcripts and extract customer details,
    issue descriptions, and other relevant information.
    """
    try:
        from ..utils.bedrock_client import BedrockClient
        
        transcript = request.get("transcript", "")
        caller_phone = request.get("caller_phone", "")
        
        if not transcript:
            raise HTTPException(status_code=400, detail="transcript is required")
        
        logger.info(f"Call info extraction: transcript_length={len(transcript)}")
        
        bedrock_client = BedrockClient()
        extracted_info = await bedrock_client.extract_call_info(
            transcript=transcript,
            caller_phone=caller_phone
        )
        
        logger.info("Call info extraction completed")
        return extracted_info
        
    except Exception as e:
        logger.error(f"Call info extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Call info extraction failed: {str(e)}"
        )

@router.post("/analyze_call_sentiment")
async def analyze_call_sentiment(
    request: Dict[str, Any],
    supabase=Depends(get_supabase_client)
):
    """
    Analyze sentiment and urgency from call transcript
    
    Performs sentiment analysis on call transcripts to determine
    customer frustration levels and issue urgency.
    """
    try:
        from ..utils.bedrock_client import BedrockClient
        
        transcript = request.get("transcript", "")
        conversation_segments = request.get("conversation_segments", [])
        
        if not transcript:
            raise HTTPException(status_code=400, detail="transcript is required")
        
        logger.info(f"Sentiment analysis: transcript_length={len(transcript)}")
        
        bedrock_client = BedrockClient()
        sentiment_result = await bedrock_client.analyze_sentiment(
            transcript=transcript,
            conversation_segments=conversation_segments
        )
        
        logger.info("Sentiment analysis completed")
        return sentiment_result
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Sentiment analysis failed: {str(e)}"
        )

async def log_kb_search(supabase, query: str, results_count: int, search_time_ms: int, context: str = None):
    """Log KB search to Supabase for analytics"""
    try:
        log_data = {
            "id": str(uuid.uuid4()),
            "interaction_type": "kb_search",
            "query": query,
            "results_count": results_count,
            "search_time_ms": search_time_ms,
            "context": context,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("support_interactions").insert(log_data).execute()
        logger.info(f"KB search logged: query='{query}', results={results_count}")
        
    except Exception as e:
        logger.error(f"Failed to log KB search: {e}")