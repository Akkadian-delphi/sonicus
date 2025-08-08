#!/usr/bin/env python3
"""
Quick test script to check profile update endpoint
"""
import requests
import json

# Test configuration
BASE_URL = "http://127.0.0.1:18100/api/v1"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

def test_profile_endpoint():
    """Test the profile update endpoint"""
    
    print("🧪 Testing Profile Update Endpoint")
    print("-" * 40)
    
    # Test different endpoint paths to find the right one
    endpoints_to_test = [
        "/users/me",       # What frontend expects (legacy path)
        "/api/users/me",   # Unified router path without v1
        "/api/v1/users/me" # Full path with API version
    ]
    
    print("1. Attempting to get authentication...")
    
    try:
        # Try the unified router login endpoint first
        login_response = requests.post(
            f"{BASE_URL}/users/login",  # Unified router login
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers={
                "Content-Type": "application/json"
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            print(f"✅ Authentication successful via unified router")
        else:
            print(f"❌ Unified auth failed: {login_response.status_code}")
            # Try legacy token endpoint
            login_response = requests.post(
                f"{BASE_URL}/token",
                data={
                    "username": TEST_EMAIL,
                    "password": TEST_PASSWORD
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                print(f"✅ Authentication successful via legacy token endpoint")
            else:
                print(f"❌ Legacy auth also failed: {login_response.status_code}")
                token = None
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        print("   Trying without authentication...")
        token = None
    
    # Test the different profile endpoint paths
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    for i, endpoint in enumerate(endpoints_to_test, 2):
        print(f"\n{i}. Testing GET {endpoint}...")
        try:
            get_response = requests.get(f"http://127.0.0.1:18100{endpoint}", headers=headers)
            print(f"   Status: {get_response.status_code}")
            if get_response.status_code == 200:
                print(f"   ✅ Success! Data: {get_response.json()}")
            elif get_response.status_code == 401:
                print(f"   🔐 Authentication required")
            elif get_response.status_code == 404:
                print(f"   ❌ Endpoint not found")
            else:
                print(f"   ❓ Error: {get_response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        print(f"\n{i + len(endpoints_to_test)}. Testing PUT {endpoint}...")
        test_data = {
            "telephone": "+1234567890",
            "company_name": "Test Company Updated"
        }
        
        try:
            put_response = requests.put(
                f"http://127.0.0.1:18100{endpoint}", 
                json=test_data,
                headers={**headers, "Content-Type": "application/json"}
            )
            print(f"   Status: {put_response.status_code}")
            if put_response.status_code in [200, 201]:
                print(f"   ✅ Success! Data: {put_response.json()}")
            elif put_response.status_code == 401:
                print(f"   🔐 Authentication required")
            elif put_response.status_code == 404:
                print(f"   ❌ Endpoint not found")
            elif put_response.status_code == 405:
                allowed_methods = put_response.headers.get('Allow', 'Not specified')
                print(f"   🚫 Method not allowed. Allowed: {allowed_methods}")
            else:
                print(f"   ❓ Error: {put_response.text}")
                
        except Exception as e:
            print(f"   Exception: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed! Check which endpoint path works.")

if __name__ == "__main__":
    test_profile_endpoint()
