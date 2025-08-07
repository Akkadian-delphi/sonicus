"""
Authentication Transition Module

This module provides backward compatibility between simple JWT tokens and Authentik OIDC tokens
during the migration period. It will try Authentik first, then fall back to simple JWT.
"""

import logging
from typing import Optional, Dict, Any, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

# Import both authentication systems
from app.core.authentik_auth import get_current_user_authentik, authentik
from app.core.security import get_current_user as get_current_user_jwt
from app.db.session import get_db
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthTransition:
    """Handles the transition between JWT and OIDC authentication"""
    
    def __init__(self):
        self.prefer_oidc = True  # Set to False to prefer JWT during transition
    
    async def authenticate_user(
        self, 
        credentials: HTTPAuthorizationCredentials,
        db: Session
    ) -> Union[User, Dict[str, Any]]:
        """
        Try to authenticate user with both systems
        Returns either a SQLAlchemy User object (JWT) or dict (OIDC)
        """
        token = credentials.credentials
        
        # First, try to determine token type by structure
        if self._is_oidc_token(token):
            logger.debug("Token appears to be OIDC, trying Authentik first")
            try:
                return await self._authenticate_with_oidc(token, db)
            except HTTPException as e:
                logger.warning(f"OIDC authentication failed: {e.detail}")
                if self.prefer_oidc:
                    raise
                # Fall back to JWT
                logger.debug("Falling back to JWT authentication")
                return await self._authenticate_with_jwt(token, db)
        else:
            logger.debug("Token appears to be JWT, trying JWT first")
            try:
                return await self._authenticate_with_jwt(token, db)
            except HTTPException as e:
                logger.warning(f"JWT authentication failed: {e.detail}")
                # Fall back to OIDC
                logger.debug("Falling back to OIDC authentication")
                return await self._authenticate_with_oidc(token, db)
    
    def _is_oidc_token(self, token: str) -> bool:
        """
        Heuristic to determine if token is likely OIDC vs simple JWT
        """
        try:
            import base64
            import json
            
            # Decode header without verification
            header_data = token.split('.')[0]
            # Add padding if needed
            header_data += '=' * (4 - len(header_data) % 4)
            header = json.loads(base64.urlsafe_b64decode(header_data))
            
            # OIDC tokens typically have 'kid' (Key ID) in header
            # Simple JWT tokens from our system may not
            has_kid = 'kid' in header
            
            # Check algorithm - OIDC typically uses RS256
            algorithm = header.get('alg', '')
            is_rs256 = algorithm == 'RS256'
            
            logger.debug(f"Token analysis: has_kid={has_kid}, algorithm={algorithm}")
            
            return has_kid and is_rs256
            
        except Exception as e:
            logger.debug(f"Token analysis failed: {e}")
            return False
    
    async def _authenticate_with_oidc(self, token: str, db: Session) -> Dict[str, Any]:
        """Authenticate using Authentik OIDC"""
        try:
            # Verify token with Authentik
            payload = await authentik.verify_token(token)
            
            # Get additional user info
            user_info = await authentik.get_user_info(token)
            
            # Sync user with local database if needed
            user = await self._sync_oidc_user_to_db(payload, user_info, db)
            
            # Return dict with both OIDC data and local user
            return {
                "auth_type": "oidc",
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "name": user_info.get("name"),
                "username": payload.get("preferred_username"),
                "groups": user_info.get("groups", []),
                "role": self._determine_role_from_groups(user_info.get("groups", [])),
                "is_active": payload.get("email_verified", False),
                "local_user": user,
                "token_payload": payload
            }
            
        except Exception as e:
            logger.error(f"OIDC authentication failed: {e}")
            raise HTTPException(status_code=401, detail="OIDC authentication failed")
    
    async def _authenticate_with_jwt(self, token: str, db: Session) -> User:
        """Authenticate using simple JWT"""
        # Use existing JWT authentication logic
        from app.core.security import get_current_user
        from unittest.mock import MagicMock
        
        # Create a mock Depends object that returns the token
        mock_token_dep = MagicMock(return_value=token)
        mock_db_dep = MagicMock(return_value=db)
        
        # Call the JWT authentication function directly
        try:
            return get_current_user(token=token, db=db)
        except Exception as e:
            logger.error(f"JWT authentication failed: {e}")
            raise HTTPException(status_code=401, detail="JWT authentication failed")
    
    async def _sync_oidc_user_to_db(self, payload: dict, user_info: dict, db: Session) -> Optional[User]:
        """
        Sync OIDC user data with local database
        Create or update user record based on OIDC information
        """
        try:
            email = payload.get("email") or user_info.get("email")
            if not email:
                logger.warning("No email found in OIDC token")
                return None
            
            # Check if user exists
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                # Create new user from OIDC data
                role_name = self._determine_role_from_groups(user_info.get("groups", []))
                user_role = getattr(UserRole, role_name.upper())
                
                user = User(
                    email=email,
                    is_active=payload.get("email_verified", False),
                    role=user_role,
                    # Set other fields as needed
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"Created new user from OIDC: {email}")
            else:
                # Update existing user if needed
                role_name = self._determine_role_from_groups(user_info.get("groups", []))
                expected_role = getattr(UserRole, role_name.upper())
                
                if user.role != expected_role:
                    user.role = expected_role
                    db.commit()
                    logger.info(f"Updated user role from OIDC: {email} -> {role_name}")
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to sync OIDC user to database: {e}")
            return None
    
    def _determine_role_from_groups(self, groups: list) -> str:
        """Map Authentik groups to Sonicus roles"""
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

# Global transition manager
auth_transition = AuthTransition()

async def get_current_user_transition(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Union[User, Dict[str, Any]]:
    """
    FastAPI dependency that supports both JWT and OIDC authentication
    During transition period
    """
    try:
        return await auth_transition.authenticate_user(credentials, db)
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

def check_business_admin_transition(current_user: Union[User, Dict[str, Any]]):
    """Check if user has business admin access (works with both auth types)"""
    if isinstance(current_user, dict):
        # OIDC user
        role = current_user.get("role", "user")
        if role not in ["super_admin", "business_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Business Admin access required"
            )
    else:
        # JWT user (SQLAlchemy User object)
        allowed_roles = [UserRole.BUSINESS_ADMIN, UserRole.SUPER_ADMIN]
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Business Admin access required"
            )

def get_business_admin_user_transition(
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_user_transition)
):
    """Get current user and validate business admin access (transition compatible)"""
    check_business_admin_transition(current_user)
    return current_user
