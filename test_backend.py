#!/usr/bin/env python3
"""
Quick test to see if the backend can start
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing backend imports...")
    
    # Test basic imports
    from mcp_service.main import app
    print("✅ Main app imported successfully")
    
    # Test if we can create the app
    print("✅ FastAPI app created successfully")
    
    # Test environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        print("✅ Supabase credentials found")
    else:
        print("⚠️  Supabase credentials not found (this is OK for testing)")
    
    print("\n🎉 Backend should work! The issue might be with Docker or networking.")
    print("\nTry these steps:")
    print("1. Stop all containers: docker-compose down")
    print("2. Rebuild: docker-compose build --no-cache")
    print("3. Start again: docker-compose up -d")
    print("4. Check logs: docker-compose logs supertickets-ai")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMissing dependencies. Try:")
    print("pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nCheck your .env file and dependencies")