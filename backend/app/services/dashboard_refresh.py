"""
Dashboard Data Refresh Service

This service provides data refresh and caching mechanisms for the Super Admin dashboard,
supporting both manual refresh and automatic background updates.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.redis_caching import advanced_cache
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.subscription import Subscription
from app.models.therapy_sound import TherapySound
from app.routers.dashboard_websocket import dashboard_ws_manager
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


class DashboardDataRefreshService:
    """Service for refreshing and caching dashboard data."""
    
    def __init__(self):
        self.cache_prefix = "dashboard_cache"
        self.default_ttl = 300  # 5 minutes
        self.refresh_in_progress = False
        
    async def refresh_all_dashboard_data(self, db: Session) -> Dict[str, Any]:
        """Refresh all dashboard data and update cache."""
        if self.refresh_in_progress:
            raise HTTPException(
                status_code=429, 
                detail="Dashboard refresh already in progress"
            )
            
        self.refresh_in_progress = True
        refresh_results = {}
        
        try:
            logger.info("Starting complete dashboard data refresh")
            
            # Refresh platform statistics
            platform_stats = await self._refresh_platform_stats(db)
            refresh_results["platform_stats"] = platform_stats
            
            # Refresh revenue analytics
            revenue_analytics = await self._refresh_revenue_analytics(db)
            refresh_results["revenue_analytics"] = revenue_analytics
            
            # Refresh growth trends
            growth_trends = await self._refresh_growth_trends(db)
            refresh_results["growth_trends"] = growth_trends
            
            # Refresh system health
            system_health = await self._refresh_system_health(db)
            refresh_results["system_health"] = system_health
            
            # Update cache timestamps
            await self._update_cache_metadata()
            
            # Notify WebSocket connections of refresh
            await self._notify_websocket_refresh(refresh_results)
            
            logger.info("Dashboard data refresh completed successfully")
            return {
                "success": True,
                "refreshed_at": datetime.now().isoformat(),
                "data": refresh_results
            }
            
        except Exception as e:
            logger.error(f"Dashboard refresh failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "refreshed_at": datetime.now().isoformat()
            }
        finally:
            self.refresh_in_progress = False
            
    async def _refresh_platform_stats(self, db: Session) -> Dict[str, Any]:
        """Refresh platform statistics."""
        try:
            # Count total users
            total_users = db.query(User).count()
            
            # Count active users (logged in within last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            active_users = db.query(User).filter(
                User.last_login >= thirty_days_ago
            ).count()
            
            # Count total organizations
            total_organizations = db.query(Organization).count()
            
            # Calculate monthly revenue (simplified)
            monthly_revenue = db.query(func.sum(Subscription.price)).scalar() or 0.0
            
            # Count therapy sounds
            total_sounds = db.query(TherapySound).count()
            
            # Calculate growth rates (simplified - would need historical data)
            user_growth_rate = 5.2  # Mock growth rate
            org_growth_rate = 8.1
            revenue_growth_rate = 12.3
            
            platform_stats = {
                "total_users": total_users,
                "active_users": active_users,
                "total_organizations": total_organizations,
                "monthly_revenue": float(monthly_revenue),
                "total_sounds": total_sounds,
                "user_growth_rate": user_growth_rate,
                "org_growth_rate": org_growth_rate,
                "revenue_growth_rate": revenue_growth_rate,
                "active_sessions": 156,  # Mock data - would come from session tracking
                "content_plays": 8432,  # Mock data - would come from analytics
                "conversion_rate": 3.7   # Mock data - would be calculated
            }
            
            # Cache the data
            cache_key = "platform_stats"
            advanced_cache.set("dashboard", cache_key, platform_stats, ttl=self.default_ttl)
            
            return platform_stats
            
        except Exception as e:
            logger.error(f"Failed to refresh platform stats: {e}")
            raise
            
    async def _refresh_revenue_analytics(self, db: Session) -> Dict[str, Any]:
        """Refresh revenue analytics."""
        try:
            # Calculate revenue metrics (simplified)
            total_revenue = db.query(func.sum(Subscription.price)).scalar() or 0.0
            total_subscribers = db.query(Subscription).filter(Subscription.is_active == True).count()
            
            # Calculate key metrics
            mrr = float(total_revenue)  # Monthly Recurring Revenue
            arr = mrr * 12  # Annual Recurring Revenue
            arpu = mrr / max(total_subscribers, 1)  # Average Revenue Per User
            clv = arpu * 24  # Customer Lifetime Value (simplified)
            
            revenue_analytics = {
                "mrr": mrr,
                "arr": arr,
                "arpu": arpu,
                "clv": clv,
                "total_revenue": float(total_revenue),
                "total_subscribers": total_subscribers,
                "mrr_growth_rate": 8.5,  # Mock growth rate
                "arr_growth_rate": 8.5,
                "churn_rate": 2.1,
                "revenue_breakdown": {
                    "starter": mrr * 0.3,
                    "professional": mrr * 0.5,
                    "enterprise": mrr * 0.2
                }
            }
            
            # Cache the data
            cache_key = "revenue_analytics"
            advanced_cache.set("dashboard", cache_key, revenue_analytics, ttl=self.default_ttl)
            
            return revenue_analytics
            
        except Exception as e:
            logger.error(f"Failed to refresh revenue analytics: {e}")
            raise
            
    async def _refresh_growth_trends(self, db: Session) -> Dict[str, Any]:
        """Refresh growth trends."""
        try:
            # Calculate growth metrics (simplified)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            new_users = db.query(User).filter(User.created_at >= thirty_days_ago).count()
            new_organizations = db.query(Organization).filter(
                Organization.created_at >= thirty_days_ago
            ).count()
            
            # Mock retention and churn data (would come from analytics)
            growth_trends = {
                "new_users": new_users,
                "new_organizations": new_organizations,
                "retention_rate": 85.2,
                "churn_rate": 2.1,
                "user_growth_rate": 15.3,
                "org_growth_rate": 22.1,
                "geographic_distribution": {
                    "north_america": 45.2,
                    "europe": 28.7,
                    "asia": 18.9,
                    "other": 7.2
                },
                "acquisition_channels": {
                    "organic": 42.1,
                    "paid_search": 28.5,
                    "referral": 18.2,
                    "social": 11.2
                },
                "key_insights": [
                    "User acquisition increased 23% this month",
                    "Enterprise signups are trending upward",
                    "Mobile usage has grown 45% quarter-over-quarter",
                    "Customer satisfaction scores improved to 4.7/5"
                ]
            }
            
            # Cache the data
            cache_key = "growth_trends"
            advanced_cache.set("dashboard", cache_key, growth_trends, ttl=self.default_ttl)
            
            return growth_trends
            
        except Exception as e:
            logger.error(f"Failed to refresh growth trends: {e}")
            raise
            
    async def _refresh_system_health(self, db: Session) -> Dict[str, Any]:
        """Refresh system health metrics."""
        try:
            # Mock system health data (would come from monitoring systems)
            system_health = {
                "overall_health_score": 94.7,
                "status": "healthy",
                "components": {
                    "database": {
                        "status": "healthy",
                        "response_time": 12,
                        "uptime": 99.8,
                        "connections": 15
                    },
                    "redis_cache": {
                        "status": "healthy", 
                        "response_time": 3,
                        "uptime": 99.9,
                        "memory_usage": 45.2
                    },
                    "api_server": {
                        "status": "healthy",
                        "response_time": 89,
                        "uptime": 99.7,
                        "requests_per_minute": 145
                    },
                    "background_jobs": {
                        "status": "healthy",
                        "active_jobs": 3,
                        "queue_size": 8,
                        "success_rate": 98.5
                    }
                },
                "performance_metrics": {
                    "avg_response_time": 67,
                    "error_rate": 0.12,
                    "throughput": 145,
                    "cpu_usage": 23.4,
                    "memory_usage": 67.8
                }
            }
            
            # Cache the data
            cache_key = "system_health"
            advanced_cache.set("dashboard", cache_key, system_health, ttl=60)  # Shorter TTL for health data
            
            return system_health
            
        except Exception as e:
            logger.error(f"Failed to refresh system health: {e}")
            raise
            
    async def _update_cache_metadata(self):
        """Update cache metadata with refresh timestamps."""
        metadata = {
            "last_refresh": datetime.now().isoformat(),
            "refresh_count": await self._increment_refresh_count(),
            "cache_status": "healthy"
        }
        
        cache_key = "metadata"
        advanced_cache.set("dashboard", cache_key, metadata, ttl=3600)  # 1 hour TTL
        
    async def _increment_refresh_count(self) -> int:
        """Increment and return refresh count."""
        cache_key = "refresh_count"
        try:
            current_count = advanced_cache.get("dashboard", cache_key) or 0
            new_count = int(current_count) + 1
            advanced_cache.set("dashboard", cache_key, new_count, ttl=86400)  # 24 hour TTL
            return new_count
        except Exception:
            return 1
            
    async def _notify_websocket_refresh(self, data: Dict[str, Any]):
        """Notify WebSocket connections of data refresh."""
        try:
            refresh_message = {
                "type": "data_refresh",
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            await dashboard_ws_manager.broadcast_to_admins(refresh_message)
            logger.info("Sent refresh notification to WebSocket connections")
            
        except Exception as e:
            logger.error(f"Failed to notify WebSocket connections: {e}")
            
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get dashboard cache statistics."""
        try:
            metadata_key = "metadata"
            metadata = advanced_cache.get("dashboard", metadata_key) or {}
            
            cache_keys = ["platform_stats", "revenue_analytics", "growth_trends", "system_health"]
            
            cache_status = {}
            for key in cache_keys:
                cached_data = advanced_cache.get("dashboard", key)
                cache_status[key] = {
                    "cached": cached_data is not None,
                    "size": len(str(cached_data)) if cached_data else 0
                }
                
            return {
                "cache_metadata": metadata,
                "cache_status": cache_status,
                "refresh_in_progress": self.refresh_in_progress
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {"error": str(e)}
            
    async def clear_dashboard_cache(self):
        """Clear all dashboard cache data."""
        try:
            cache_keys = ["platform_stats", "revenue_analytics", "growth_trends", "system_health", "metadata"]
            
            for key in cache_keys:
                advanced_cache.delete("dashboard", key)
                
            logger.info("Dashboard cache cleared successfully")
            return {"success": True, "cleared_keys": len(cache_keys)}
            
        except Exception as e:
            logger.error(f"Failed to clear dashboard cache: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
dashboard_refresh_service = DashboardDataRefreshService()


# Background refresh task
async def background_dashboard_refresh():
    """Background task for automatic dashboard refresh."""
    while True:
        try:
            await asyncio.sleep(300)  # Refresh every 5 minutes
            
            # Get database session (you may need to adjust this based on your setup)
            from app.db.session import SessionLocal
            db = SessionLocal()
            
            try:
                await dashboard_refresh_service.refresh_all_dashboard_data(db)
                logger.info("Background dashboard refresh completed")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Background dashboard refresh failed: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying


# Function to start background refresh task
def start_dashboard_background_refresh():
    """Start the background dashboard refresh task."""
    asyncio.create_task(background_dashboard_refresh())
    logger.info("Dashboard background refresh task started")
