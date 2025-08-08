"""
Authentik Authentication Router for Sonicus

Handles OIDC authentication flow with Authentik
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import logging
import secrets

from app.core.authentik_auth import authentik, get_current_user_authentik
from app.db.session import get_db
from app.models.user import User, UserRole
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])

class AuthCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
    role: str

@router.get("/login")
async def initiate_login():
    """
    Initiate OIDC login flow with Authentik
    """
    state = secrets.token_urlsafe(32)
    authorization_url = authentik.get_authorization_url(state)
    
    return {
        "authorization_url": authorization_url,
        "state": state
    }

@router.post("/callback", response_model=LoginResponse)
async def auth_callback(callback_data: AuthCallbackRequest, db: Session = Depends(get_db)):
    """
    Handle OIDC callback and complete authentication
    """
    try:
        # Exchange code for tokens
        tokens = await authentik.exchange_code_for_tokens(callback_data.code)
        
        # Get user info from Authentik
        user_info = await authentik.get_user_info(tokens["access_token"])
        
        # Create or update user in local database
        user = await sync_user_with_database(user_info, db)
        
        # Map groups to role
        groups = user_info.get("groups", [])
        role = determine_role_from_groups(groups)
        
        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", ""),
            expires_in=tokens.get("expires_in", 3600),
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "username": user_info.get("preferred_username"),
                "is_active": user.is_active
            },
            role=role
        )
        
    except Exception as e:
        logger.error(f"Authentication callback failed: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")

@router.get("/me")
async def get_current_user(user: dict = Depends(get_current_user_authentik)):
    """
    Get current authenticated user information
    """
    return {
        "user": user,
        "authenticated": True
    }

@router.post("/logout")
async def logout(user: dict = Depends(get_current_user_authentik)):
    """
    Logout user (token revocation would be handled by frontend)
    """
    # Log the logout event
    logger.info(f"User {user['email']} logged out")
    
    return {"message": "Logged out successfully"}

async def sync_user_with_database(user_info: dict, db: Session) -> User:
    """
    Create or update user in local database based on Authentik user info
    """
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Authentik")
    
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user
        user = User(
            email=email,
            full_name=user_info.get("name", ""),
            is_active=user_info.get("email_verified", True),
            role=UserRole.USER  # Default role, will be overridden by groups
        )
        db.add(user)
    else:
        # Update existing user
        user.full_name = user_info.get("name", user.full_name)
        user.is_active = user_info.get("email_verified", user.is_active)
    
    # Update role based on groups
    groups = user_info.get("groups", [])
    role_enum = determine_role_enum_from_groups(groups)
    setattr(user, 'role', role_enum)
    
    db.commit()
    db.refresh(user)
    
    return user

def determine_role_enum_from_groups(groups: list) -> UserRole:
    """
    Map Authentik groups to Sonicus UserRole enum values
    """
    group_role_mapping = {
        "sonicus-super-admin": UserRole.SUPER_ADMIN,
        "sonicus-business-admin": UserRole.BUSINESS_ADMIN, 
        "sonicus-staff": UserRole.STAFF,
        "sonicus-user": UserRole.USER
    }
    
    # Check groups in order of priority (highest to lowest)
    for group in ["sonicus-super-admin", "sonicus-business-admin", "sonicus-staff", "sonicus-user"]:
        if group in groups:
            return group_role_mapping[group]
    
    return UserRole.USER  # Default role

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
