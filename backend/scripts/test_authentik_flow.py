#!/usr/bin/env python3
"""
Authentik OIDC Flow Test Script

This script tests the complete OIDC authentication flow with Authentik.
"""

import os
import sys
import asyncio
import logging
import httpx
from typing import Dict, Any, Optional
import json
from urllib.parse import parse_qs, urlparse
import secrets
import base64
import hashlib

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

class AuthentikFlowTester:
    """Test the complete Authentik OIDC flow"""
    
    def __init__(self):
        self.base_url = os.getenv("AUTHENTIK_BASE_URL", "https://veritas.elefefe.eu")
        self.client_id = os.getenv("AUTHENTIK_CLIENT_ID")
        self.client_secret = os.getenv("AUTHENTIK_CLIENT_SECRET")
        self.redirect_uri = os.getenv("AUTHENTIK_REDIRECT_URI", "http://localhost:3000/auth/callback")
        
        # OIDC configuration cache
        self.oidc_config = None
        self.jwks = None
        
        logger.info("🧪 Authentik OIDC Flow Tester Initialized")
    
    async def fetch_oidc_config(self) -> Dict[str, Any]:
        """Fetch OIDC configuration"""
        if self.oidc_config is None:
            async with httpx.AsyncClient() as client:
                discovery_url = f"{self.base_url}/application/o/sonicus-platform/.well-known/openid_configuration"
                response = await client.get(discovery_url)
                response.raise_for_status()
                self.oidc_config = response.json()
        
        return self.oidc_config
    
    async def fetch_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS for token verification"""
        if self.jwks is None:
            async with httpx.AsyncClient() as client:
                jwks_url = f"{self.base_url}/application/o/sonicus-platform/jwks/"
                response = await client.get(jwks_url)
                response.raise_for_status()
                self.jwks = response.json()
        
        return self.jwks
    
    def generate_pkce_challenge(self) -> tuple[str, str]:
        """Generate PKCE code challenge and verifier"""
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    async def test_authorization_endpoint(self) -> str:
        """Test authorization endpoint and generate auth URL"""
        logger.info("🔗 Testing authorization endpoint...")
        
        config = await self.fetch_oidc_config()
        auth_endpoint = config['authorization_endpoint']
        
        # Generate PKCE challenge
        code_verifier, code_challenge = self.generate_pkce_challenge()
        state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        auth_url = (
            f"{auth_endpoint}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope=openid+profile+email+groups"
            f"&state={state}"
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
        )
        
        logger.info("✅ Authorization URL generated:")
        logger.info(f"   {auth_url}")
        logger.info(f"   State: {state}")
        logger.info(f"   Code verifier: {code_verifier[:20]}...")
        
        return auth_url
    
    async def simulate_token_exchange(self, auth_code: str, code_verifier: str) -> Optional[Dict[str, Any]]:
        """Simulate token exchange (for testing purposes)"""
        logger.info("🔄 Simulating token exchange...")
        
        config = await self.fetch_oidc_config()
        token_endpoint = config['token_endpoint']
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': code_verifier
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_endpoint,
                    data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code == 200:
                    tokens = response.json()
                    logger.info("✅ Token exchange successful")
                    logger.info(f"   Access token: {tokens.get('access_token', 'N/A')[:20]}...")
                    logger.info(f"   Token type: {tokens.get('token_type', 'N/A')}")
                    logger.info(f"   Expires in: {tokens.get('expires_in', 'N/A')} seconds")
                    return tokens
                else:
                    logger.error(f"❌ Token exchange failed: {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Token exchange error: {e}")
            return None
    
    async def test_userinfo_endpoint(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Test userinfo endpoint"""
        logger.info("👤 Testing userinfo endpoint...")
        
        config = await self.fetch_oidc_config()
        userinfo_endpoint = config['userinfo_endpoint']
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    userinfo_endpoint,
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    logger.info("✅ Userinfo endpoint successful")
                    logger.info(f"   Subject: {user_info.get('sub', 'N/A')}")
                    logger.info(f"   Email: {user_info.get('email', 'N/A')}")
                    logger.info(f"   Name: {user_info.get('name', 'N/A')}")
                    logger.info(f"   Groups: {user_info.get('groups', [])}")
                    return user_info
                else:
                    logger.error(f"❌ Userinfo request failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Userinfo request error: {e}")
            return None
    
    async def test_role_mapping(self, user_info: Dict[str, Any]) -> str:
        """Test role mapping from groups"""
        logger.info("🎭 Testing role mapping...")
        
        # Import role mapping function
        try:
            from app.core.authentik_auth import determine_role_from_groups
            
            groups = user_info.get('groups', [])
            role = determine_role_from_groups(groups)
            
            logger.info(f"✅ Role mapping successful")
            logger.info(f"   Groups: {groups}")
            logger.info(f"   Mapped role: {role}")
            
            return role
            
        except ImportError as e:
            logger.error(f"❌ Failed to import role mapping function: {e}")
            return "user"
        except Exception as e:
            logger.error(f"❌ Role mapping error: {e}")
            return "user"
    
    async def test_backend_integration(self) -> bool:
        """Test backend integration endpoints"""
        logger.info("🔧 Testing backend integration...")
        
        try:
            # Import backend modules
            from app.routers.authentik_auth import router
            from app.core.authentik_auth import AuthentikAuth
            
            logger.info("✅ Backend modules imported successfully")
            
            # Test AuthentikAuth class
            auth = AuthentikAuth()
            
            # Test OIDC config fetch
            config = await auth.get_oidc_config()
            logger.info("✅ Backend OIDC config fetch works")
            
            # Test JWKS fetch
            jwks = await auth.get_jwks()
            logger.info("✅ Backend JWKS fetch works")
            
            # Test auth URL generation
            auth_url = auth.get_authorization_url()
            logger.info("✅ Backend auth URL generation works")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Backend integration test failed: {e}")
            return False
    
    def generate_test_instructions(self):
        """Generate step-by-step test instructions"""
        logger.info("📝 Manual Testing Instructions:")
        logger.info("=" * 60)
        logger.info("1. 🌐 Open the authorization URL in your browser")
        logger.info("2. 🔐 Login with your test user credentials:")
        logger.info("   - Super Admin: admin@sonicus.dev / [your password]")
        logger.info("   - Business Admin: bizadmin@sonicus.dev / [your password]")
        logger.info("   - Regular User: user@sonicus.dev / [your password]")
        logger.info("3. ✅ Authorize the application")
        logger.info("4. 📋 Copy the authorization code from the callback URL")
        logger.info("5. 🧪 Test token exchange with: python scripts/test_token_exchange.py [code]")
        logger.info("=" * 60)
    
    async def run_comprehensive_test(self):
        """Run comprehensive OIDC flow test"""
        logger.info("=" * 80)
        logger.info("🧪 AUTHENTIK OIDC FLOW TEST")
        logger.info("=" * 80)
        
        success_count = 0
        total_tests = 4
        
        # 1. Test OIDC discovery
        try:
            config = await self.fetch_oidc_config()
            logger.info("✅ OIDC discovery successful")
            logger.info(f"   Issuer: {config.get('issuer')}")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ OIDC discovery failed: {e}")
        
        logger.info("-" * 40)
        
        # 2. Test JWKS endpoint
        try:
            jwks = await self.fetch_jwks()
            logger.info(f"✅ JWKS fetch successful ({len(jwks.get('keys', []))} keys)")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ JWKS fetch failed: {e}")
        
        logger.info("-" * 40)
        
        # 3. Test authorization URL generation
        try:
            auth_url = await self.test_authorization_endpoint()
            logger.info("✅ Authorization URL generation successful")
            success_count += 1
            
            # Store auth URL for manual testing
            with open('dev_auth_url.txt', 'w') as f:
                f.write(auth_url)
            logger.info("   📁 Auth URL saved to: dev_auth_url.txt")
            
        except Exception as e:
            logger.error(f"❌ Authorization URL generation failed: {e}")
        
        logger.info("-" * 40)
        
        # 4. Test backend integration
        if await self.test_backend_integration():
            logger.info("✅ Backend integration test successful")
            success_count += 1
        else:
            logger.error("❌ Backend integration test failed")
        
        logger.info("-" * 40)
        
        # Generate manual test instructions
        self.generate_test_instructions()
        
        logger.info("=" * 80)
        logger.info(f"📊 TEST RESULTS: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            logger.info("🎉 ALL TESTS PASSED! OIDC flow is ready for testing!")
            logger.info("")
            logger.info("🚀 Ready for Phase 2: Backend Integration")
            return True
        else:
            logger.error("❌ Some tests failed. Please check the errors above.")
            return False

async def main():
    """Main function"""
    tester = AuthentikFlowTester()
    success = await tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
