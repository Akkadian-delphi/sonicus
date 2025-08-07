#!/usr/bin/env python3
"""
Quick OIDC Test Script

Run this immediately after completing the Authentik OIDC configuration.
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def quick_oidc_test():
    """Quick test to verify OIDC configuration is working"""
    
    logger.info("🚀 Quick OIDC Configuration Test")
    logger.info("="*50)
    
    base_url = "https://veritas.elefefe.eu"
    app_slug = "sonicus-platform"
    
    # Expected endpoint
    discovery_url = f"{base_url}/application/o/{app_slug}/.well-known/openid_configuration"
    
    logger.info(f"Testing: {discovery_url}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(discovery_url)
            
            if response.status_code == 200:
                config = response.json()
                logger.info("🎉 SUCCESS! OIDC configuration is working!")
                logger.info("")
                logger.info("📍 Discovered endpoints:")
                logger.info(f"   Issuer: {config.get('issuer')}")
                logger.info(f"   Authorization: {config.get('authorization_endpoint')}")
                logger.info(f"   Token: {config.get('token_endpoint')}")
                logger.info(f"   UserInfo: {config.get('userinfo_endpoint')}")
                logger.info(f"   JWKS: {config.get('jwks_uri')}")
                
                # Test JWKS endpoint
                jwks_uri = config.get('jwks_uri')
                if jwks_uri:
                    logger.info("")
                    logger.info("🔑 Testing JWKS endpoint...")
                    jwks_response = await client.get(jwks_uri)
                    if jwks_response.status_code == 200:
                        jwks = jwks_response.json()
                        key_count = len(jwks.get('keys', []))
                        logger.info(f"✅ JWKS works! Found {key_count} keys")
                    else:
                        logger.warning(f"⚠️ JWKS endpoint issue: {jwks_response.status_code}")
                
                logger.info("")
                logger.info("🚀 Ready to run full test suite:")
                logger.info("   python3 scripts/setup_authentik_dev.py")
                logger.info("   python3 scripts/test_authentik_flow.py")
                
                return True
                
            elif response.status_code == 404:
                logger.error("❌ OIDC endpoint still returns 404")
                logger.error("")
                logger.error("🔧 Configuration issue - please check:")
                logger.error("1. Provider is created in Authentik")
                logger.error("2. Application is created with slug 'sonicus-platform'")
                logger.error("3. Application is linked to the provider")
                logger.error("4. Both provider and application are active")
                logger.error("")
                logger.error("📝 See: OIDC_CONFIGURATION_NEEDED.md")
                return False
                
            else:
                logger.error(f"❌ Unexpected response: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}...")
                return False
                
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_oidc_test())
    print("\n" + "="*50)
    if success:
        print("🎉 OIDC configuration is complete and working!")
    else:
        print("❌ OIDC configuration needs attention.")
        print("📖 See OIDC_CONFIGURATION_NEEDED.md for detailed steps.")
    
    exit(0 if success else 1)
