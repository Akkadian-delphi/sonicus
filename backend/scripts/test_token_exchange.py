#!/usr/bin/env python3
"""
Token Exchange Test Script

Use this script to test token exchange after getting an authorization code
from the manual login flow.

Usage: python scripts/test_token_exchange.py [authorization_code]
"""

import os
import sys
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_token_exchange(auth_code: str):
    """Test token exchange with authorization code"""
    logger.info("🔄 Testing token exchange...")
    
    try:
        from app.core.authentik_auth import AuthentikAuth
        
        auth = AuthentikAuth()
        
        # Exchange code for tokens
        tokens = await auth.exchange_code_for_tokens(auth_code)
        
        logger.info("✅ Token exchange successful!")
        logger.info(f"   Access token: {tokens.get('access_token', 'N/A')[:30]}...")
        logger.info(f"   Token type: {tokens.get('token_type', 'N/A')}")
        logger.info(f"   Expires in: {tokens.get('expires_in', 'N/A')} seconds")
        
        # Get user info
        if 'access_token' in tokens:
            user_info = await auth.get_user_info(tokens['access_token'])
            
            logger.info("👤 User information:")
            logger.info(f"   Subject: {user_info.get('sub', 'N/A')}")
            logger.info(f"   Email: {user_info.get('email', 'N/A')}")
            logger.info(f"   Name: {user_info.get('name', 'N/A')}")
            logger.info(f"   Groups: {user_info.get('groups', [])}")
            
            # Test role mapping
            from app.core.authentik_auth import determine_role_from_groups
            role = determine_role_from_groups(user_info.get('groups', []))
            logger.info(f"   Mapped role: {role}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Token exchange failed: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        logger.error("Usage: python scripts/test_token_exchange.py [authorization_code]")
        logger.info("Get the authorization code by:")
        logger.info("1. Run: python scripts/test_authentik_flow.py")
        logger.info("2. Open the generated auth URL in browser")
        logger.info("3. Login and copy the 'code' parameter from callback URL")
        return 1
    
    auth_code = sys.argv[1]
    logger.info(f"Testing token exchange with code: {auth_code[:20]}...")
    
    success = asyncio.run(test_token_exchange(auth_code))
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
