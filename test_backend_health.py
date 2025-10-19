#!/usr/bin/env python3
"""
Quick backend health test
"""

import requests
import time

def test_backend_health():
    """Test if backend is responding"""
    print("🔧 Testing Backend Health...")
    
    # Wait a bit more for the backend to fully start
    print("⏳ Waiting 15 seconds for backend to fully start...")
    time.sleep(15)
    
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy!")
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            return True
        else:
            print(f"❌ Backend returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_basic_endpoints():
    """Test basic API endpoints"""
    print("\n🧪 Testing Basic API Endpoints...")
    
    endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/analytics/dashboard", "Dashboard analytics"),
        ("POST", "/mcp/kb-lookup", "Knowledge base lookup", {"query": "test", "threshold": 0.8, "limit": 5})
    ]
    
    for method, endpoint, description, *data in endpoints:
        try:
            url = f"http://localhost:8000{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                json_data = data[0] if data else {}
                response = requests.post(url, json=json_data, timeout=5)
            
            if response.status_code in [200, 422]:  # 422 is OK for some endpoints
                print(f"✅ {description}: {response.status_code}")
            else:
                print(f"⚠️  {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: {e}")

if __name__ == "__main__":
    print("🚀 SuperTickets.AI Backend Health Check")
    print("=" * 50)
    
    if test_backend_health():
        test_basic_endpoints()
        print("\n🎉 Backend is working! You can now:")
        print("   🌐 Open frontend: http://localhost:3000")
        print("   📚 View API docs: http://localhost:8000/docs")
    else:
        print("\n❌ Backend is not responding. Check logs with:")
        print("   docker-compose logs supertickets-ai")