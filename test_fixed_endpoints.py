#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:8000"

# Test the correct endpoints
endpoints = [
    "/api/system/status",
    "/api/system/config",
    "/api/tasks/active",
    "/api/files",
    "/api/chat/test",
]

print("Testing fixed endpoints...")
for endpoint in endpoints:
    try:
        response = requests.get(BASE_URL + endpoint, timeout=5)
        print(f"{'✅' if response.status_code == 200 else '❌'} {endpoint}: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"❌ {endpoint}: ERROR - {e}")
