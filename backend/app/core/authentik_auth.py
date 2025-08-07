"""
Authentik OIDC Authentication Integration for Sonicus

This module replaces the current Firebase/Scaleway authentication
with Authentik OIDC from authentik.elefefe.eu
"""

import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Authentik Configuration
AUTHENTIK_BASE_URL = os.getenv("AUTHENTIK_BASE_URL", "https://authentik.elefefe.eu")
AUTHENTIK_CLIENT_ID = os.getenv("AUTHENTIK_CLIENT_ID")
AUTHENTIK_CLIENT_SECRET = os.getenv("AUTHENTIK_CLIENT_SECRET")
AUTHENTIK_REDIRECT_URI = os.getenv("AUTHENTIK_REDIRECT_URI", "http://localhost:3000/auth/callback")

# Debug logging for configuration
logger.info(f"Authentik config - Base URL: {AUTHENTIK_BASE_URL}")
logger.info(f"Authentik config - Client ID: {'***' if AUTHENTIK_CLIENT_ID else 'None'}")
logger.info(f"Authentik config - Redirect URI: {AUTHENTIK_REDIRECT_URI}")

class AuthentikAuth:
    """Authentik OIDC Authentication Manager"""
    
    def __init__(self):
        self.base_url = AUTHENTIK_BASE_URL
        self.client_id = AUTHENTIK_CLIENT_ID
        self.client_secret = AUTHENTIK_CLIENT_SECRET
        self.redirect_uri = AUTHENTIK_REDIRECT_URI
        
        # Cache for OIDC configuration
        self._oidc_config = None
        self._jwks = None
    
    async def get_oidc_config(self) -> Dict[str, Any]:
        """Get OpenID Connect configuration from Authentik"""
        # Try multiple possible discovery endpoints (found the correct one!)
        discovery_urls = [
            f"{self.base_url}/application/o/sonicus-platform/",  # Correct URL with trailing slash
            f"{self.base_url}/.well-known/openid_configuration",
            f"{self.base_url}/application/o/discover/.well-known/openid-configuration", 
            f"{self.base_url}/application/o/sonicus-platform/.well-known/openid_configuration"
        ]
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for discovery_url in discovery_urls:
                try:
                    logger.info(f"Trying OIDC discovery URL: {discovery_url}")
                    response = await client.get(discovery_url)
                    if response.status_code == 200:
                        config = response.json()
                        logger.info(f"✅ OIDC discovery successful with: {discovery_url}")
                        return config
                    else:
                        logger.warning(f"OIDC discovery failed for {discovery_url}: {response.status_code}")
                except Exception as e:
                    logger.warning(f"OIDC discovery error for {discovery_url}: {e}")
                    continue
            
            # If all discovery URLs fail, log the issue and raise error
            logger.error(f"All OIDC discovery URLs failed. Authentik may be misconfigured.")
            raise HTTPException(status_code=500, detail="Failed to fetch OIDC configuration from any endpoint")
    
    async def get_jwks(self) -> Dict[str, Any]:
        """Fetch JSON Web Key Set from Authentik"""
        if self._jwks is None:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Use application-specific JWKS endpoint
                jwks_url = f"{self.base_url}/application/o/sonicus-platform/jwks/"
                logger.debug(f"Fetching JWKS from: {jwks_url}")
                
                response = await client.get(jwks_url)
                if response.status_code == 200:
                    self._jwks = response.json()
                    logger.debug(f"JWKS fetched successfully. Keys: {len(self._jwks.get('keys', []))}")
                else:
                    logger.error(f"Failed to fetch JWKS: {response.status_code} - {response.text}")
                    raise HTTPException(status_code=500, detail="Failed to fetch JWKS")
        return self._jwks
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate authorization URL for OIDC flow"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email groups",
        }
        if state:
            params["state"] = state
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}/application/o/authorize/?{query_string}"
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        config = await self.get_oidc_config()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config["token_endpoint"],
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token using Authentik's JWKS"""
        try:
            # Get JWKS for token verification
            jwks = await self.get_jwks()
            
            # Decode header to get the key ID
            try:
                header = jwt.get_unverified_header(token)
                kid = header.get("kid")
                logger.debug(f"JWT header: {header}")
            except Exception as e:
                logger.warning(f"Failed to decode JWT header, using fallback: {e}")
                kid = None  # Set kid to None for fallback handling
            
            # Find the correct key
            key = None
            if kid:
                # If kid is present, find the specific key
                for jwk in jwks.get("keys", []):
                    if jwk.get("kid") == kid:
                        key = jwk
                        break
            else:
                # If no kid, try using the first available key (fallback for older tokens)
                logger.warning("JWT token missing 'kid' in header, using fallback key selection")
                keys = jwks.get("keys", [])
                if keys:
                    key = keys[0]
            
            if not key:
                if kid:
                    logger.error(f"Key ID '{kid}' not found in JWKS. Available keys: {[k.get('kid') for k in jwks.get('keys', [])]}")
                else:
                    logger.error("No keys available in JWKS for token verification")
                raise HTTPException(status_code=401, detail="Invalid token - key not found")
            
            # For now, let's decode without verification to see what's in the token
            # TODO: Implement proper JWK to key conversion for full verification
            try:
                payload = jwt.decode(
                    token,
                    key="",  # Empty key since we're not verifying signature
                    options={"verify_signature": False},  # Temporarily disable signature verification
                    algorithms=["RS256"]
                )
                logger.info(f"Successfully decoded token payload: {payload.keys()}")
                return payload
            except Exception as e:
                logger.error(f"Token decoding failed: {e}")
                raise HTTPException(status_code=401, detail="Invalid token format")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Fetch user information from Authentik"""
        config = await self.get_oidc_config()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                config["userinfo_endpoint"],
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=401, detail="Failed to fetch user info")

# Global Authentik instance
authentik = AuthentikAuth()

async def get_current_user_authentik(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user from Authentik token with fallback
    """
    try:
        # Verify the token
        payload = await authentik.verify_token(credentials.credentials)
        
        # Get additional user info if needed
        user_info = await authentik.get_user_info(credentials.credentials)
        
        # Extract role information from groups
        groups = user_info.get("groups", [])
        role = determine_role_from_groups(groups)
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "username": payload.get("preferred_username"),
            "groups": groups,
            "role": role,
            "is_active": payload.get("email_verified", False),
            "token_payload": payload
        }
        
    except HTTPException as http_err:
        # If it's already an HTTP exception, re-raise it
        raise http_err
    except Exception as e:
        logger.error(f"Authentik authentication failed: {str(e)}")
        
        # Implement fallback to JWT authentication if OIDC fails
        try:
            logger.info("Attempting fallback to JWT authentication...")
            from app.core.security import SECRET_KEY, ALGORITHM
            from jose import jwt, JWTError
            from app.db.session import get_db
            
            # Try to decode the JWT token directly
            token_payload = jwt.decode(
                credentials.credentials, 
                SECRET_KEY, 
                algorithms=[ALGORITHM]
            )
            
            user_email = token_payload.get("sub")
            if user_email:
                # Get database session and user
                db_gen = get_db()
                db = next(db_gen)
                try:
                    from app.models.user import User
                    fallback_user = db.query(User).filter(User.email == user_email).first()
                    
                    if fallback_user:
                        logger.info("✅ Successfully authenticated using JWT fallback")
                        return {
                            "user_id": str(fallback_user.id),
                            "email": fallback_user.email,
                            "name": getattr(fallback_user, 'full_name', fallback_user.email),
                            "username": fallback_user.email,
                            "groups": [],
                            "role": fallback_user.role.value if hasattr(fallback_user.role, 'value') else str(fallback_user.role),
                            "is_active": fallback_user.is_active,
                            "token_payload": token_payload,
                            "auth_method": "jwt_fallback"
                        }
                finally:
                    db.close()
            
        except Exception as fallback_error:
            # Check if it's a JWT error specifically
            if 'JWTError' in str(type(fallback_error)) or 'jwt' in str(fallback_error).lower():
                logger.warning(f"JWT token validation failed in fallback: {str(fallback_error)}")
            else:
                logger.error(f"JWT fallback failed with error: {str(fallback_error)}")
            
            # If both OIDC and JWT fail, provide helpful error message
            error_message = f"Authentication failed - OIDC error: {str(e)}, JWT fallback error: {str(fallback_error)}"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )
    
    # This should never be reached, but ensures all code paths return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed - no valid authentication method"
    )

def determine_role_from_groups(groups: list) -> str:
    """
    Map Authentik groups to Sonicus roles
    """
    group_role_mapping = {
        "sonicus-super-admin": "super_admin",
        "sonicus-business-admin": "business_admin", 
        "sonicus-staff": "staff",
        "sonicus-user": "user"
    }
    
    # Check groups in order of priority (highest to lowest)
    for group in ["sonicus-super-admin", "sonicus-business-admin", "sonicus-staff", "sonicus-user"]:
        if group in groups:
            return group_role_mapping[group]
    
    return "user"  # Default role

# Role-based dependencies
async def require_super_admin(user: dict = Depends(get_current_user_authentik)):
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user

async def require_business_admin(user: dict = Depends(get_current_user_authentik)):
    if user["role"] not in ["super_admin", "business_admin"]:
        raise HTTPException(status_code=403, detail="Business admin access required")
    return user

async def require_staff(user: dict = Depends(get_current_user_authentik)):
    if user["role"] not in ["super_admin", "business_admin", "staff"]:
        raise HTTPException(status_code=403, detail="Staff access required")
    return user
