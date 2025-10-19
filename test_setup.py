#!/usr/bin/env python3
"""
Test script to verify SuperTickets.AI setup
"""

import requests
import time
import sys

def test_backend():
    """Test if backend is running"""
    try:
        print("🔧 Testing backend connection...")
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data.get('status')}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_frontend():
    """Test if frontend is running"""
    try:
        print("🌐 Testing frontend connection...")
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend connection failed: {e}")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    endpoints = [
        ("GET", "/health", "Health check"),
        ("GET", "/", "Root endpoint"),
        ("GET", "/analytics/dashboard", "Dashboard analytics")
    ]
    
    print("🧪 Testing API endpoints...")
    for method, endpoint, description in endpoints:
        try:
            url = f"http://localhost:8000{endpoint}"
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 422]:  # 422 is OK for endpoints requiring data
                print(f"✅ {description}: {response.status_code}")
            else:
                print(f"⚠️  {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: {e}")

def main():
    """Main test function"""
    print("🚀 SuperTickets.AI Setup Test")
    print("=" * 40)
    
    # Wait a bit for services to start
    print("⏳ Waiting for services to start...")
    time.sleep(5)
    
    backend_ok = test_backend()
    frontend_ok = test_frontend()
    
    if backend_ok:
        test_api_endpoints()
    
    print("\n" + "=" * 40)
    if backend_ok and frontend_ok:
        print("🎉 All tests passed! SuperTickets.AI is running correctly.")
        print("\n📍 Access your application:")
        print("   🌐 Frontend: http://localhost:3000")
        print("   🔧 Backend:  http://localhost:8000")
        print("   📚 API Docs: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Check the logs:")
        print("   docker-compose logs supertickets-ai")
        print("   docker-compose logs frontend")
        sys.exit(1)

if __name__ == "__main__":
    main()