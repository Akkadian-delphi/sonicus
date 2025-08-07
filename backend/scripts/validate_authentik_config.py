#!/usr/bin/env python3
"""
Authentik Configuration Validator for Sonicus Platform

This script helps validate your Authentik configuration and test the OIDC flow.
"""

import asyncio
import httpx
import json
import os
from urllib.parse import urlencode

class AuthentikConfigValidator:
    def __init__(self):
        self.base_url = os.getenv("AUTHENTIK_BASE_URL", "https://authentik.elefefe.eu")
        self.client_id = os.getenv("AUTHENTIK_CLIENT_ID")
        self.client_secret = os.getenv("AUTHENTIK_CLIENT_SECRET")
        self.redirect_uri = os.getenv("AUTHENTIK_REDIRECT_URI", "http://localhost:3000/auth/callback")
    
    async def test_oidc_discovery(self):
        """Test OIDC discovery endpoint"""
        print("🔍 Testing OIDC Discovery...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/application/o/.well-known/openid_configuration")
                
                if response.status_code == 200:
                    config = response.json()
                    print("✅ OIDC Discovery successful!")
                    print(f"   Authorization Endpoint: {config.get('authorization_endpoint')}")
                    print(f"   Token Endpoint: {config.get('token_endpoint')}")
                    print(f"   UserInfo Endpoint: {config.get('userinfo_endpoint')}")
                    print(f"   JWKS URI: {config.get('jwks_uri')}")
                    return config
                else:
                    print(f"❌ OIDC Discovery failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ OIDC Discovery error: {e}")
            return None
    
    async def test_jwks_endpoint(self, config):
        """Test JWKS endpoint"""
        print("\n🔑 Testing JWKS Endpoint...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(config["jwks_uri"])
                
                if response.status_code == 200:
                    jwks = response.json()
                    print("✅ JWKS endpoint accessible!")
                    print(f"   Number of keys: {len(jwks.get('keys', []))}")
                    return True
                else:
                    print(f"❌ JWKS endpoint failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ JWKS endpoint error: {e}")
            return False
    
    def generate_auth_url(self, config):
        """Generate authorization URL"""
        print("\n🚀 Generating Authorization URL...")
        
        if not config:
            print("❌ Cannot generate auth URL without OIDC config")
            return None
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email groups",
            "state": "test-state-123"
        }
        
        auth_url = f"{config['authorization_endpoint']}?{urlencode(params)}"
        print("✅ Authorization URL generated!")
        print(f"   URL: {auth_url}")
        print("\n📋 Next Steps:")
        print("   1. Copy the URL above")
        print("   2. Open it in your browser")
        print("   3. Login with your Authentik credentials")
        print("   4. You should be redirected to your callback URL with a code parameter")
        
        return auth_url
    
    def validate_environment(self):
        """Validate environment variables"""
        print("🔧 Validating Environment Variables...")
        
        required_vars = {
            "AUTHENTIK_BASE_URL": self.base_url,
            "AUTHENTIK_CLIENT_ID": self.client_id,
            "AUTHENTIK_CLIENT_SECRET": self.client_secret,
            "AUTHENTIK_REDIRECT_URI": self.redirect_uri
        }
        
        missing_vars = []
        
        for var_name, var_value in required_vars.items():
            if not var_value or var_value.startswith("your-"):
                missing_vars.append(var_name)
                print(f"❌ {var_name}: Not configured")
            else:
                # Mask sensitive values
                display_value = var_value
                if "secret" in var_name.lower() or "password" in var_name.lower():
                    display_value = "*" * len(var_value)
                print(f"✅ {var_name}: {display_value}")
        
        if missing_vars:
            print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("   Please update your .env file with the correct values")
            return False
        else:
            print("✅ All environment variables configured!")
            return True
    
    async def run_validation(self):
        """Run complete validation"""
        print("🎯 Authentik Configuration Validation for Sonicus Platform")
        print("=" * 60)
        
        # Check environment variables
        if not self.validate_environment():
            return False
        
        # Test OIDC discovery
        config = await self.test_oidc_discovery()
        if not config:
            return False
        
        # Test JWKS endpoint
        jwks_ok = await self.test_jwks_endpoint(config)
        if not jwks_ok:
            return False
        
        # Generate auth URL for testing
        self.generate_auth_url(config)
        
        print("\n🎉 Authentik configuration validation completed!")
        print("   Your Authentik integration is ready for testing.")
        
        return True

async def main():
    """Main function"""
    # Load environment variables from .env file if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📄 Loaded environment variables from .env file")
    except ImportError:
        print("📄 python-dotenv not installed, reading from environment")
    
    validator = AuthentikConfigValidator()
    await validator.run_validation()

if __name__ == "__main__":
    asyncio.run(main())
