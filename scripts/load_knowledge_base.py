#!/usr/bin/env python3
"""
Script to load knowledge base data into Supabase
"""

import json
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
env_path = project_root / ".env"
load_dotenv(env_path)

from mcp_service.utils.supabase_client import get_supabase_client
from mcp_service.utils.embedding_search import EmbeddingSearch

async def load_knowledge_base():
    """Load knowledge base from JSON file into Supabase"""
    
    # Load knowledge base JSON
    kb_file = project_root / ".kiro" / "kb" / "knowledge.json"
    
    if not kb_file.exists():
        print(f"❌ Knowledge base file not found: {kb_file}")
        return
    
    with open(kb_file, 'r') as f:
        data = json.load(f)
    
    knowledge_entries = data.get("knowledge_base", {}).get("entries", [])
    
    if not knowledge_entries:
        print("❌ No knowledge entries found in JSON file")
        return
    
    print(f"📚 Loading {len(knowledge_entries)} knowledge base entries...")
    
    # Initialize clients
    supabase = get_supabase_client()
    embedding_search = EmbeddingSearch(supabase)
    
    loaded_count = 0
    
    for entry in knowledge_entries:
        try:
            await embedding_search.add_knowledge_entry(
                title=entry["title"],
                content=entry["content"],
                category=entry["category"],
                tags=entry.get("tags", []),
                solution_steps=entry.get("solution_steps", []),
                success_rate=entry.get("success_rate", 0.0),
                avg_resolution_time=entry.get("avg_resolution_time", "Unknown")
            )
            loaded_count += 1
            print(f"✅ Loaded: {entry['title']}")
            
        except Exception as e:
            print(f"❌ Failed to load {entry['title']}: {e}")
    
    print(f"\n🎉 Successfully loaded {loaded_count}/{len(knowledge_entries)} entries!")

if __name__ == "__main__":
    # Check environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        sys.exit(1)
    
    print("🚀 Starting knowledge base loading...")
    asyncio.run(load_knowledge_base())