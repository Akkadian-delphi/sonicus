"""
WebSocket Routes for Real-Time Analytics

FastAPI WebSocket endpoints for real-time analytics data streaming:
- Organization analytics WebSocket
- System-wide analytics WebSocket
- Analytics dashboard integration
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
import logging

from app.db.session import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from app.services.websocket_analytics import (
    websocket_handler, 
    connection_manager,
    RealTimeAnalyticsBroadcaster
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


def verify_websocket_token(token: str) -> dict:
    """Verify JWT token for WebSocket connections."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")


@router.websocket("/ws/analytics/{organization_id}")
async def websocket_organization_analytics(
    websocket: WebSocket,
    organization_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time organization analytics.
    
    Provides:
    - Real-time usage metrics
    - Live engagement updates
    - Health score alerts
    - Revenue notifications
    
    Authentication via token parameter or query string.
    """
    user_id = None
    
    # Optional authentication - if token provided, verify it
    if token:
        try:
            payload = verify_websocket_token(token)
            user_id = payload.get("sub")
            
            # Verify user has access to this organization
            # Note: Would implement proper authorization check here
            logger.info(f"Authenticated WebSocket connection for user {user_id}, org {organization_id}")
            
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    # Handle the WebSocket connection
    await websocket_handler.handle_websocket_connection(
        websocket=websocket,
        organization_id=organization_id,
        user_id=user_id,
        db=db
    )


@router.websocket("/ws/system-analytics")
async def websocket_system_analytics(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for system-wide analytics (Super Admin only).
    
    Provides:
    - Platform-wide metrics
    - System health status
    - Multi-organization analytics
    - Performance monitoring
    """
    user_id = None
    is_super_admin = False
    
    # Authentication required for system analytics
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        payload = verify_websocket_token(token)
        user_id = payload.get("sub")
        user_role = payload.get("role", "")
        
        # Verify super admin access
        is_super_admin = user_role == "super_admin"
        if not is_super_admin:
            logger.warning(f"Non-admin user {user_id} attempted system analytics WebSocket")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        logger.info(f"Super admin WebSocket connection for user {user_id}")
        
    except Exception as e:
        logger.warning(f"System analytics WebSocket authentication failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Handle system-wide analytics connection
    await websocket_handler.handle_websocket_connection(
        websocket=websocket,
        organization_id="__system__",  # Special organization ID for system metrics
        user_id=user_id,
        db=db
    )


# Regular HTTP endpoints for WebSocket management
@router.get("/analytics/connections/status")
async def get_websocket_status():
    """Get current WebSocket connection status."""
    return {
        "total_connections": connection_manager.get_total_connections(),
        "connected_organizations": connection_manager.get_connected_organizations(),
        "organization_counts": {
            org_id: connection_manager.get_organization_connection_count(org_id)
            for org_id in connection_manager.get_connected_organizations()
        }
    }


@router.post("/analytics/broadcast/{organization_id}")
async def trigger_analytics_broadcast(
    organization_id: str,
    message_type: str = "usage_update",
    db: Session = Depends(get_db)
):
    """
    Manually trigger analytics broadcast to organization.
    Useful for testing or forced updates.
    """
    try:
        broadcaster = RealTimeAnalyticsBroadcaster(db)
        
        if message_type == "usage_update":
            await broadcaster.broadcast_usage_update(organization_id)
        elif message_type == "engagement_update":
            await broadcaster.broadcast_engagement_update(organization_id)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown message type: {message_type}"
            )
        
        return {
            "message": f"Broadcast triggered for organization {organization_id}",
            "type": message_type,
            "connections_notified": connection_manager.get_organization_connection_count(organization_id)
        }
        
    except Exception as e:
        logger.error(f"Error triggering broadcast: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger broadcast: {str(e)}"
        )


@router.post("/analytics/broadcast/system")
async def trigger_system_broadcast(
    message: str,
    status: str = "info",
    db: Session = Depends(get_db)
):
    """
    Broadcast system-wide message to all connected clients.
    Super admin functionality.
    """
    try:
        broadcaster = RealTimeAnalyticsBroadcaster(db)
        await broadcaster.broadcast_system_status(status, message)
        
        return {
            "message": "System broadcast sent",
            "status": status,
            "content": message,
            "total_connections": connection_manager.get_total_connections()
        }
        
    except Exception as e:
        logger.error(f"Error triggering system broadcast: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger system broadcast: {str(e)}"
        )


@router.delete("/analytics/connections/{organization_id}")
async def disconnect_organization_websockets(organization_id: str):
    """
    Disconnect all WebSocket connections for a specific organization.
    Useful for maintenance or security purposes.
    """
    try:
        initial_count = connection_manager.get_organization_connection_count(organization_id)
        
        # Get all connections for the organization
        if organization_id in connection_manager.active_connections:
            connections_to_close = list(connection_manager.active_connections[organization_id])
            
            # Close all connections
            for websocket in connections_to_close:
                try:
                    await websocket.close(code=1000, reason="Administrative disconnect")
                except:
                    pass  # Connection might already be closed
                
                connection_manager.disconnect(websocket)
        
        return {
            "message": f"Disconnected all WebSocket connections for organization {organization_id}",
            "connections_closed": initial_count,
            "remaining_connections": connection_manager.get_organization_connection_count(organization_id)
        }
        
    except Exception as e:
        logger.error(f"Error disconnecting organization WebSockets: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect WebSockets: {str(e)}"
        )
