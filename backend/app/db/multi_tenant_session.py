"""
Multi-tenant database session management.
Provides database sessions for user-specific databases.
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.core.firebase_security import get_current_user_firebase
from app.services.multi_tenant_db_service import multi_tenant_db_service

async def get_user_db(
    current_user: User = Depends(get_current_user_firebase)
) -> AsyncGenerator[Session, None]:
    """
    Get database session for the current user's database.
    Creates the database if it doesn't exist.
    """
    firebase_uid = getattr(current_user, 'firebase_uid', None)
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User has no Firebase UID"
        )
    
    # Ensure user database exists
    db_created = await multi_tenant_db_service.create_user_database(current_user)
    if not db_created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create or access user database"
        )
    
    # Get database session
    db = multi_tenant_db_service.get_user_database_session(firebase_uid)
    try:
        yield db
    finally:
        db.close()

async def get_admin_user_db(
    current_user: User = Depends(get_current_user_firebase),
    target_user_uuid: Optional[str] = None
) -> AsyncGenerator[Session, None]:
    """
    Get database session for a specific user (admin only).
    Allows admins to access any user's database.
    """
    # Check if current user is admin
    is_admin = getattr(current_user, 'is_superuser', False)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if not target_user_uuid:
        # If no target specified, use admin's own database
        firebase_uid = getattr(current_user, 'firebase_uid', None)
        if not firebase_uid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User has no Firebase UID"
            )
        target_user_uuid = firebase_uid
    
    # Get database session for target user
    if not target_user_uuid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Target user UUID is required"
        )
    
    db = multi_tenant_db_service.get_user_database_session(target_user_uuid)
    try:
        yield db
    finally:
        db.close()
