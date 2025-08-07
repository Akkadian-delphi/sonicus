#!/usr/bin/env python3
"""
Authentik Development Setup Script

This script helps set up and test the Authentik OIDC integration for development.
"""

import os
import sys
import asyncio
import logging
import httpx
from typing import Dict, Any
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuthentikDevSetup:
    """Development setup and testing for Authentik OIDC"""
    
    def __init__(self):
        self.base_url = os.getenv("AUTHENTIK_BASE_URL", "https://authentik.elefefe.eu")
        self.client_id = os.getenv("AUTHENTIK_CLIENT_ID")
        self.client_secret = os.getenv("AUTHENTIK_CLIENT_SECRET")
        self.redirect_uri = os.getenv("AUTHENTIK_REDIRECT_URI", "http://localhost:3000/auth/callback")
        
        logger.info("🚀 Authentik Development Setup Initialized")
        logger.info(f"   Base URL: {self.base_url}")
        logger.info(f"   Client ID: {'✓ Set' if self.client_id else '❌ Missing'}")
        logger.info(f"   Client Secret: {'✓ Set' if self.client_secret else '❌ Missing'}")
        logger.info(f"   Redirect URI: {self.redirect_uri}")
    
    async def test_authentik_connectivity(self) -> bool:
        """Test basic connectivity to Authentik instance"""
        logger.info("🔍 Testing Authentik connectivity...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test OIDC discovery endpoint
                discovery_url = f"{self.base_url}/application/o/sonicus-platform/.well-known/openid_configuration"
                logger.info(f"   Testing discovery endpoint: {discovery_url}")
                
                response = await client.get(discovery_url)
                
                if response.status_code == 200:
                    config = response.json()
                    logger.info("✅ OIDC Discovery endpoint accessible")
                    logger.info(f"   Issuer: {config.get('issuer', 'N/A')}")
                    logger.info(f"   Authorization endpoint: {config.get('authorization_endpoint', 'N/A')}")
                    logger.info(f"   Token endpoint: {config.get('token_endpoint', 'N/A')}")
                    logger.info(f"   UserInfo endpoint: {config.get('userinfo_endpoint', 'N/A')}")
                    logger.info(f"   JWKS URI: {config.get('jwks_uri', 'N/A')}")
                    return True
                else:
                    logger.error(f"❌ Discovery endpoint returned {response.status_code}")
                    logger.error(f"   Response: {response.text[:200]}...")
                    return False
                    
        except httpx.TimeoutException:
            logger.error("❌ Timeout connecting to Authentik")
            return False
        except Exception as e:
            logger.error(f"❌ Error connecting to Authentik: {e}")
            return False
    
    async def test_jwks_endpoint(self) -> bool:
        """Test JWKS endpoint for token verification"""
        logger.info("🔑 Testing JWKS endpoint...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                jwks_url = f"{self.base_url}/application/o/sonicus-platform/jwks/"
                logger.info(f"   Testing JWKS endpoint: {jwks_url}")
                
                response = await client.get(jwks_url)
                
                if response.status_code == 200:
                    jwks = response.json()
                    keys_count = len(jwks.get('keys', []))
                    logger.info(f"✅ JWKS endpoint accessible with {keys_count} keys")
                    
                    # Log key information (without sensitive data)
                    for i, key in enumerate(jwks.get('keys', [])[:2]):  # Show first 2 keys only
                        logger.info(f"   Key {i+1}: {key.get('kty')} - {key.get('use')} - {key.get('kid', 'no kid')}")
                    
                    return True
                else:
                    logger.error(f"❌ JWKS endpoint returned {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error accessing JWKS endpoint: {e}")
            return False
    
    def generate_auth_url(self) -> str:
        """Generate authorization URL for testing"""
        if not self.client_id:
            logger.error("❌ Cannot generate auth URL - Client ID not set")
            return ""
        
        auth_url = (
            f"{self.base_url}/application/o/authorize/"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope=openid+profile+email+groups"
            f"&state=dev-test-{int(datetime.now().timestamp())}"
        )
        
        logger.info("🔗 Generated authorization URL:")
        logger.info(f"   {auth_url}")
        
        return auth_url
    
    def check_environment_variables(self) -> bool:
        """Check if all required environment variables are set"""
        logger.info("⚙️  Checking environment variables...")
        
        required_vars = {
            "AUTHENTIK_BASE_URL": self.base_url,
            "AUTHENTIK_CLIENT_ID": self.client_id,
            "AUTHENTIK_CLIENT_SECRET": self.client_secret,
            "AUTHENTIK_REDIRECT_URI": self.redirect_uri
        }
        
        all_set = True
        
        for var_name, var_value in required_vars.items():
            if var_value:
                if var_name == "AUTHENTIK_CLIENT_SECRET":
                    logger.info(f"✅ {var_name}: {'*' * min(len(var_value), 20)}...")
                else:
                    logger.info(f"✅ {var_name}: {var_value}")
            else:
                logger.error(f"❌ {var_name}: Not set")
                all_set = False
        
        return all_set
    
    async def test_auth_integration(self) -> bool:
        """Test the Authentik auth integration"""
        logger.info("🧪 Testing Authentik auth integration...")
        
        try:
            # Import and test our auth module
            from app.core.authentik_auth import AuthentikAuth
            
            auth = AuthentikAuth()
            logger.info("✅ AuthentikAuth class imported successfully")
            
            # Test OIDC config fetch
            try:
                config = await auth.get_oidc_config()
                logger.info("✅ OIDC configuration fetched successfully")
                logger.info(f"   Issuer: {config.get('issuer', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ Failed to fetch OIDC config: {e}")
                return False
            
            # Test JWKS fetch
            try:
                jwks = await auth.get_jwks()
                logger.info(f"✅ JWKS fetched successfully ({len(jwks.get('keys', []))} keys)")
            except Exception as e:
                logger.error(f"❌ Failed to fetch JWKS: {e}")
                return False
            
            # Test authorization URL generation
            try:
                auth_url = auth.get_authorization_url()
                logger.info("✅ Authorization URL generated successfully")
                logger.info(f"   URL: {auth_url[:80]}...")
            except Exception as e:
                logger.error(f"❌ Failed to generate authorization URL: {e}")
                return False
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ Failed to import AuthentikAuth: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Integration test failed: {e}")
            return False
    
    def create_test_users_guide(self):
        """Generate guide for creating test users"""
        logger.info("👥 Test Users Setup Guide:")
        logger.info("   1. Access Authentik admin: https://authentik.elefefe.eu/if/admin/")
        logger.info("   2. Go to Directory → Users")
        logger.info("   3. Create test users with these profiles:")
        logger.info("")
        logger.info("   📝 Super Admin User:")
        logger.info("      Username: admin@sonicus.dev")
        logger.info("      Email: admin@sonicus.dev")
        logger.info("      Name: Super Admin Dev")
        logger.info("      Groups: sonicus-super-admin")
        logger.info("")
        logger.info("   📝 Business Admin User:")
        logger.info("      Username: bizadmin@sonicus.dev")
        logger.info("      Email: bizadmin@sonicus.dev") 
        logger.info("      Name: Business Admin Dev")
        logger.info("      Groups: sonicus-business-admin")
        logger.info("")
        logger.info("   📝 Regular User:")
        logger.info("      Username: user@sonicus.dev")
        logger.info("      Email: user@sonicus.dev")
        logger.info("      Name: Regular User Dev")
        logger.info("      Groups: sonicus-user")
        logger.info("")
        logger.info("   4. Set passwords for all test users")
        logger.info("   5. Ensure all users are active")
    
    async def run_full_setup_test(self):
        """Run complete setup and testing process"""
        logger.info("=" * 80)
        logger.info("🚀 AUTHENTIK DEVELOPMENT SETUP - PHASE 1")
        logger.info("=" * 80)
        
        success_count = 0
        total_tests = 5
        
        # 1. Check environment variables
        if self.check_environment_variables():
            success_count += 1
            logger.info("✅ Environment variables check passed")
        else:
            logger.error("❌ Environment variables check failed")
        
        logger.info("-" * 40)
        
        # 2. Test connectivity
        if await self.test_authentik_connectivity():
            success_count += 1
            logger.info("✅ Authentik connectivity test passed")
        else:
            logger.error("❌ Authentik connectivity test failed")
        
        logger.info("-" * 40)
        
        # 3. Test JWKS
        if await self.test_jwks_endpoint():
            success_count += 1
            logger.info("✅ JWKS endpoint test passed")
        else:
            logger.error("❌ JWKS endpoint test failed")
        
        logger.info("-" * 40)
        
        # 4. Test auth integration
        if await self.test_auth_integration():
            success_count += 1
            logger.info("✅ Auth integration test passed")
        else:
            logger.error("❌ Auth integration test failed")
        
        logger.info("-" * 40)
        
        # 5. Generate auth URL
        auth_url = self.generate_auth_url()
        if auth_url:
            success_count += 1
            logger.info("✅ Authorization URL generation passed")
        else:
            logger.error("❌ Authorization URL generation failed")
        
        logger.info("-" * 40)
        
        # Display test users guide
        self.create_test_users_guide()
        
        logger.info("=" * 80)
        logger.info(f"📊 SETUP RESULTS: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Authentik development setup is ready!")
            logger.info("")
            logger.info("Next steps:")
            logger.info("1. Create test users in Authentik (see guide above)")
            logger.info("2. Test authentication flow with the generated URL")
            logger.info("3. Run: python scripts/test_authentik_flow.py")
            return True
        else:
            logger.error("❌ Some tests failed. Please check the errors above.")
            return False

async def main():
    """Main function"""
    setup = AuthentikDevSetup()
    success = await setup.run_full_setup_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
