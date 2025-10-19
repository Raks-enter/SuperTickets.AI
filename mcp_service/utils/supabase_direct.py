"""
Direct Supabase Client Access
Alternative approach that returns the raw Supabase client
"""

import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def get_supabase_direct() -> Client:
    """Get direct Supabase client without wrapper"""
    
    # Ensure environment variables are loaded
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
    
    client = create_client(url, key)
    logger.info("Direct Supabase client created")
    
    return client

# Global client instance
_direct_client = None

def get_supabase_client_direct():
    """Get or create direct Supabase client instance"""
    global _direct_client
    
    if _direct_client is None:
        _direct_client = get_supabase_direct()
    
    return _direct_client