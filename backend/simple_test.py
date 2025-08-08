#!/usr/bin/env python3
"""
Simple test to check if PUT /users/me endpoint works
"""
import requests
import json

BASE_URL = "http://127.0.0.1:18100/api/v1"

def test_put_endpoint():
    """Test just the PUT endpoint"""
    print("🔍 Testing PUT /users/me endpoint...")
    
    # Test without authentication first to see if endpoint exists
    test_data = {
        "telephone": "+1234567890",
        "company_name": "Test Company Updated"
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/users/me", 
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            print("✅ Endpoint exists! (Authentication required)")
        elif response.status_code == 405:
            allowed = response.headers.get('Allow', 'Not specified')
            print(f"❌ Method not allowed. Allowed methods: {allowed}")
        elif response.status_code == 404:
            print("❌ Endpoint not found")
        elif response.status_code == 422:
            print("✅ Endpoint exists! (Validation error)")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_put_endpoint()
