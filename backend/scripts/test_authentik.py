#!/usr/bin/env python3
"""
Test script for Authentik authentication module
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, '.')

from app.core.authentik_auth import authentik

async def test_authentik_auth():
    """Test the Authentik authentication module"""
    print('🔍 Testing Authentik Auth Module')
    print('=' * 50)
    print(f'Base URL: {authentik.base_url}')
    print(f'Client ID: {"✓ Set" if authentik.client_id else "❌ Missing"}')
    print(f'Redirect URI: {authentik.redirect_uri}')
    print()
    
    try:
        print('📋 Testing OIDC Discovery...')
        config = await authentik.get_oidc_config()
        print('✅ OIDC Discovery successful!')
        print(f'   Issuer: {config.get("issuer", "N/A")}')
        print(f'   Auth endpoint: {config.get("authorization_endpoint", "N/A")}')
        print(f'   Token endpoint: {config.get("token_endpoint", "N/A")}')
        print(f'   UserInfo endpoint: {config.get("userinfo_endpoint", "N/A")}')
        print(f'   JWKS URI: {config.get("jwks_uri", "N/A")}')
        print()
        
        print('🔑 Testing JWKS endpoint...')
        jwks = await authentik.get_jwks()
        print(f'✅ JWKS successful! Found {len(jwks.get("keys", []))} keys')
        
        # Show key details
        for i, key in enumerate(jwks.get("keys", [])[:2]):  # Show first 2 keys
            print(f'   Key {i+1}: {key.get("kty")} - {key.get("use")} - {key.get("kid", "no kid")}')
        print()
        
        print('🔗 Testing authorization URL generation...')
        auth_url = authentik.get_authorization_url('test-state')
        print('✅ Authorization URL generated successfully')
        print(f'   URL: {auth_url[:80]}...')
        print()
        
        print('🎉 All Authentik tests passed!')
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_authentik_auth())
    sys.exit(0 if success else 1)
