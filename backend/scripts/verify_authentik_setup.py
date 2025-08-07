#!/usr/bin/env python3
"""
Quick Authentik Verification Script

Run this after configuring the Authentik application to verify everything is working.
"""

import asyncio
import httpx
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_authentik_setup():
    """Verify that Authentik is properly configured"""
    base_url = "https://authentik.elefefe.eu"
    app_slug = "sonicus-platform"
    
    logger.info("🔍 Verifying Authentik setup...")
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        
        # Test 1: OIDC Discovery
        discovery_url = f"{base_url}/application/o/{app_slug}/.well-known/openid_configuration"
        logger.info(f"1️⃣ Testing OIDC Discovery: {discovery_url}")
        
        try:
            response = await client.get(discovery_url)
            if response.status_code == 200:
                config = response.json()
                logger.info("✅ OIDC Discovery works!")
                logger.info(f"   Issuer: {config.get('issuer')}")
                logger.info(f"   Authorization: {config.get('authorization_endpoint')}")
                logger.info(f"   Token: {config.get('token_endpoint')}")
                logger.info(f"   UserInfo: {config.get('userinfo_endpoint')}")
                logger.info(f"   JWKS: {config.get('jwks_uri')}")
                
                # Test 2: JWKS Endpoint
                jwks_uri = config.get('jwks_uri')
                if jwks_uri:
                    logger.info(f"\n2️⃣ Testing JWKS: {jwks_uri}")
                    jwks_response = await client.get(jwks_uri)
                    if jwks_response.status_code == 200:
                        jwks = jwks_response.json()
                        logger.info(f"✅ JWKS works! ({len(jwks.get('keys', []))} keys found)")
                    else:
                        logger.error(f"❌ JWKS failed: {jwks_response.status_code}")
                
                # Test 3: Authorization Endpoint Accessibility
                auth_endpoint = config.get('authorization_endpoint')
                if auth_endpoint:
                    logger.info(f"\n3️⃣ Testing Authorization endpoint accessibility: {auth_endpoint}")
                    # Just check if it's accessible (will return login form)
                    auth_response = await client.get(auth_endpoint, follow_redirects=False)
                    if auth_response.status_code in [200, 302, 400]:  # 400 is expected without params
                        logger.info("✅ Authorization endpoint is accessible!")
                    else:
                        logger.error(f"❌ Authorization endpoint failed: {auth_response.status_code}")
                
                logger.info("\n🎉 Authentik setup verification complete!")
                logger.info("Ready to run: python3 scripts/setup_authentik_dev.py")
                return True
                
            else:
                logger.error(f"❌ OIDC Discovery failed: {response.status_code}")
                logger.error("🔧 Please complete Authentik configuration (see AUTHENTIK_SETUP_REQUIRED.md)")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            logger.error("🔧 Check Authentik instance accessibility")
            return False

if __name__ == "__main__":
    success = asyncio.run(verify_authentik_setup())
    exit(0 if success else 1)
