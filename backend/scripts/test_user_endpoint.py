#!/usr/bin/env python3
"""
Test script to check user authentication and role
"""
import requests
import json

def test_login_and_user_me():
    base_url = "http://localhost:18100"
    
    # Test data
    login_data = {
        "email": "dev@elefefe.eu",
        "password": "your_password_here"  # Replace with actual password
    }
    
    print("Testing JWT login and user/me endpoint...")
    
    # Step 1: Login
    try:
        login_response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            print(f"✅ Login successful!")
            print(f"Token type: {token_data.get('token_type')}")
            
            # Step 2: Get user info
            headers = {"Authorization": f"Bearer {access_token}"}
            user_response = requests.get(f"{base_url}/api/v1/users/me", headers=headers)
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                print(f"✅ User data retrieved successfully!")
                print(f"User data: {json.dumps(user_data, indent=2)}")
                
                # Check role specifically
                print(f"\n🔍 Role Analysis:")
                print(f"Role: {user_data.get('role')}")
                print(f"Role type: {type(user_data.get('role'))}")
                print(f"Role lowercase: {user_data.get('role', '').lower()}")
                print(f"Organization ID: {user_data.get('organization_id')}")
                
            else:
                print(f"❌ Failed to get user data: {user_response.status_code}")
                print(f"Response: {user_response.text}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Please update the password in the script and run again.")
    # test_login_and_user_me()
