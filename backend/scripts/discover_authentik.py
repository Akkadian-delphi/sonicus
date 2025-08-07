#!/usr/bin/env python3
"""
Authentik Discovery Script

This script helps discover the correct Authentik application configuration
by testing different endpoint patterns.
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def discover_authentik_endpoints():
    """Discover the correct Authentik endpoints"""
    base_url = "https://authentik.elefefe.eu"
    
    logger.info("🔍 Discovering Authentik endpoints...")
    
    # Test different application patterns
    patterns_to_test = [
        "/application/o/.well-known/openid_configuration",
        "/application/o/sonicus/.well-known/openid_configuration", 
        "/application/o/sonicus-platform/.well-known/openid_configuration",
        "/application/o/elefefe/.well-known/openid_configuration",
        "/application/o/default/.well-known/openid_configuration",
        "/.well-known/openid_configuration",
        "/auth/realms/master/.well-known/openid_configuration"
    ]
    
    working_endpoints = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for pattern in patterns_to_test:
            url = f"{base_url}{pattern}"
            logger.info(f"Testing: {url}")
            
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    logger.info(f"✅ Found working endpoint: {url}")
                    config = response.json()
                    logger.info(f"   Issuer: {config.get('issuer', 'N/A')}")
                    logger.info(f"   Auth endpoint: {config.get('authorization_endpoint', 'N/A')}")
                    working_endpoints.append((url, config))
                else:
                    logger.info(f"❌ {response.status_code} - {url}")
            except Exception as e:
                logger.info(f"❌ Error - {url}: {e}")
    
    if working_endpoints:
        logger.info("\n🎉 Found working OIDC endpoints:")
        for url, config in working_endpoints:
            logger.info(f"📍 {url}")
            logger.info(f"   Issuer: {config.get('issuer')}")
            logger.info(f"   Auth: {config.get('authorization_endpoint')}")
            logger.info(f"   Token: {config.get('token_endpoint')}")
            logger.info(f"   UserInfo: {config.get('userinfo_endpoint')}")
            logger.info(f"   JWKS: {config.get('jwks_uri')}")
            logger.info("")
    else:
        logger.error("❌ No working OIDC endpoints found")
        
        # Test basic connectivity
        logger.info("🔍 Testing basic Authentik connectivity...")
        try:
            response = await client.get(base_url)
            if response.status_code == 200:
                logger.info(f"✅ Base URL accessible: {base_url}")
                logger.info("   Authentik instance is running")
            else:
                logger.error(f"❌ Base URL returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Cannot reach Authentik instance: {e}")
        
        # Suggest next steps
        logger.info("\n📝 Next steps:")
        logger.info("1. Check if Authentik application is properly configured")
        logger.info("2. Verify the application slug in Authentik admin")
        logger.info("3. Ensure the OIDC provider is created and linked")
        logger.info("4. Check that the application is accessible")

if __name__ == "__main__":
    asyncio.run(discover_authentik_endpoints())
