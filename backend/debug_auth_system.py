#!/usr/bin/env python3
"""
Comprehensive Authentication System Debug Script

This script tests all authentication components and provides recommendations.
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthDebugger:
    """Comprehensive authentication system debugger"""
    
    def __init__(self):
        self.results = {}
        self.recommendations = []
    
    async def test_oidc_configuration(self) -> Dict[str, Any]:
        """Test OIDC/Authentik configuration"""
        logger.info("🔍 Testing OIDC Configuration...")
        
        try:
            from app.core.authentik_auth import AuthentikAuth
            auth = AuthentikAuth()
            
            # Test discovery endpoints
            try:
                config = await auth.get_oidc_config()
                return {
                    "status": "✅ WORKING",
                    "config_endpoints": len(config),
                    "discovery_url": "Found working endpoint"
                }
            except Exception as e:
                return {
                    "status": "❌ FAILED", 
                    "error": str(e),
                    "issue": "OIDC discovery endpoints not accessible"
                }
                
        except Exception as e:
            return {
                "status": "❌ IMPORT ERROR",
                "error": str(e)
            }
    
    def test_jwt_authentication(self) -> Dict[str, Any]:
        """Test JWT authentication system"""
        logger.info("🔍 Testing JWT Authentication...")
        
        try:
            from app.core.security import create_access_token, SECRET_KEY, ALGORITHM
            from jose import jwt
            from datetime import timedelta
            
            # Create test token
            test_data = {"sub": "test@example.com", "exp": datetime.utcnow() + timedelta(minutes=30)}
            test_token = create_access_token(test_data)
            
            # Verify token
            decoded = jwt.decode(test_token, SECRET_KEY, algorithms=[ALGORITHM])
            
            return {
                "status": "✅ WORKING",
                "secret_key_configured": bool(SECRET_KEY and SECRET_KEY != "dev-secret-key-change-in-production"),
                "algorithm": ALGORITHM,
                "test_token_created": bool(test_token),
                "test_token_verified": bool(decoded)
            }
            
        except Exception as e:
            return {
                "status": "❌ FAILED",
                "error": str(e)
            }
    
    def test_database_connection(self) -> Dict[str, Any]:
        """Test database connectivity"""
        logger.info("🔍 Testing Database Connection...")
        
        try:
            from app.db.session import get_db
            from app.models.user import User
            
            # Get database session
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                # Test query
                user_count = db.query(User).count()
                db.close()
                
                return {
                    "status": "✅ WORKING",
                    "user_count": user_count,
                    "connection": "Successful"
                }
                
            except Exception as e:
                db.close()
                return {
                    "status": "❌ QUERY FAILED",
                    "error": str(e)
                }
                
        except Exception as e:
            return {
                "status": "❌ CONNECTION FAILED",
                "error": str(e)
            }
    
    def test_environment_variables(self) -> Dict[str, Any]:
        """Test environment variable configuration"""
        logger.info("🔍 Testing Environment Variables...")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = {
            "SECRET_KEY": os.getenv("SECRET_KEY"),
            "POSTGRES_SERVER": os.getenv("POSTGRES_SERVER"),
            "POSTGRES_USER": os.getenv("POSTGRES_USER"),
            "POSTGRES_DB": os.getenv("POSTGRES_DB"),
        }
        
        optional_vars = {
            "AUTHENTIK_BASE_URL": os.getenv("AUTHENTIK_BASE_URL"),
            "AUTHENTIK_CLIENT_ID": os.getenv("AUTHENTIK_CLIENT_ID"),
            "AUTHENTIK_CLIENT_SECRET": os.getenv("AUTHENTIK_CLIENT_SECRET"),
        }
        
        missing_required = [k for k, v in required_vars.items() if not v]
        missing_optional = [k for k, v in optional_vars.items() if not v]
        
        status = "✅ WORKING" if not missing_required else "⚠️  PARTIAL"
        
        return {
            "status": status,
            "required_missing": missing_required,
            "optional_missing": missing_optional,
            "total_configured": len(required_vars) + len(optional_vars) - len(missing_required) - len(missing_optional)
        }
    
    async def test_authentication_endpoints(self) -> Dict[str, Any]:
        """Test authentication endpoint accessibility"""
        logger.info("🔍 Testing Authentication Endpoints...")
        
        try:
            import httpx
            
            # Test backend health
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get("http://localhost:18100/api/v1/health")
                    backend_status = "✅ ACCESSIBLE" if response.status_code == 200 else f"❌ ERROR {response.status_code}"
                except Exception:
                    backend_status = "❌ NOT ACCESSIBLE"
            
            return {
                "status": backend_status,
                "backend_port": "18100",
                "health_endpoint": backend_status
            }
            
        except Exception as e:
            return {
                "status": "❌ TEST FAILED",
                "error": str(e)
            }
    
    def analyze_error_logs(self) -> Dict[str, Any]:
        """Analyze recent error logs"""
        logger.info("🔍 Analyzing Error Logs...")
        
        try:
            log_file = "/Users/luis/Projects/Elefefe/Sonicus/backend/logs/errors.log"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Count recent 'kid' errors
                kid_errors = [line for line in lines[-100:] if "'kid'" in line]
                auth_errors = [line for line in lines[-100:] if "Authentication failed" in line]
                
                return {
                    "status": "✅ ANALYZED",
                    "total_recent_lines": min(100, len(lines)),
                    "kid_errors": len(kid_errors),
                    "auth_errors": len(auth_errors),
                    "log_file_exists": True
                }
            else:
                return {
                    "status": "⚠️  NO LOG FILE",
                    "log_file_exists": False
                }
                
        except Exception as e:
            return {
                "status": "❌ ANALYSIS FAILED",
                "error": str(e)
            }
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        logger.info("💡 Generating Recommendations...")
        
        # OIDC recommendations
        if self.results.get("oidc", {}).get("status") == "❌ FAILED":
            self.recommendations.append({
                "priority": "HIGH",
                "category": "OIDC Configuration",
                "issue": "Authentik OIDC discovery endpoints not accessible",
                "solution": "1. Verify Authentik instance is running at https://authentik.elefefe.eu\n2. Check if 'sonicus-platform' application exists\n3. Verify OIDC provider configuration\n4. Consider using JWT-only authentication temporarily"
            })
        
        # JWT recommendations
        jwt_status = self.results.get("jwt", {})
        if jwt_status.get("status") == "✅ WORKING" and not jwt_status.get("secret_key_configured"):
            self.recommendations.append({
                "priority": "MEDIUM",
                "category": "Security",
                "issue": "Using default SECRET_KEY",
                "solution": "Generate a secure SECRET_KEY for production use"
            })
        
        # Database recommendations
        if self.results.get("database", {}).get("status") != "✅ WORKING":
            self.recommendations.append({
                "priority": "HIGH",
                "category": "Database",
                "issue": "Database connection issues",
                "solution": "Check PostgreSQL service and connection parameters"
            })
        
        # Error log recommendations
        error_analysis = self.results.get("error_logs", {})
        if error_analysis.get("kid_errors", 0) > 10:
            self.recommendations.append({
                "priority": "MEDIUM",
                "category": "Error Reduction",
                "issue": f"{error_analysis.get('kid_errors')} recent authentication errors",
                "solution": "The improved authentication system with JWT fallback should reduce these errors"
            })
    
    def print_results(self):
        """Print comprehensive results"""
        print("\n" + "="*80)
        print("🔍 SONICUS AUTHENTICATION SYSTEM - COMPREHENSIVE DEBUG REPORT")
        print("="*80)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test Results
        print("\n📋 TEST RESULTS:")
        print("-"*50)
        
        for category, result in self.results.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            print(f"  Status: {result.get('status', 'Unknown')}")
            
            for key, value in result.items():
                if key != 'status':
                    print(f"  {key}: {value}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-"*50)
        
        if not self.recommendations:
            print("✅ No critical issues found!")
        else:
            for i, rec in enumerate(self.recommendations, 1):
                print(f"\n{i}. [{rec['priority']}] {rec['category']}")
                print(f"   Issue: {rec['issue']}")
                print(f"   Solution: {rec['solution']}")
        
        # System Status Summary
        print("\n📊 SYSTEM STATUS SUMMARY:")
        print("-"*50)
        
        working_count = sum(1 for r in self.results.values() if r.get('status', '').startswith('✅'))
        total_tests = len(self.results)
        health_percentage = (working_count / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Overall Health: {health_percentage:.1f}% ({working_count}/{total_tests} systems working)")
        
        if health_percentage >= 80:
            print("🟢 System Status: HEALTHY")
        elif health_percentage >= 60:
            print("🟡 System Status: NEEDS ATTENTION")
        else:
            print("🔴 System Status: CRITICAL ISSUES")
        
        print("\n" + "="*80)
    
    async def run_all_tests(self):
        """Run all authentication tests"""
        logger.info("🚀 Starting Comprehensive Authentication Debug...")
        
        # Run all tests
        self.results["environment"] = self.test_environment_variables()
        self.results["database"] = self.test_database_connection()
        self.results["jwt"] = self.test_jwt_authentication()
        self.results["oidc"] = await self.test_oidc_configuration()
        self.results["endpoints"] = await self.test_authentication_endpoints()
        self.results["error_logs"] = self.analyze_error_logs()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Print results
        self.print_results()


async def main():
    """Main function"""
    debugger = AuthDebugger()
    await debugger.run_all_tests()
    

if __name__ == "__main__":
    asyncio.run(main())
