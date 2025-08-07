#!/usr/bin/env python3
"""
Extended Authentik Discovery Script

This script checks for existing applications and providers in Authentik.
"""

import asyncio
import httpx
import logging
import json
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def comprehensive_authentik_discovery():
    """Comprehensive discovery of Authentik configuration"""
    base_url = "https://authentik.elefefe.eu"
    
    logger.info("🔍 Comprehensive Authentik discovery...")
    
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
        
        # Test 1: Basic connectivity
        logger.info(f"\n1️⃣ Testing basic connectivity to {base_url}")
        try:
            response = await client.get(base_url)
            logger.info(f"✅ Base URL accessible: {response.status_code}")
            if "authentik" in response.text.lower():
                logger.info("✅ Confirmed: This is an Authentik instance")
            else:
                logger.warning("⚠️ May not be an Authentik instance")
        except Exception as e:
            logger.error(f"❌ Cannot reach base URL: {e}")
            return False
        
        # Test 2: Check admin interface
        logger.info(f"\n2️⃣ Testing admin interface accessibility")
        admin_url = f"{base_url}/if/admin/"
        try:
            response = await client.get(admin_url)
            logger.info(f"✅ Admin interface: {response.status_code}")
            if response.status_code in [200, 302]:
                logger.info("✅ Admin interface is accessible")
            else:
                logger.warning(f"⚠️ Admin interface returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Cannot reach admin interface: {e}")
        
        # Test 3: Try different OIDC patterns
        logger.info(f"\n3️⃣ Testing OIDC discovery patterns")
        
        # Common Authentik application patterns
        test_patterns = [
            # Standard patterns
            "/application/o/.well-known/openid_configuration",
            
            # Potential application slugs based on your setup
            "/application/o/sonicus-platform/.well-known/openid_configuration",
            "/application/o/sonicus/.well-known/openid_configuration",
            "/application/o/elefefe/.well-known/openid_configuration",
            "/application/o/default/.well-known/openid_configuration",
            
            # Alternative patterns
            "/.well-known/openid_configuration",
            "/api/v3/.well-known/openid_configuration",
            "/application/.well-known/openid_configuration",
            
            # Check if it's using a different path structure
            "/auth/realms/master/.well-known/openid_configuration",
            "/realms/master/.well-known/openid_configuration",
        ]
        
        working_configs = []
        
        for pattern in test_patterns:
            url = f"{base_url}{pattern}"
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    try:
                        config = response.json()
                        if 'issuer' in config and 'authorization_endpoint' in config:
                            logger.info(f"✅ Found OIDC config: {pattern}")
                            logger.info(f"   Issuer: {config.get('issuer')}")
                            working_configs.append((pattern, config))
                        else:
                            logger.info(f"⚠️ Invalid OIDC config: {pattern}")
                    except json.JSONDecodeError:
                        logger.info(f"⚠️ Non-JSON response: {pattern}")
                elif response.status_code == 404:
                    logger.debug(f"❌ 404: {pattern}")
                else:
                    logger.info(f"⚠️ {response.status_code}: {pattern}")
            except Exception as e:
                logger.debug(f"❌ Error {pattern}: {e}")
        
        # Test 4: API endpoints discovery
        logger.info(f"\n4️⃣ Testing API endpoints")
        api_endpoints = [
            "/api/v3/core/applications/",
            "/api/v3/providers/oauth2/",
            "/api/v3/core/users/",
            "/api/",
        ]
        
        for endpoint in api_endpoints:
            url = f"{base_url}{endpoint}"
            try:
                response = await client.get(url)
                if response.status_code in [200, 401, 403]:  # 401/403 means endpoint exists but needs auth
                    logger.info(f"✅ API endpoint exists: {endpoint} ({response.status_code})")
                elif response.status_code == 404:
                    logger.debug(f"❌ Not found: {endpoint}")
                else:
                    logger.info(f"⚠️ {response.status_code}: {endpoint}")
            except Exception as e:
                logger.debug(f"❌ Error {endpoint}: {e}")
        
        # Test 5: Flow endpoints (Authentik uses flows for auth)
        logger.info(f"\n5️⃣ Testing flow endpoints")
        flow_endpoints = [
            "/flows/",
            "/if/flow/",
            "/auth/",
        ]
        
        for endpoint in flow_endpoints:
            url = f"{base_url}{endpoint}"
            try:
                response = await client.get(url)
                if response.status_code in [200, 302, 401, 403]:
                    logger.info(f"✅ Flow endpoint accessible: {endpoint} ({response.status_code})")
            except Exception as e:
                logger.debug(f"❌ Error {endpoint}: {e}")
        
        # Summary
        logger.info(f"\n" + "="*60)
        logger.info("📊 DISCOVERY SUMMARY")
        logger.info(f"="*60)
        
        if working_configs:
            logger.info("🎉 Found working OIDC configurations:")
            for pattern, config in working_configs:
                logger.info(f"📍 Pattern: {pattern}")
                logger.info(f"   Issuer: {config.get('issuer')}")
                logger.info(f"   Auth endpoint: {config.get('authorization_endpoint')}")
                logger.info(f"   Token endpoint: {config.get('token_endpoint')}")
                logger.info(f"   UserInfo endpoint: {config.get('userinfo_endpoint')}")
                logger.info(f"   JWKS URI: {config.get('jwks_uri')}")
                logger.info("")
            return True
        else:
            logger.error("❌ No OIDC configurations found")
            logger.info("\n💡 Possible issues:")
            logger.info("1. OIDC Provider not created in Authentik")
            logger.info("2. Application not created or not linked to provider")
            logger.info("3. Application slug is different than expected")
            logger.info("4. Provider is not properly configured")
            logger.info("\n🔧 Next steps:")
            logger.info("1. Access Authentik admin: https://authentik.elefefe.eu/if/admin/")
            logger.info("2. Check Applications → Providers (should have an OIDC provider)")
            logger.info("3. Check Applications → Applications (should have Sonicus app)")
            logger.info("4. Verify the application slug matches our expectations")
            logger.info("5. Ensure the provider is properly linked to the application")
            return False

if __name__ == "__main__":
    success = asyncio.run(comprehensive_authentik_discovery())
    exit(0 if success else 1)
