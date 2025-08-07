"""
Real-Time Analytics WebSocket Handler

Provides real-time analytics updates via WebSocket connections:
- Live usage metrics updates
- Engagement analytics streaming
- Revenue changes notifications
- Organization health score alerts
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Set, Optional, Any
import json
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from app.db.session import get_db
from app.services.real_data_analytics import RealDataOrganizationAnalyticsService
from app.schemas.organization_analytics import MetricTimeRange
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Manager for WebSocket connections with organization-based grouping."""
    
    def __init__(self):
        # organization_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        # websocket -> organization_id mapping for cleanup
        self.connection_orgs: Dict[WebSocket, str] = {}
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, organization_id: str, user_id: Optional[str] = None):
        """Accept a new WebSocket connection and add to organization group."""
        await websocket.accept()
        
        self.active_connections[organization_id].add(websocket)
        self.connection_orgs[websocket] = organization_id
        self.connection_metadata[websocket] = {
            "organization_id": organization_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        logger.info(f"WebSocket connected for organization {organization_id}, user {user_id}")
        
        # Send initial connection confirmation
        await self.send_personal_message(websocket, {
            "type": "connection_established",
            "organization_id": organization_id,
            "connected_at": datetime.utcnow().isoformat(),
            "message": "Real-time analytics connection established"
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection from all groups."""
        if websocket in self.connection_orgs:
            organization_id = self.connection_orgs[websocket]
            self.active_connections[organization_id].discard(websocket)
            del self.connection_orgs[websocket]
            
            if websocket in self.connection_metadata:
                user_id = self.connection_metadata[websocket].get("user_id")
                del self.connection_metadata[websocket]
                logger.info(f"WebSocket disconnected for organization {organization_id}, user {user_id}")
            
            # Clean up empty organization groups
            if not self.active_connections[organization_id]:
                del self.active_connections[organization_id]
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_organization(self, organization_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for a specific organization."""
        if organization_id not in self.active_connections:
            return
        
        disconnected_connections = []
        
        for websocket in self.active_connections[organization_id].copy():
            try:
                await websocket.send_text(json.dumps(message, default=str))
                # Update last ping time
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_ping"] = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error broadcasting to organization {organization_id}: {e}")
                disconnected_connections.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            self.disconnect(websocket)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all active connections."""
        for organization_id in list(self.active_connections.keys()):
            await self.broadcast_to_organization(organization_id, message)
    
    def get_organization_connection_count(self, organization_id: str) -> int:
        """Get number of active connections for an organization."""
        return len(self.active_connections.get(organization_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_connected_organizations(self) -> List[str]:
        """Get list of organizations with active connections."""
        return list(self.active_connections.keys())
    
    async def cleanup_stale_connections(self):
        """Remove connections that haven't been active recently."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)
        stale_connections = []
        
        for websocket, metadata in self.connection_metadata.items():
            if metadata.get("last_ping", datetime.utcnow()) < cutoff_time:
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            logger.info("Cleaning up stale WebSocket connection")
            self.disconnect(websocket)


# Global connection manager instance
connection_manager = WebSocketConnectionManager()


class RealTimeAnalyticsBroadcaster:
    """Service for broadcasting real-time analytics updates."""
    
    def __init__(self, db: Session):
        self.db = db
        self.analytics_service = RealDataOrganizationAnalyticsService(db)
    
    async def broadcast_usage_update(self, organization_id: str):
        """Broadcast updated usage metrics to organization connections."""
        try:
            # Get latest usage metrics
            usage_metrics = await self.analytics_service.get_real_time_usage_metrics(
                organization_id=organization_id,
                time_range=MetricTimeRange.LAST_7_DAYS
            )
            
            message = {
                "type": "usage_metrics_update",
                "organization_id": organization_id,
                "data": usage_metrics.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await connection_manager.broadcast_to_organization(organization_id, message)
            logger.info(f"Broadcasted usage update to organization {organization_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting usage update: {e}")
    
    async def broadcast_engagement_update(self, organization_id: str):
        """Broadcast updated engagement analytics to organization connections."""
        try:
            # Note: Would implement engagement analytics method
            message = {
                "type": "engagement_analytics_update",
                "organization_id": organization_id,
                "data": {"placeholder": "engagement_data"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await connection_manager.broadcast_to_organization(organization_id, message)
            logger.info(f"Broadcasted engagement update to organization {organization_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting engagement update: {e}")
    
    async def broadcast_health_score_alert(self, organization_id: str, health_score: float, previous_score: float):
        """Broadcast health score changes that exceed threshold."""
        try:
            score_change = abs(health_score - previous_score)
            if score_change >= 10:  # Alert on significant changes
                message = {
                    "type": "health_score_alert",
                    "organization_id": organization_id,
                    "data": {
                        "current_score": health_score,
                        "previous_score": previous_score,
                        "change": health_score - previous_score,
                        "severity": "high" if score_change >= 20 else "medium"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await connection_manager.broadcast_to_organization(organization_id, message)
                logger.info(f"Broadcasted health score alert to organization {organization_id}")
        
        except Exception as e:
            logger.error(f"Error broadcasting health score alert: {e}")
    
    async def broadcast_system_status(self, status: str, message: str):
        """Broadcast system-wide status updates."""
        try:
            broadcast_message = {
                "type": "system_status",
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await connection_manager.broadcast_to_all(broadcast_message)
            logger.info(f"Broadcasted system status: {status}")
            
        except Exception as e:
            logger.error(f"Error broadcasting system status: {e}")


class AnalyticsWebSocketHandler:
    """WebSocket handler for analytics connections."""
    
    def __init__(self):
        self.update_intervals = {
            "usage": 60,        # Update usage metrics every minute
            "engagement": 300,  # Update engagement every 5 minutes
            "health": 1800,     # Update health scores every 30 minutes
        }
    
    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        organization_id: str,
        user_id: Optional[str] = None,
        db: Session = Depends(get_db)
    ):
        """Handle WebSocket connection lifecycle."""
        await connection_manager.connect(websocket, organization_id, user_id)
        update_tasks = []
        
        try:
            # Send initial analytics data
            await self._send_initial_analytics(websocket, organization_id, db)
            
            # Start background update tasks
            update_tasks = [
                asyncio.create_task(self._periodic_usage_updates(organization_id, db))
            ]
            
            # Listen for client messages
            while True:
                try:
                    # Wait for client messages with timeout
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    message = json.loads(data)
                    await self._handle_client_message(websocket, organization_id, message, db)
                
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await connection_manager.send_personal_message(websocket, {
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                except json.JSONDecodeError:
                    await connection_manager.send_personal_message(websocket, {
                        "type": "error",
                        "message": "Invalid JSON message format"
                    })
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for organization {organization_id}")
        
        except Exception as e:
            logger.error(f"WebSocket error for organization {organization_id}: {e}")
            await connection_manager.send_personal_message(websocket, {
                "type": "error",
                "message": f"Server error: {str(e)}"
            })
        
        finally:
            # Cancel background tasks
            for task in update_tasks:
                task.cancel()
            
            connection_manager.disconnect(websocket)
    
    async def _send_initial_analytics(self, websocket: WebSocket, organization_id: str, db: Session):
        """Send initial analytics data when client connects."""
        try:
            analytics_service = RealDataOrganizationAnalyticsService(db)
            
            # Get initial usage metrics
            usage_metrics = await analytics_service.get_real_time_usage_metrics(
                organization_id=organization_id,
                time_range=MetricTimeRange.LAST_7_DAYS
            )
            
            await connection_manager.send_personal_message(websocket, {
                "type": "initial_data",
                "usage_metrics": usage_metrics.dict(),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error sending initial analytics: {e}")
    
    async def _handle_client_message(
        self,
        websocket: WebSocket,
        organization_id: str,
        message: Dict[str, Any],
        db: Session
    ):
        """Handle messages from WebSocket clients."""
        try:
            message_type = message.get("type")
            
            if message_type == "request_update":
                # Client requesting immediate update
                metric_type = message.get("metric_type", "usage")
                await self._send_metric_update(websocket, organization_id, metric_type, db)
            
            elif message_type == "change_time_range":
                # Client changing time range for metrics
                time_range = message.get("time_range", "last_24_hours")
                metric_time_range = MetricTimeRange(time_range)
                await self._send_metric_with_range(websocket, organization_id, metric_time_range, db)
            
            elif message_type == "pong":
                # Response to ping - just update last activity
                if websocket in connection_manager.connection_metadata:
                    connection_manager.connection_metadata[websocket]["last_ping"] = datetime.utcnow()
            
            else:
                await connection_manager.send_personal_message(websocket, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
        
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def _send_metric_update(
        self,
        websocket: WebSocket,
        organization_id: str,
        metric_type: str,
        db: Session
    ):
        """Send specific metric update to client."""
        try:
            analytics_service = RealDataOrganizationAnalyticsService(db)
            
            if metric_type == "usage":
                data = await analytics_service.get_real_time_usage_metrics(
                    organization_id=organization_id,
                    time_range=MetricTimeRange.LAST_7_DAYS
                )
                
                await connection_manager.send_personal_message(websocket, {
                    "type": "metric_update",
                    "metric_type": metric_type,
                    "data": data.dict(),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error sending metric update: {e}")
    
    async def _send_metric_with_range(
        self,
        websocket: WebSocket,
        organization_id: str,
        time_range: MetricTimeRange,
        db: Session
    ):
        """Send metrics with specific time range."""
        try:
            analytics_service = RealDataOrganizationAnalyticsService(db)
            
            usage_data = await analytics_service.get_real_time_usage_metrics(
                organization_id=organization_id,
                time_range=time_range
            )
            
            await connection_manager.send_personal_message(websocket, {
                "type": "time_range_data",
                "time_range": time_range.value,
                "usage_metrics": usage_data.dict(),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error sending metric with range: {e}")
    
    async def _periodic_usage_updates(self, organization_id: str, db: Session):
        """Periodically broadcast usage metric updates."""
        while True:
            try:
                await asyncio.sleep(self.update_intervals["usage"])
                
                if connection_manager.get_organization_connection_count(organization_id) > 0:
                    broadcaster = RealTimeAnalyticsBroadcaster(db)
                    await broadcaster.broadcast_usage_update(organization_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic usage updates: {e}")


# Create handler instance
websocket_handler = AnalyticsWebSocketHandler()
