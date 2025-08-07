"""
Admin endpoints for managing user databases.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.user import User
from app.db.b2b2c_session import get_contextual_db_session
from app.services.multi_tenant_db_service import multi_tenant_db_service
from app.core.auth_dependencies import get_super_admin_user

router = APIRouter(prefix="/admin/databases", tags=["admin-databases"])

@router.get("/list", response_model=List[Dict[str, Any]])
async def list_user_databases(
    admin_user: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """
    List all user databases with basic information.
    """
    try:
        # Get all users from master database
        users = db.query(User).all()
        
        databases_info = []
        for user in users:
            firebase_uid = getattr(user, 'firebase_uid', None)
            if firebase_uid:
                db_info = await multi_tenant_db_service.get_database_info(firebase_uid)
                created_at = getattr(user, 'created_at', None)
                db_info.update({
                    "user_id": getattr(user, 'id', None),
                    "user_email": getattr(user, 'email', None),
                    "firebase_uid": firebase_uid,
                    "is_active": getattr(user, 'is_active', None),
                    "created_at": created_at.isoformat() if created_at is not None else None
                })
                databases_info.append(db_info)
        
        return databases_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list databases: {str(e)}"
        )

@router.get("/{user_uuid}/info", response_model=Dict[str, Any])
async def get_user_database_info(
    user_uuid: str,
    admin_user: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """
    Get detailed information about a specific user's database.
    """
    try:
        # Get user from master database to get user_id
        user = db.query(User).filter(getattr(User, 'firebase_uid') == user_uuid).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = getattr(user, 'id')
        db_info = await multi_tenant_db_service.get_database_info(user_id)
        return db_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database info: {str(e)}"
        )

@router.post("/{user_uuid}/create")
async def create_user_database(
    user_uuid: str,
    admin_user: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """
    Manually create a database for a user.
    """
    try:
        # Get user from master database
        user = db.query(User).filter(getattr(User, 'firebase_uid') == user_uuid).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create database
        success = await multi_tenant_db_service.create_user_database(user)
        
        if success:
            return {"message": f"Database created successfully for user {user_uuid}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create database"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create database: {str(e)}"
        )

@router.post("/{user_uuid}/backup")
async def backup_user_database(
    user_uuid: str,
    background_tasks: BackgroundTasks,
    backup_path: Optional[str] = None,
    admin_user: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """
    Create a backup of a user's database.
    """
    try:
        # Get user from master database to get user_id
        user = db.query(User).filter(getattr(User, 'firebase_uid') == user_uuid).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = getattr(user, 'id')
        
        if not backup_path:
            # Generate default backup path
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"/tmp/sonicus_backup_{user_uuid}_{timestamp}.sql"
        
        # Run backup in background
        background_tasks.add_task(
            multi_tenant_db_service.backup_user_database,
            user_id,
            backup_path
        )
        
        return {
            "message": f"Backup started for user {user_uuid}",
            "backup_path": backup_path
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start backup: {str(e)}"
        )

@router.delete("/{user_uuid}/delete")
async def delete_user_database(
    user_uuid: str,
    confirm: bool = False,
    admin_user: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """
    Delete a user's database (DANGEROUS - requires confirmation).
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database deletion requires confirmation. Set confirm=true"
        )
    
    try:
        # Get user from master database to get user_id
        user = db.query(User).filter(getattr(User, 'firebase_uid') == user_uuid).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = getattr(user, 'id')
        success = await multi_tenant_db_service.delete_user_database(user_id)
        
        if success:
            return {"message": f"Database deleted successfully for user {user_uuid}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete database"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete database: {str(e)}"
        )

@router.get("/health")
async def database_health_check(
    admin_user: User = Depends(get_super_admin_user)
):
    """
    Check health of database system.
    """
    try:
        # Test master database connection
        master_engine = multi_tenant_db_service.master_engine
        
        with master_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            master_healthy = result.fetchone() is not None
        
        return {
            "master_database": "healthy" if master_healthy else "unhealthy",
            "multi_tenant_service": "operational",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "master_database": "unhealthy",
            "multi_tenant_service": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
