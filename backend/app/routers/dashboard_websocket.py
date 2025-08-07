"""
Real-time WebSocket service for Super Admin Dashboard updates.

This service provides WebSocket endpoints for real-time dashboard data updates,
integrating with the dashboard metrics API and background job system.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.routing import APIRouter
import jwt
from jwt import PyJWTError

from app.core.auth_dependencies import get_current_user_compatible
from app.models.user import User, UserRole
from app.core.config import settings
from app.db.session import get_db
from app.routers.dashboard_metrics import (
    get_platform_stats, get_revenue_analytics, get_growth_trends,
    get_system_health
)
from app.schemas.dashboard_metrics import TimeRangeEnum
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket Dashboard"])


class DashboardWebSocketManager:
    """Manages WebSocket connections for real-time dashboard updates."""
    
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        # Background update task
        self.update_task: Optional[asyncio.Task] = None
        self.update_interval = 30  # seconds
        
    async def connect(self, websocket: WebSocket, user_id: str, user_role: str):
        """Accept WebSocket connection and store it."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.connection_metadata[user_id] = {
            "connected_at": datetime.now(),
            "role": user_role,
            "last_update": None
        }
        
        logger.info(f"Dashboard WebSocket connected for user {user_id} with role {user_role}")
        
        # Start background update task if this is the first connection
        if len(self.active_connections) == 1 and self.update_task is None:
            self.update_task = asyncio.create_task(self._background_update_loop())
            
    async def disconnect(self, user_id: str):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.connection_metadata:
            del self.connection_metadata[user_id]
            
        logger.info(f"Dashboard WebSocket disconnected for user {user_id}")
        
        # Stop background update task if no connections remain
        if len(self.active_connections) == 0 and self.update_task:
            self.update_task.cancel()
            self.update_task = None
            
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user."""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(json.dumps(message))
                self.connection_metadata[user_id]["last_update"] = datetime.now()
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                await self.disconnect(user_id)
                
    async def broadcast_to_admins(self, message: dict):
        """Send message to all connected super admin users."""
        admin_connections = {
            user_id: websocket for user_id, websocket in self.active_connections.items()
            if self.connection_metadata.get(user_id, {}).get("role") == UserRole.SUPER_ADMIN
        }
        
        if not admin_connections:
            return
            
        disconnected_users = []
        for user_id, websocket in admin_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
                self.connection_metadata[user_id]["last_update"] = datetime.now()
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")
                disconnected_users.append(user_id)
                
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(user_id)
            
    async def _background_update_loop(self):
        """Background task to send periodic dashboard updates."""
        while len(self.active_connections) > 0:
            try:
                await self._send_dashboard_updates()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                logger.info("Dashboard WebSocket background update task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(self.update_interval)
                
    async def _send_dashboard_updates(self):
        """Fetch and send latest dashboard data to all connected admins."""
        try:
            # Note: In a real implementation, you would need to get a database session
            # and user context. For now, this is a simplified version.
            
            # Create mock data for demonstration
            update_message = {
                "type": "dashboard_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "platform_stats": {
                        "total_users": 12500,
                        "active_sessions": 234,
                        "monthly_revenue": 145000.50,
                        "content_plays": 8765
                    },
                    "system_health": {
                        "overall_health_score": 95.2,
                        "status": "healthy"
                    }
                }
            }
            
            await self.broadcast_to_admins(update_message)
            logger.debug("Sent dashboard update to all connected admins")
            
        except Exception as e:
            logger.error(f"Failed to send dashboard updates: {e}")
            
    async def send_alert_notification(self, alert_data: dict):
        """Send immediate alert notification to all admins."""
        alert_message = {
            "type": "alert_notification",
            "timestamp": datetime.now().isoformat(),
            "data": alert_data
        }
        
        await self.broadcast_to_admins(alert_message)
        logger.info(f"Sent alert notification: {alert_data.get('message', 'Unknown alert')}")
        
    def get_connection_stats(self) -> dict:
        """Get statistics about active connections."""
        return {
            "total_connections": len(self.active_connections),
            "admin_connections": len([
                uid for uid, meta in self.connection_metadata.items()
                if meta.get("role") == UserRole.SUPER_ADMIN
            ]),
            "connections": [
                {
                    "user_id": user_id,
                    "connected_at": meta["connected_at"].isoformat(),
                    "role": meta["role"],
                    "last_update": meta["last_update"].isoformat() if meta["last_update"] else None
                }
                for user_id, meta in self.connection_metadata.items()
            ]
        }


# Global WebSocket manager instance
dashboard_ws_manager = DashboardWebSocketManager()


async def verify_websocket_token(token: str, db: Session) -> Optional[User]:
    """Verify JWT token for WebSocket authentication."""
    try:
        # Use a default secret key for demo purposes
        secret_key = "your-secret-key-here"  # In production, use proper configuration
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            return None
            
        # In a real implementation, you would fetch the user from the database
        # For now, return a mock super admin user
        from app.models.user import User, UserRole
        mock_user = User(
            id=user_id,
            email="admin@example.com",
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        return mock_user
        
    except PyJWTError:
        return None


@router.websocket("/admin/dashboard")
async def dashboard_websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time Super Admin dashboard updates."""
    
    # Verify authentication
    if not token:
        await websocket.close(code=4001, reason="Authentication token required")
        return
        
    user = await verify_websocket_token(token, db)
    if not user or getattr(user, 'role', None) != UserRole.SUPER_ADMIN:
        await websocket.close(code=4003, reason="Super Admin access required")
        return
        
    user_id = str(user.id)
    
    try:
        # Accept connection
        await dashboard_ws_manager.connect(websocket, user_id, str(getattr(user, 'role', 'unknown')))
        
        # Send initial dashboard data
        initial_message = {
            "type": "connection_established",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to Super Admin dashboard updates"
        }
        await dashboard_ws_manager.send_personal_message(initial_message, user_id)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    pong_message = {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }
                    await dashboard_ws_manager.send_personal_message(pong_message, user_id)
                    
                elif message_type == "request_update":
                    # Client requesting immediate update
                    await dashboard_ws_manager._send_dashboard_updates()
                    
                elif message_type == "subscribe":
                    # Client subscribing to specific data types
                    subscriptions = message.get("subscriptions", [])
                    # Store subscription preferences (implementation depends on requirements)
                    logger.info(f"User {user_id} subscribed to: {subscriptions}")
                    
                else:
                    logger.warning(f"Unknown message type from user {user_id}: {message_type}")
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from user {user_id}")
            except Exception as e:
                logger.error(f"Error handling message from user {user_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await dashboard_ws_manager.disconnect(user_id)


@router.get("/admin/dashboard/connections")
async def get_dashboard_connections(
    current_user: User = Depends(get_current_user_compatible)
):
    """Get information about active dashboard WebSocket connections."""
    if getattr(current_user, 'role', None) != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Admin access required")
        
    return dashboard_ws_manager.get_connection_stats()


@router.post("/admin/dashboard/broadcast")
async def broadcast_dashboard_message(
    message: dict,
    current_user: User = Depends(get_current_user_compatible)
):
    """Broadcast a message to all connected dashboard users."""
    if getattr(current_user, 'role', None) != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Admin access required")
        
    broadcast_message = {
        "type": "admin_broadcast",
        "timestamp": datetime.now().isoformat(),
        "from": getattr(current_user, 'email', 'unknown'),
        "data": message
    }
    
    await dashboard_ws_manager.broadcast_to_admins(broadcast_message)
    
    return {
        "success": True,
        "message": "Message broadcasted to all connected dashboard users",
        "recipients": len(dashboard_ws_manager.active_connections)
    }


# Function to send alerts from other parts of the application
async def send_dashboard_alert(alert_data: dict):
    """
    Function to be called from other parts of the application to send alerts.
    
    Args:
        alert_data: Dictionary containing alert information
    """
    await dashboard_ws_manager.send_alert_notification(alert_data)


# Function to trigger dashboard refresh
async def trigger_dashboard_refresh():
    """
    Function to trigger an immediate dashboard data refresh.
    """
    refresh_message = {
        "type": "refresh_triggered",
        "timestamp": datetime.now().isoformat(),
        "message": "Dashboard data refresh triggered"
    }
    
    await dashboard_ws_manager.broadcast_to_admins(refresh_message)
