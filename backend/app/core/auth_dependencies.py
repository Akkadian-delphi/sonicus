"""
Authentik OIDC Authentication Dependencies

This module provides authentication dependencies that use Authentik OIDC
as the primary authentication method, with proper FastAPI integration.

Key features:
1. Authentik OIDC as primary authentication
2. User synchronization with local database
3. Role-based access control
4. FastAPI-compatible dependencies
"""

import logging
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.session import get_db
from app.core.authentik_auth import get_current_user_authentik, require_super_admin, require_business_admin

logger = logging.getLogger(__name__)


async def get_current_user_compatible(
    user: Dict[str, Any] = Depends(get_current_user_authentik),
    db: Session = Depends(get_db)
):
    """
    Authentik OIDC-compatible authentication dependency.
    
    This function:
    1. Uses Authentik OIDC for authentication
    2. Syncs user with local database
    3. Returns SQLAlchemy User model for compatibility
    
    Args:
        user: Authenticated user data from Authentik
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If authentication fails
    """
    # Import User model locally to avoid FastAPI type introspection
    from app.models.user import User, UserRole
    
    try:
        user_email = user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not found in token",
            )
        
        # Get or create user in local database
        db_user = db.query(User).filter(User.email == user_email).first()
        
        if not db_user:
            # Create new user from Authentik data
            db_user = User(
                email=user_email,
                hashed_password="",  # Not needed for OIDC
                is_active=True,
                is_superuser=user.get("role") == "super_admin",
                role=user.get("role", "user")
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            logger.info(f"Created new user from Authentik: {user_email}")
        else:
            # Update user role if changed in Authentik
            authentik_role = user.get("role", "user")
            if db_user.role != authentik_role:
                db_user.role = authentik_role
                db_user.is_superuser = authentik_role == "super_admin"
                db.commit()
                db.refresh(db_user)
                logger.info(f"Updated user role for {user_email}: {authentik_role}")
        
        if not getattr(db_user, 'is_active', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user account"
            )
        
        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in authentication dependency: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


async def get_admin_user_compatible(
    current_user = Depends(get_current_user_compatible)
):
    """
    Authentik OIDC-compatible admin authentication dependency.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not getattr(current_user, 'is_superuser', False):
        logger.warning(f"Non-admin user {getattr(current_user, 'id', 'unknown')} attempted to access admin endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    return current_user


async def get_active_user_compatible(
    current_user = Depends(get_current_user_compatible)
):
    """
    Authentik OIDC-compatible active user authentication dependency.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If user is not active
    """
    if not getattr(current_user, 'is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user


# Business admin dependency using Authentik role-based access
async def get_business_admin_user(
    user: Dict[str, Any] = Depends(require_business_admin),
    db: Session = Depends(get_db)
):
    """
    Authentik OIDC business admin authentication dependency.
    
    Args:
        user: Authenticated business admin user data from Authentik
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If user is not a business admin
    """
    return await get_current_user_compatible(user, db)


# Super admin dependency using Authentik role-based access  
async def get_super_admin_user(
    user: Dict[str, Any] = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """
    Authentik OIDC super admin authentication dependency.
    
    Args:
        user: Authenticated super admin user data from Authentik
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If user is not a super admin
    """
    return await get_current_user_compatible(user, db)


# Legacy compatibility aliases - now pointing to Authentik OIDC
get_current_user_enhanced = get_current_user_compatible
get_admin_user_enhanced = get_admin_user_compatible
get_current_user = get_current_user_compatible  # Replace core.security dependency
