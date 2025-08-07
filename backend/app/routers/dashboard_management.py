"""
Dashboard Management API

This module provides management endpoints for the Super Admin dashboard,
including data refresh, cache management, and system monitoring.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_current_user_compatible
from app.models.user import User, UserRole
from app.db.session import get_db
from app.services.dashboard_refresh import dashboard_refresh_service
from app.routers.dashboard_websocket import dashboard_ws_manager, send_dashboard_alert
from app.core.redis_caching import advanced_cache
from app.core.error_handling import advanced_logger, ErrorCategory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/super-admin/dashboard/manage", tags=["Dashboard Management"])


async def require_super_admin(current_user: User = Depends(get_current_user_compatible)) -> User:
    """Require Super Admin role for management endpoints."""
    if current_user is None:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
    # Use getattr for safe SQLAlchemy column access
    user_role = getattr(current_user, 'role', None)
    if user_role != UserRole.SUPER_ADMIN:
        advanced_logger.error(
            "Unauthorized dashboard management access",
            category=ErrorCategory.AUTHORIZATION,
            extra={"user_id": getattr(current_user, 'id', 'unknown'), "endpoint": "dashboard_management"}
        )
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
    return current_user


@router.post("/refresh")
async def refresh_dashboard_data(
    background_tasks: BackgroundTasks,
    force: bool = False,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """
    Refresh all dashboard data manually.
    
    Args:
        force: Force refresh even if one is in progress
        background_tasks: FastAPI background tasks
        current_user: Authenticated super admin user
        db: Database session
    """
    try:
        if dashboard_refresh_service.refresh_in_progress and not force:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Dashboard refresh already in progress",
                    "suggestion": "Use force=true to override or wait for current refresh to complete"
                }
            )
        
        # Start refresh in background
        background_tasks.add_task(
            _background_refresh_task,
            db,
            getattr(current_user, 'id', 'unknown')
        )
        
        advanced_logger.info(
            "Dashboard refresh initiated",
            extra={
                "user_id": getattr(current_user, 'id', 'unknown'),
                "force": force
            }
        )
        
        return {
            "success": True,
            "message": "Dashboard refresh initiated",
            "initiated_at": datetime.now().isoformat(),
            "initiated_by": getattr(current_user, 'email', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate dashboard refresh: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate dashboard refresh")


async def _background_refresh_task(db: Session, user_id: str):
    """Background task for dashboard refresh."""
    try:
        result = await dashboard_refresh_service.refresh_all_dashboard_data(db)
        
        # Send success notification
        await send_dashboard_alert({
            "type": "refresh_complete",
            "severity": "info",
            "message": "Dashboard data refresh completed successfully",
            "timestamp": datetime.now().isoformat(),
            "initiated_by": user_id
        })
        
        logger.info(f"Dashboard refresh completed successfully for user {user_id}")
        
    except Exception as e:
        logger.error(f"Background dashboard refresh failed: {e}")
        
        # Send error notification
        await send_dashboard_alert({
            "type": "refresh_failed",
            "severity": "warning",
            "message": f"Dashboard data refresh failed: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "initiated_by": user_id
        })


@router.get("/cache/status")
async def get_cache_status(
    current_user: User = Depends(require_super_admin)
):
    """Get dashboard cache status and statistics."""
    try:
        cache_stats = await dashboard_refresh_service.get_cache_statistics()
        
        return {
            "success": True,
            "cache_statistics": cache_stats,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache status")


@router.post("/cache/clear")
async def clear_dashboard_cache(
    confirm: bool = False,
    current_user: User = Depends(require_super_admin)
):
    """
    Clear all dashboard cache data.
    
    Args:
        confirm: Confirmation flag to prevent accidental clearing
        current_user: Authenticated super admin user
    """
    if not confirm:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Cache clear requires confirmation",
                "suggestion": "Add confirm=true parameter to clear cache"
            }
        )
    
    try:
        result = await dashboard_refresh_service.clear_dashboard_cache()
        
        advanced_logger.info(
            "Dashboard cache cleared",
            extra={
                "user_id": getattr(current_user, 'id', 'unknown'),
                "cleared_keys": result.get("cleared_keys", 0)
            }
        )
        
        # Notify WebSocket connections
        await send_dashboard_alert({
            "type": "cache_cleared",
            "severity": "info",
            "message": "Dashboard cache has been cleared",
            "timestamp": datetime.now().isoformat(),
            "cleared_by": getattr(current_user, 'email', 'unknown')
        })
        
        return {
            "success": True,
            "message": "Dashboard cache cleared successfully",
            "result": result,
            "cleared_at": datetime.now().isoformat(),
            "cleared_by": getattr(current_user, 'email', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Failed to clear dashboard cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear dashboard cache")


@router.get("/websocket/connections")
async def get_websocket_connections(
    current_user: User = Depends(require_super_admin)
):
    """Get active WebSocket connection statistics."""
    try:
        connection_stats = dashboard_ws_manager.get_connection_stats()
        
        return {
            "success": True,
            "websocket_connections": connection_stats,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get WebSocket connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve WebSocket connections")


@router.post("/websocket/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    current_user: User = Depends(require_super_admin)
):
    """
    Broadcast a message to all connected dashboard WebSocket clients.
    
    Args:
        message: Message data to broadcast
        current_user: Authenticated super admin user
    """
    try:
        broadcast_data = {
            "type": "admin_message",
            "timestamp": datetime.now().isoformat(),
            "from": getattr(current_user, 'email', 'unknown'),
            "data": message
        }
        
        await dashboard_ws_manager.broadcast_to_admins(broadcast_data)
        
        advanced_logger.info(
            "Message broadcasted to dashboard clients",
            extra={
                "user_id": getattr(current_user, 'id', 'unknown'),
                "recipients": len(dashboard_ws_manager.active_connections)
            }
        )
        
        return {
            "success": True,
            "message": "Message broadcasted successfully",
            "recipients": len(dashboard_ws_manager.active_connections),
            "broadcasted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")


@router.post("/alert")
async def send_alert(
    alert_data: Dict[str, Any],
    current_user: User = Depends(require_super_admin)
):
    """
    Send an alert notification to all connected dashboard clients.
    
    Args:
        alert_data: Alert data including type, severity, message, etc.
        current_user: Authenticated super admin user
    """
    try:
        # Validate alert data
        required_fields = ["type", "severity", "message"]
        missing_fields = [field for field in required_fields if field not in alert_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required alert fields: {', '.join(missing_fields)}"
            )
        
        # Add metadata
        alert_data.update({
            "timestamp": datetime.now().isoformat(),
            "sent_by": getattr(current_user, 'email', 'unknown'),
            "alert_id": f"alert_{int(datetime.now().timestamp())}"
        })
        
        await send_dashboard_alert(alert_data)
        
        advanced_logger.info(
            "Dashboard alert sent",
            extra={
                "user_id": getattr(current_user, 'id', 'unknown'),
                "alert_type": alert_data.get("type"),
                "severity": alert_data.get("severity")
            }
        )
        
        return {
            "success": True,
            "message": "Alert sent successfully",
            "alert_id": alert_data["alert_id"],
            "sent_at": alert_data["timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to send alert")


@router.get("/health")
async def get_management_health(
    current_user: User = Depends(require_super_admin)
):
    """Get health status of dashboard management components."""
    try:
        health_data = {
            "dashboard_refresh_service": {
                "status": "healthy" if not dashboard_refresh_service.refresh_in_progress else "busy",
                "refresh_in_progress": dashboard_refresh_service.refresh_in_progress
            },
            "websocket_manager": {
                "status": "healthy",
                "active_connections": len(dashboard_ws_manager.active_connections),
                "admin_connections": len([
                    uid for uid, meta in dashboard_ws_manager.connection_metadata.items()
                    if meta.get("role") == UserRole.SUPER_ADMIN
                ])
            },
            "cache_system": {
                "status": "healthy",  # Could add actual Redis health check
                "namespace": "dashboard"
            }
        }
        
        # Calculate overall health
        all_healthy = all(
            component["status"] == "healthy" 
            for component in health_data.values()
        )
        
        return {
            "success": True,
            "overall_status": "healthy" if all_healthy else "degraded",
            "components": health_data,
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get management health: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health status")


@router.get("/stats")
async def get_management_stats(
    current_user: User = Depends(require_super_admin)
):
    """Get dashboard management statistics and metrics."""
    try:
        # Get cache statistics
        cache_stats = await dashboard_refresh_service.get_cache_statistics()
        
        # Get WebSocket statistics
        ws_stats = dashboard_ws_manager.get_connection_stats()
        
        stats = {
            "cache_statistics": cache_stats,
            "websocket_statistics": ws_stats,
            "refresh_service": {
                "refresh_in_progress": dashboard_refresh_service.refresh_in_progress,
                "default_ttl": dashboard_refresh_service.default_ttl
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get management stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve management statistics")
