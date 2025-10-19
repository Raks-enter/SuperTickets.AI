"""
Analytics Route
Provides dashboard statistics and metrics from the database
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/analytics/dashboard")
async def get_dashboard_stats(
    days: int = 30,
    supabase=Depends(get_supabase_client)
):
    """
    Get dashboard statistics for the specified number of days
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all interactions in date range
        interactions_result = supabase.table("support_interactions")\
            .select("*")\
            .gte("created_at", start_date.isoformat())\
            .lte("created_at", end_date.isoformat())\
            .execute()
        
        interactions = interactions_result.data if interactions_result.data else []
        
        # Calculate statistics
        stats = {
            "total_interactions": len(interactions),
            "tickets_created": len([i for i in interactions if i.get("interaction_type") == "ticket_created"]),
            "emails_sent": len([i for i in interactions if i.get("interaction_type") == "email_sent"]),
            "kb_searches": len([i for i in interactions if i.get("interaction_type") == "kb_search"]),
            "callbacks_scheduled": len([i for i in interactions if i.get("interaction_type") == "callback_scheduled"]),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }
        
        # Daily breakdown
        daily_stats = {}
        for i in range(days):
            date = (start_date + timedelta(days=i)).date()
            date_str = date.isoformat()
            daily_stats[date_str] = {
                "tickets": 0,
                "emails": 0,
                "kb_searches": 0
            }
        
        for interaction in interactions:
            interaction_date = datetime.fromisoformat(interaction["created_at"]).date().isoformat()
            if interaction_date in daily_stats:
                if interaction.get("interaction_type") == "ticket_created":
                    daily_stats[interaction_date]["tickets"] += 1
                elif interaction.get("interaction_type") == "email_sent":
                    daily_stats[interaction_date]["emails"] += 1
                elif interaction.get("interaction_type") == "kb_search":
                    daily_stats[interaction_date]["kb_searches"] += 1
        
        stats["daily_breakdown"] = daily_stats
        
        # Recent activity (last 10 interactions)
        recent_interactions = sorted(interactions, key=lambda x: x["created_at"], reverse=True)[:10]
        stats["recent_activity"] = recent_interactions
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )

@router.get("/analytics/tickets")
async def get_ticket_analytics(
    days: int = 30,
    supabase=Depends(get_supabase_client)
):
    """
    Get detailed ticket analytics
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get ticket interactions
        tickets_result = supabase.table("support_interactions")\
            .select("*")\
            .eq("interaction_type", "ticket_created")\
            .gte("created_at", start_date.isoformat())\
            .lte("created_at", end_date.isoformat())\
            .execute()
        
        tickets = tickets_result.data if tickets_result.data else []
        
        # Analyze by priority
        priority_stats = {}
        category_stats = {}
        source_stats = {}
        
        for ticket in tickets:
            # Priority breakdown
            priority = ticket.get("priority", "unknown")
            priority_stats[priority] = priority_stats.get(priority, 0) + 1
            
            # Category breakdown
            category = ticket.get("category", "unknown")
            category_stats[category] = category_stats.get(category, 0) + 1
            
            # Source breakdown
            source = ticket.get("source", "unknown")
            source_stats[source] = source_stats.get(source, 0) + 1
        
        return {
            "total_tickets": len(tickets),
            "priority_breakdown": priority_stats,
            "category_breakdown": category_stats,
            "source_breakdown": source_stats,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get ticket analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve ticket analytics: {str(e)}"
        )