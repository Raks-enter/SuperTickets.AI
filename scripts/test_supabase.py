#!/usr/bin/env python3
"""
Test Supabase connection and setup
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
env_path = project_root / ".env"
load_dotenv(env_path)

from mcp_service.utils.supabase_client import get_supabase_client

def test_supabase_connection():
    """Test Supabase connection and table setup"""
    
    print("🔍 Testing Supabase connection...")
    
    try:
        # Test connection
        supabase = get_supabase_client()
        print("✅ Supabase client initialized successfully")
        
        # Test support_interactions table
        result = supabase.client.table("support_interactions").select("*").limit(1).execute()
        print("✅ support_interactions table accessible")
        
        # Test knowledge_base table  
        result = supabase.client.table("knowledge_base").select("*").limit(1).execute()
        print("✅ knowledge_base table accessible")
        
        # Test vector function
        try:
            # This will fail if the function doesn't exist, but that's expected initially
            result = supabase.client.rpc("match_knowledge_base", {
                "query_embedding": [0.0] * 1536,
                "match_threshold": 0.8,
                "match_count": 1
            }).execute()
            print("✅ match_knowledge_base function working")
        except Exception as e:
            print(f"⚠️  Vector search function needs setup: {e}")
        
        print("\n🎉 Supabase setup looks good!")
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your SUPABASE_URL and SUPABASE_KEY in .env")
        print("2. Make sure you've created the required tables")
        print("3. Enable the pgvector extension in Supabase")

if __name__ == "__main__":
    print("🔍 Loading environment variables...")
    
    # Check if .env file exists
    env_file = project_root / ".env"
    if not env_file.exists():
        print(f"❌ .env file not found at: {env_file}")
        print("Please copy .env.example to .env and fill in your credentials")
        sys.exit(1)
    
    print(f"✅ Found .env file at: {env_file}")
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        print(f"SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
        print(f"SUPABASE_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")
        print("Please check your .env file")
        sys.exit(1)
    
    print(f"✅ SUPABASE_URL: {supabase_url[:50]}...")
    print(f"✅ SUPABASE_KEY: {supabase_key[:20]}...")
    
    test_supabase_connection()