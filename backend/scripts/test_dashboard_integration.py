"""
Test script for the enhanced Super Admin Dashboard with real-time features.

This script tests the new dashboard functionality including:
- Real API integration
- WebSocket connections  
- Cache management
- Data refresh mechanisms
"""

import asyncio
import json
import requests
import websockets
from datetime import datetime


class DashboardTester:
    """Test suite for the enhanced dashboard functionality."""
    
    def __init__(self, base_url="http://localhost:8000", ws_url="ws://localhost:8000"):
        self.base_url = base_url
        self.ws_url = ws_url
        self.token = None
        
    def authenticate(self):
        """Authenticate and get access token."""
        try:
            # Mock authentication - in real app, use proper login
            self.token = "mock-super-admin-token"
            print("✅ Authentication: Mock token set")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
            
    def test_dashboard_endpoints(self):
        """Test all dashboard API endpoints."""
        endpoints = [
            ("/api/v1/super-admin/dashboard/stats", "Platform Statistics"),
            ("/api/v1/super-admin/dashboard/revenue", "Revenue Analytics"),
            ("/api/v1/super-admin/dashboard/growth", "Growth Trends"),
            ("/api/v1/super-admin/dashboard/health", "System Health"),
            ("/api/v1/super-admin/dashboard/alerts", "System Alerts")
        ]
        
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        print("\n🔍 Testing Dashboard API Endpoints:")
        for endpoint, name in endpoints:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {name}: {len(str(data))} bytes received")
                else:
                    print(f"⚠️ {name}: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ {name}: Connection error - {e}")
                
    def test_management_endpoints(self):
        """Test dashboard management endpoints."""
        management_tests = [
            ("GET", "/api/v1/super-admin/dashboard/manage/cache/status", "Cache Status"),
            ("GET", "/api/v1/super-admin/dashboard/manage/health", "Management Health"),
            ("GET", "/api/v1/super-admin/dashboard/manage/stats", "Management Stats"),
        ]
        
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        print("\n🔧 Testing Management Endpoints:")
        for method, endpoint, name in management_tests:
            try:
                if method == "GET":
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        timeout=10
                    )
                else:
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        json={},
                        timeout=10
                    )
                
                if response.status_code in [200, 201]:
                    print(f"✅ {name}: Success")
                else:
                    print(f"⚠️ {name}: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ {name}: Connection error - {e}")
                
    async def test_websocket_connection(self):
        """Test WebSocket real-time connection."""
        print("\n🔄 Testing WebSocket Connection:")
        
        try:
            ws_endpoint = f"{self.ws_url}/ws/admin/dashboard?token={self.token}"
            
            async with websockets.connect(ws_endpoint) as websocket:
                print("✅ WebSocket: Connected successfully")
                
                # Send ping message
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(ping_message))
                print("📤 WebSocket: Ping sent")
                
                # Wait for response with timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "pong":
                        print("✅ WebSocket: Pong received - connection working")
                    else:
                        print(f"📥 WebSocket: Message received - {data.get('type', 'unknown')}")
                        
                except asyncio.TimeoutError:
                    print("⚠️ WebSocket: No response received (timeout)")
                    
        except Exception as e:
            print(f"❌ WebSocket: Connection failed - {e}")
            
    def test_cache_operations(self):
        """Test cache management operations."""
        print("\n💾 Testing Cache Operations:")
        
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        # Test cache status
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/super-admin/dashboard/manage/cache/status",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                cache_data = response.json()
                print("✅ Cache Status: Retrieved successfully")
                if "cache_statistics" in cache_data:
                    print(f"   Cache entries found: {len(cache_data.get('cache_statistics', {}))}")
            else:
                print(f"⚠️ Cache Status: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Cache Status: Error - {e}")
            
    def test_data_refresh(self):
        """Test manual data refresh functionality."""
        print("\n🔄 Testing Data Refresh:")
        
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/super-admin/dashboard/manage/refresh",
                headers=headers,
                json={},
                timeout=15
            )
            
            if response.status_code in [200, 202]:
                refresh_data = response.json()
                print("✅ Data Refresh: Initiated successfully")
                print(f"   Message: {refresh_data.get('message', 'No message')}")
            else:
                print(f"⚠️ Data Refresh: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Data Refresh: Error - {e}")
            
    def run_all_tests(self):
        """Run complete test suite."""
        print("🚀 Starting Enhanced Dashboard Test Suite")
        print("=" * 50)
        
        # Basic setup
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return
            
        # Test API endpoints
        self.test_dashboard_endpoints()
        
        # Test management features
        self.test_management_endpoints()
        
        # Test cache operations
        self.test_cache_operations()
        
        # Test data refresh
        self.test_data_refresh()
        
        # Test WebSocket (async)
        print("\n🔄 Running WebSocket test...")
        try:
            asyncio.run(self.test_websocket_connection())
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            
        print("\n✅ Test Suite Completed!")
        print("=" * 50)
        
        # Summary
        print("\n📋 Test Summary:")
        print("- Dashboard API endpoints tested")
        print("- Management endpoints tested") 
        print("- Cache operations tested")
        print("- Data refresh tested")
        print("- WebSocket connection tested")
        print("\nNote: Some tests may show warnings if the server is not running.")


if __name__ == "__main__":
    tester = DashboardTester()
    tester.run_all_tests()
