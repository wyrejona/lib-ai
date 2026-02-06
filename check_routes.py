#!/usr/bin/env python3
import requests
import json

BASE = "http://localhost:8000"

try:
    # Get all routes
    response = requests.get(f"{BASE}/debug/routes", timeout=5)
    data = response.json()
    
    print("=== ALL REGISTERED ROUTES ===")
    for route in sorted(data.get("routes", []), key=lambda x: x["path"]):
        methods = route.get("methods", [])
        print(f"{route['path']:30} {methods}")
    
    print("\n=== API ROUTES ONLY ===")
    api_routes = [r for r in data.get("routes", []) if r["path"].startswith("/api")]
    for route in sorted(api_routes, key=lambda x: x["path"]):
        methods = route.get("methods", [])
        print(f"{route['path']:30} {methods}")
        
except Exception as e:
    print(f"Error: {e}")
