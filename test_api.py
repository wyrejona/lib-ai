#!/usr/bin/env python3
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_endpoints():
    endpoints = [
        "/health",
        "/api/system/status",
        "/api/system/config",
        "/api/tasks",
        "/api/chat/test",
        "/api/files/list",
        "/api/system/models"
    ]
    
    print("Testing API endpoints...")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            url = BASE_URL + endpoint
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint:30} {response.status_code}")
            
            if response.status_code != 200:
                print(f"   Response: {response.text[:100]}")
        except Exception as e:
            print(f"❌ {endpoint:30} ERROR: {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_endpoints()
