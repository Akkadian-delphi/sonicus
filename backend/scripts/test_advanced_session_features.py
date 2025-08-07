#!/usr/bin/env python3
"""
Advanced Session Features Integration Test

This script tests all the advanced session features:
- Role-based session timeout policies
- IP-based access restrictions
- Two-factor authentication
- Session analytics and monitoring
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import UserRole
from app.core.advanced_session import advanced_session_manager
from app.core.two_factor_auth import two_factor_auth_manager
from app.core.session_monitoring import session_analytics, session_monitoring_dashboard


class AdvancedSessionTester:
    """Test all advanced session features"""
    
    def __init__(self):
        self.test_user_id = 12345
        self.test_email = "admin@test.com"
        self.test_ip = "192.168.1.100"
        self.test_user_agent = "TestBot/1.0"
        self.results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
        print(f"{status}: {test_name} - {details}")
    
    def test_advanced_session_creation(self):
        """Test advanced session creation with role-based policies"""
        try:
            # Test session creation for admin role
            session_data = advanced_session_manager.create_advanced_session(
                user_id=self.test_user_id,
                role=UserRole.BUSINESS_ADMIN,
                ip_address=self.test_ip,
                user_agent=self.test_user_agent,
                organization_id=1
            )
            
            success = bool(session_data and "session_id" in session_data)
            timeout = session_data.get("timeout_minutes", 0) if session_data else 0
            
            self.log_test(
                "Advanced Session Creation", 
                success, 
                f"Created session with {timeout}min timeout for BUSINESS_ADMIN"
            )
            
            return session_data
            
        except Exception as e:
            self.log_test("Advanced Session Creation", False, f"Error: {e}")
            return None
    
    def test_session_validation(self, session_data):
        """Test session validation with security policies"""
        if not session_data:
            self.log_test("Session Validation", False, "No session data to validate")
            return
        
        try:
            session_id = session_data.get("session_id")
            is_valid, validated_data, error_reason = advanced_session_manager.validate_session_with_policies(
                session_id=session_id,
                current_ip=self.test_ip,
                current_user_agent=self.test_user_agent
            )
            
            self.log_test(
                "Session Validation", 
                is_valid, 
                f"Validation result: {error_reason or 'Valid'}"
            )
            
        except Exception as e:
            self.log_test("Session Validation", False, f"Error: {e}")
    
    def test_ip_restrictions(self):
        """Test IP-based access restrictions"""
        try:
            # Add IP restriction
            allowed_ips = ["192.168.1.0/24", "10.0.0.1"]
            success = advanced_session_manager.add_ip_restriction(
                user_id=self.test_user_id,
                allowed_ips=allowed_ips
            )
            
            self.log_test(
                "IP Restriction Addition", 
                success, 
                f"Added restrictions for {len(allowed_ips)} IP ranges"
            )
            
            # Test IP validation (should pass)
            is_allowed = advanced_session_manager._check_ip_restrictions(
                user_id=self.test_user_id,
                current_ip="192.168.1.100"  # Should be allowed
            )
            
            self.log_test(
                "IP Restriction Validation (Allowed)", 
                is_allowed, 
                "IP 192.168.1.100 validation"
            )
            
            # Test IP validation (should fail)
            is_blocked = not advanced_session_manager._check_ip_restrictions(
                user_id=self.test_user_id,
                current_ip="203.0.113.1"  # Should be blocked
            )
            
            self.log_test(
                "IP Restriction Validation (Blocked)", 
                is_blocked, 
                "IP 203.0.113.1 validation"
            )
            
        except Exception as e:
            self.log_test("IP Restrictions", False, f"Error: {e}")
    
    def test_2fa_setup(self):
        """Test two-factor authentication setup"""
        try:
            # Generate secret
            secret = two_factor_auth_manager.generate_secret_key(self.test_user_id)
            
            self.log_test(
                "2FA Secret Generation", 
                bool(secret), 
                f"Generated secret: {secret[:8]}..." if secret else "No secret"
            )
            
            # Test QR code generation
            if secret:
                qr_data = two_factor_auth_manager.generate_qr_code(
                    user_id=self.test_user_id,
                    user_email=self.test_email,
                    secret=secret
                )
                
                self.log_test(
                    "2FA QR Code Generation", 
                    bool(qr_data), 
                    f"Generated QR code: {len(qr_data)} bytes" if qr_data else "No QR code"
                )
            
            return secret
            
        except Exception as e:
            self.log_test("2FA Setup", False, f"Error: {e}")
            return None
    
    def test_2fa_status(self):
        """Test 2FA status checking"""
        try:
            status = two_factor_auth_manager.get_2fa_status(self.test_user_id)
            
            self.log_test(
                "2FA Status Check", 
                isinstance(status, dict), 
                f"Status: {status.get('enabled', 'Unknown')}"
            )
            
        except Exception as e:
            self.log_test("2FA Status Check", False, f"Error: {e}")
    
    def test_session_analytics(self):
        """Test session analytics and monitoring"""
        try:
            # Test session overview
            overview = session_analytics.get_session_overview(days=7)
            
            self.log_test(
                "Session Analytics Overview", 
                isinstance(overview, dict), 
                f"Overview keys: {list(overview.keys())[:5]}"
            )
            
            # Test user session history
            history = session_analytics.get_user_session_history(
                user_id=self.test_user_id, 
                days=30
            )
            
            self.log_test(
                "User Session History", 
                isinstance(history, dict), 
                f"History user_id: {history.get('user_id', 'Unknown')}"
            )
            
            # Test active sessions
            active_sessions = session_analytics.get_active_sessions_detailed()
            
            self.log_test(
                "Active Sessions Query", 
                isinstance(active_sessions, list), 
                f"Found {len(active_sessions)} active sessions"
            )
            
        except Exception as e:
            self.log_test("Session Analytics", False, f"Error: {e}")
    
    def test_dashboard_data(self):
        """Test dashboard data compilation"""
        try:
            dashboard = session_monitoring_dashboard.get_dashboard_data()
            
            self.log_test(
                "Dashboard Data Compilation", 
                isinstance(dashboard, dict), 
                f"Dashboard sections: {list(dashboard.keys())}"
            )
            
        except Exception as e:
            self.log_test("Dashboard Data", False, f"Error: {e}")
    
    def cleanup(self):
        """Clean up test data"""
        try:
            # Remove IP restrictions
            advanced_session_manager.remove_ip_restriction(self.test_user_id)
            
            # Disable 2FA if enabled
            two_factor_auth_manager.disable_2fa(
                user_id=self.test_user_id,
                ip_address=self.test_ip,
                user_agent=self.test_user_agent
            )
            
            # Terminate test user sessions
            advanced_session_manager.terminate_user_sessions(self.test_user_id)
            
            self.log_test("Test Cleanup", True, "Cleaned up test data")
            
        except Exception as e:
            self.log_test("Test Cleanup", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all advanced session feature tests"""
        print("🚀 Starting Advanced Session Features Integration Test")
        print("=" * 60)
        
        # Test advanced session management
        session_data = self.test_advanced_session_creation()
        self.test_session_validation(session_data)
        
        # Test IP restrictions
        self.test_ip_restrictions()
        
        # Test 2FA
        secret = self.test_2fa_setup()
        self.test_2fa_status()
        
        # Test analytics
        self.test_session_analytics()
        self.test_dashboard_data()
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: ✅ {passed_tests}")
        print(f"Failed: ❌ {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n🎯 Advanced Session Features: {passed_tests}/{total_tests} components working")
        
        return passed_tests == total_tests


def main():
    """Main test execution"""
    tester = AdvancedSessionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All advanced session features are working correctly!")
        return 0
    else:
        print("\n⚠️  Some advanced session features need attention.")
        return 1


if __name__ == "__main__":
    exit(main())
