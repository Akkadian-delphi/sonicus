"""
Token-based Authentication Dependencies

Alternative authentication dependencies that work with JWT tokens directly
instead of SQLAlchemy User models, avoiding FastAPI's type introspection issues.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional, Dict, Any
import logging

from app.models.user import UserRole
from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()


def get_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract JWT token from Authorization header."""
    return credentials.credentials


def decode_jwt_token(token: str = Depends(get_jwt_token)) -> Dict[str, Any]:
    """
    Decode and validate JWT token, returning token payload.
    
    Returns:
        Dict: Token payload containing user information
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]  # Default algorithm
        )
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_token_user_id(payload: Dict[str, Any] = Depends(decode_jwt_token)) -> int:
    """Extract user ID from token payload."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID"
        )
    try:
        return int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )


def get_token_user_email(payload: Dict[str, Any] = Depends(decode_jwt_token)) -> str:
    """Extract user email from token payload."""
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email"
        )
    return str(email)


def get_token_user_role(payload: Dict[str, Any] = Depends(decode_jwt_token)) -> UserRole:
    """Extract user role from token payload."""
    role_str = payload.get("role")
    if not role_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing role"
        )
    
    try:
        return UserRole(role_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid role in token"
        )


def get_token_user_org_id(payload: Dict[str, Any] = Depends(decode_jwt_token)) -> Optional[int]:
    """Extract organization ID from token payload."""
    org_id = payload.get("organization_id")
    if org_id is None:
        return None
    
    try:
        return int(org_id)
    except (ValueError, TypeError):
        return None


def require_admin_role_token(role: UserRole = Depends(get_token_user_role)) -> UserRole:
    """Dependency to require admin role using token-based auth."""
    if role not in [UserRole.SUPER_ADMIN, UserRole.BUSINESS_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return role
