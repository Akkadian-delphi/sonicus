"""
Super Admin Dashboard Metrics API

This module provides comprehensive analytics endpoints for the Super Admin dashboard,
leveraging the system optimization features for performance and monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
import asyncio

from app.core.auth_dependencies import get_current_user_compatible
from app.models.user import UserRole
from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.subscription import Subscription
from app.models.therapy_sound import TherapySound
from app.schemas.dashboard_metrics import (
    PlatformStatsResponse, RevenueAnalyticsResponse, 
    GrowthTrendsResponse, SystemHealthResponse, SystemAlertsResponse,
    TimeRangeEnum, BreakdownEnum, AlertSeverityEnum
)
from app.core.redis_caching import advanced_cache, cached
from app.core.error_handling import advanced_logger, log_exceptions, ErrorCategory
from app.core.background_jobs import job_manager
from app.core.db_optimization import db_pool_manager
from app.core.rate_limiting import rate_limiter
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/super-admin/dashboard", tags=["Super Admin Dashboard"])


# Authentication dependency
async def require_super_admin(current_user: User = Depends(get_current_user_compatible)) -> User:
    """Require Super Admin role for dashboard access."""
    if current_user is None:
        advanced_logger.error(
            "Unauthorized dashboard access attempt - no user",
            category=ErrorCategory.AUTHORIZATION,
            extra={"endpoint": "dashboard_metrics"}
        )
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
    # Check if user has super admin role
    user_role = getattr(current_user, 'role', None)
    if user_role != UserRole.SUPER_ADMIN:
        advanced_logger.error(
            "Unauthorized dashboard access attempt",
            category=ErrorCategory.AUTHORIZATION,
            extra={
                "user_id": getattr(current_user, 'id', None),
                "role": user_role.value if user_role else None,
                "endpoint": "dashboard_metrics"
            }
        )
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return current_user


@router.get("/stats", response_model=PlatformStatsResponse)
@log_exceptions(category=ErrorCategory.SYSTEM)
@cached('dashboard_stats', ttl=300)  # Cache for 5 minutes
async def get_platform_stats(
    time_range: str = Query("7d", description="Time range: 1d, 7d, 30d, 90d"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive platform-wide statistics.
    
    Args:
        time_range: Time range for analytics (1d, 7d, 30d, 90d)
        current_user: Authenticated super admin user
        db: Database session
        
    Returns:
        Dict containing platform metrics
    """
    try:
        advanced_logger.info(
            f"Fetching platform stats for range: {time_range}",
            extra={"user_id": current_user.id, "time_range": time_range}
        )
        
        # Calculate date range
        days_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(time_range, 7)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Platform overview metrics
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_organizations = db.query(func.count(Organization.id)).scalar() or 0
        active_subscriptions = db.query(func.count(Subscription.id)).filter(
            Subscription.status == "active"
        ).scalar() or 0
        total_sounds = db.query(func.count(TherapySound.id)).scalar() or 0
        
        # Time-based metrics
        new_users = db.query(func.count(User.id)).filter(
            User.created_at >= start_date
        ).scalar() or 0
        
        new_organizations = db.query(func.count(Organization.id)).filter(
            Organization.created_at >= start_date
        ).scalar() or 0
        
        # Revenue metrics (mock for now - would integrate with billing system)
        total_revenue = active_subscriptions * 29.99  # Mock calculation
        revenue_growth = 12.5 if days > 1 else 0  # Mock growth percentage
        
        # User engagement metrics (mock - would come from analytics)
        avg_session_duration = 1240  # seconds
        daily_active_users = int(total_users * 0.3)  # Mock: 30% DAU
        monthly_active_users = int(total_users * 0.7)  # Mock: 70% MAU
        
        # Content metrics
        total_plays = total_users * 45  # Mock: avg 45 plays per user
        popular_categories = [
            {"name": "Nature Sounds", "plays": int(total_plays * 0.35)},
            {"name": "White Noise", "plays": int(total_plays * 0.25)},
            {"name": "Meditation", "plays": int(total_plays * 0.20)},
            {"name": "Sleep Sounds", "plays": int(total_plays * 0.20)}
        ]
        
        # System metrics from our optimization features
        cache_stats = advanced_cache.get_cache_info()
        job_stats = job_manager.get_queue_stats()
        db_stats = db_pool_manager.get_connection_stats()
        
        stats = {
            "overview": {
                "total_users": total_users,
                "total_organizations": total_organizations,
                "active_subscriptions": active_subscriptions,
                "total_sounds": total_sounds,
                "total_revenue": round(total_revenue, 2),
                "revenue_growth_percent": revenue_growth
            },
            "growth": {
                "time_range": time_range,
                "new_users": new_users,
                "new_organizations": new_organizations,
                "user_growth_rate": round((new_users / max(total_users - new_users, 1)) * 100, 2),
                "org_growth_rate": round((new_organizations / max(total_organizations - new_organizations, 1)) * 100, 2)
            },
            "engagement": {
                "daily_active_users": daily_active_users,
                "monthly_active_users": monthly_active_users,
                "avg_session_duration": avg_session_duration,
                "total_content_plays": total_plays,
                "popular_categories": popular_categories
            },
            "system_performance": {
                "cache_hit_rate": cache_stats["stats"]["hit_rate_percent"],
                "background_jobs": {
                    "available": job_stats.get("available", False),
                    "active_queues": len(job_stats.get("queues", []))
                },
                "database": {
                    "status": db_stats["status"],
                    "total_pools": len(db_stats["pools"])
                }
            },
            "generated_at": datetime.utcnow().isoformat(),
            "time_range_days": days
        }
        
        advanced_logger.info(
            "Platform stats generated successfully",
            extra={
                "user_id": current_user.id,
                "stats_summary": {
                    "users": total_users,
                    "organizations": total_organizations,
                    "revenue": total_revenue
                }
            }
        )
        
        return stats
        
    except Exception as e:
        advanced_logger.error(
            "Failed to generate platform stats",
            exception=e,
            category=ErrorCategory.SYSTEM,
            extra={"user_id": current_user.id, "time_range": time_range}
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve platform statistics")


@router.get("/revenue", response_model=RevenueAnalyticsResponse)
@log_exceptions(category=ErrorCategory.SYSTEM)
@cached('dashboard_revenue', ttl=600)  # Cache for 10 minutes
async def get_revenue_analytics(
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d, 1y"),
    breakdown: str = Query("daily", description="Breakdown: daily, weekly, monthly"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed revenue analytics and trends.
    
    Args:
        time_range: Time range for analytics
        breakdown: Data breakdown granularity
        current_user: Authenticated super admin user
        db: Database session
        
    Returns:
        Dict containing revenue analytics
    """
    try:
        advanced_logger.info(
            f"Fetching revenue analytics: {time_range}, breakdown: {breakdown}",
            extra={"user_id": current_user.id}
        )
        
        # Calculate date range
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(time_range, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get subscription data
        active_subscriptions = db.query(Subscription).filter(
            Subscription.status == "active"
        ).all()
        
        # Mock revenue calculations (in production, integrate with billing system)
        base_revenue = len(active_subscriptions) * 29.99
        
        # Generate time series data
        time_series = []
        if breakdown == "daily" and days <= 30:
            for i in range(days):
                date = start_date + timedelta(days=i)
                daily_revenue = base_revenue * (0.8 + (i % 7) * 0.04)  # Mock variation
                time_series.append({
                    "date": date.date().isoformat(),
                    "revenue": round(daily_revenue, 2),
                    "subscriptions": len(active_subscriptions) + (i % 3) - 1,
                    "new_subscriptions": max(0, (i % 5) - 2)
                })
        elif breakdown == "weekly":
            weeks = days // 7
            for i in range(weeks):
                week_start = start_date + timedelta(weeks=i)
                weekly_revenue = base_revenue * 7 * (0.9 + (i % 4) * 0.05)
                time_series.append({
                    "week_start": week_start.date().isoformat(),
                    "revenue": round(weekly_revenue, 2),
                    "subscriptions": len(active_subscriptions) + (i % 10),
                    "new_subscriptions": max(0, (i % 8) - 3)
                })
        else:  # monthly
            months = max(1, days // 30)
            for i in range(months):
                month_start = start_date + timedelta(days=i*30)
                monthly_revenue = base_revenue * 30 * (0.95 + (i % 3) * 0.1)
                time_series.append({
                    "month": month_start.strftime("%Y-%m"),
                    "revenue": round(monthly_revenue, 2),
                    "subscriptions": len(active_subscriptions) + (i % 20),
                    "new_subscriptions": max(0, (i % 12) - 5)
                })
        
        # Revenue metrics
        total_revenue = sum(item["revenue"] for item in time_series)
        avg_revenue_per_period = round(total_revenue / max(len(time_series), 1), 2)
        
        # Growth calculations
        if len(time_series) >= 2:
            recent_revenue = sum(item["revenue"] for item in time_series[-7:])
            previous_revenue = sum(item["revenue"] for item in time_series[-14:-7]) or 1
            growth_rate = round(((recent_revenue - previous_revenue) / previous_revenue) * 100, 2)
        else:
            growth_rate = 0
        
        # Revenue by organization type (mock data)
        revenue_by_org_type = [
            {"type": "Enterprise", "revenue": round(total_revenue * 0.45, 2), "count": len(active_subscriptions) // 3},
            {"type": "Small Business", "revenue": round(total_revenue * 0.35, 2), "count": len(active_subscriptions) // 2},
            {"type": "Startup", "revenue": round(total_revenue * 0.20, 2), "count": len(active_subscriptions) // 4}
        ]
        
        # Subscription plan breakdown (mock data)
        plan_breakdown = [
            {"plan": "Premium", "revenue": round(total_revenue * 0.60, 2), "subscribers": int(len(active_subscriptions) * 0.6)},
            {"plan": "Business", "revenue": round(total_revenue * 0.30, 2), "subscribers": int(len(active_subscriptions) * 0.3)},
            {"plan": "Enterprise", "revenue": round(total_revenue * 0.10, 2), "subscribers": int(len(active_subscriptions) * 0.1)}
        ]
        
        analytics = {
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "avg_revenue_per_period": avg_revenue_per_period,
                "growth_rate_percent": growth_rate,
                "active_subscriptions": len(active_subscriptions),
                "time_range": time_range,
                "breakdown": breakdown
            },
            "time_series": time_series,
            "revenue_by_organization_type": revenue_by_org_type,
            "subscription_plan_breakdown": plan_breakdown,
            "metrics": {
                "monthly_recurring_revenue": round(base_revenue, 2),
                "average_revenue_per_user": round(base_revenue / max(len(active_subscriptions), 1), 2),
                "churn_rate_percent": 2.5,  # Mock churn rate
                "customer_lifetime_value": round(29.99 * 12 / 0.025, 2)  # Mock CLV
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return analytics
        
    except Exception as e:
        advanced_logger.error(
            "Failed to generate revenue analytics",
            exception=e,
            category=ErrorCategory.SYSTEM,
            extra={"user_id": current_user.id}
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve revenue analytics")


@router.get("/growth", response_model=GrowthTrendsResponse)
@log_exceptions(category=ErrorCategory.SYSTEM)
@cached('dashboard_growth', ttl=300)  # Cache for 5 minutes
async def get_growth_trends(
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d, 1y"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get user and organization growth trends.
    
    Args:
        time_range: Time range for growth analysis
        current_user: Authenticated super admin user
        db: Database session
        
    Returns:
        Dict containing growth trends and forecasts
    """
    try:
        advanced_logger.info(
            f"Fetching growth trends for range: {time_range}",
            extra={"user_id": current_user.id}
        )
        
        # Calculate date range
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(time_range, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get current totals
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_organizations = db.query(func.count(Organization.id)).scalar() or 0
        
        # Generate growth time series
        user_growth = []
        org_growth = []
        
        for i in range(0, days, max(1, days // 20)):  # Max 20 data points
            date = start_date + timedelta(days=i)
            
            # Mock growth data with realistic patterns
            user_count = int(total_users * (0.3 + (i / days) * 0.7))
            org_count = int(total_organizations * (0.4 + (i / days) * 0.6))
            
            user_growth.append({
                "date": date.date().isoformat(),
                "total_users": user_count,
                "new_users": max(0, int(user_count * 0.02) + (i % 5) - 2),
                "active_users": int(user_count * 0.65)
            })
            
            org_growth.append({
                "date": date.date().isoformat(),
                "total_organizations": org_count,
                "new_organizations": max(0, int(org_count * 0.03) + (i % 3) - 1),
                "active_organizations": int(org_count * 0.85)
            })
        
        # Calculate growth rates
        if len(user_growth) >= 2:
            user_growth_rate = round(
                ((user_growth[-1]["total_users"] - user_growth[0]["total_users"]) / 
                 max(user_growth[0]["total_users"], 1)) * 100, 2
            )
            org_growth_rate = round(
                ((org_growth[-1]["total_organizations"] - org_growth[0]["total_organizations"]) / 
                 max(org_growth[0]["total_organizations"], 1)) * 100, 2
            )
        else:
            user_growth_rate = 0
            org_growth_rate = 0
        
        # Acquisition channels (mock data)
        acquisition_channels = [
            {"channel": "Organic Search", "users": int(total_users * 0.40), "cost_per_acquisition": 0},
            {"channel": "Social Media", "users": int(total_users * 0.25), "cost_per_acquisition": 15.50},
            {"channel": "Referrals", "users": int(total_users * 0.20), "cost_per_acquisition": 8.75},
            {"channel": "Paid Ads", "users": int(total_users * 0.10), "cost_per_acquisition": 32.00},
            {"channel": "Direct", "users": int(total_users * 0.05), "cost_per_acquisition": 0}
        ]
        
        # Geographic distribution (mock data)
        geographic_distribution = [
            {"region": "North America", "users": int(total_users * 0.45), "organizations": int(total_organizations * 0.50)},
            {"region": "Europe", "users": int(total_users * 0.30), "organizations": int(total_organizations * 0.25)},
            {"region": "Asia Pacific", "users": int(total_users * 0.15), "organizations": int(total_organizations * 0.15)},
            {"region": "Latin America", "users": int(total_users * 0.07), "organizations": int(total_organizations * 0.07)},
            {"region": "Other", "users": int(total_users * 0.03), "organizations": int(total_organizations * 0.03)}
        ]
        
        # Retention metrics (mock data)
        retention_metrics = {
            "day_1_retention": 85.2,
            "day_7_retention": 72.8,
            "day_30_retention": 58.5,
            "day_90_retention": 45.2
        }
        
        # Simple growth forecast (next 30 days)
        current_daily_growth = (user_growth[-1]["new_users"] if user_growth else 0)
        forecasted_users = total_users + (current_daily_growth * 30)
        forecasted_organizations = total_organizations + (int(current_daily_growth * 0.1) * 30)
        
        trends = {
            "summary": {
                "current_users": total_users,
                "current_organizations": total_organizations,
                "user_growth_rate_percent": user_growth_rate,
                "organization_growth_rate_percent": org_growth_rate,
                "time_range": time_range
            },
            "user_growth_timeline": user_growth,
            "organization_growth_timeline": org_growth,
            "acquisition_channels": acquisition_channels,
            "geographic_distribution": geographic_distribution,
            "retention_metrics": retention_metrics,
            "forecast_30_days": {
                "forecasted_users": forecasted_users,
                "forecasted_organizations": forecasted_organizations,
                "confidence_level": 75  # Mock confidence
            },
            "key_insights": [
                f"User growth rate of {user_growth_rate}% over {time_range}",
                f"Organization growth rate of {org_growth_rate}% over {time_range}",
                f"Top acquisition channel: {acquisition_channels[0]['channel']}",
                f"30-day retention rate: {retention_metrics['day_30_retention']}%"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return trends
        
    except Exception as e:
        advanced_logger.error(
            "Failed to generate growth trends",
            exception=e,
            category=ErrorCategory.SYSTEM,
            extra={"user_id": current_user.id}
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve growth trends")


@router.get("/health", response_model=SystemHealthResponse)
@log_exceptions(category=ErrorCategory.SYSTEM)
async def get_system_health(
    current_user: User = Depends(require_super_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive system health metrics leveraging optimization features.
    
    Args:
        current_user: Authenticated super admin user
        
    Returns:
        Dict containing system health status
    """
    try:
        advanced_logger.info(
            "Fetching system health metrics",
            extra={"user_id": current_user.id}
        )
        
        # Get system health from our optimization modules
        from app.core.error_handling import get_system_health, get_performance_stats
        from app.core.redis_caching import get_cache_stats
        
        # Core system health
        system_health = get_system_health()
        performance_stats = get_performance_stats()
        cache_stats = get_cache_stats()
        
        # Database health
        db_stats = db_pool_manager.get_connection_stats()
        
        # Background job health
        job_stats = job_manager.get_queue_stats()
        
        # Calculate overall health score
        health_checks = []
        
        # Database health check
        db_healthy = db_stats["status"] == "healthy"
        health_checks.append({
            "component": "Database",
            "status": "healthy" if db_healthy else "degraded",
            "score": 100 if db_healthy else 50,
            "details": f"Connection pools: {len(db_stats['pools'])}"
        })
        
        # Cache health check
        cache_healthy = cache_stats["stats"]["total_requests"] == 0 or cache_stats["stats"]["hit_rate_percent"] > 70
        health_checks.append({
            "component": "Cache",
            "status": "healthy" if cache_healthy else "warning",
            "score": 100 if cache_healthy else 75,
            "details": f"Hit rate: {cache_stats['stats']['hit_rate_percent']:.1f}%"
        })
        
        # Background jobs health check
        jobs_healthy = job_stats.get("available", False)
        health_checks.append({
            "component": "Background Jobs",
            "status": "healthy" if jobs_healthy else "warning",
            "score": 100 if jobs_healthy else 80,
            "details": f"Queues available: {len(job_stats.get('queues', []))}"
        })
        
        # Performance health check
        if "error" not in performance_stats:
            avg_response = performance_stats["request_stats"]["avg_response_time"]
            perf_healthy = avg_response < 1.0  # Less than 1 second average
            health_checks.append({
                "component": "Performance",
                "status": "healthy" if perf_healthy else "warning",
                "score": 100 if perf_healthy else 70,
                "details": f"Avg response: {avg_response:.2f}s"
            })
        
        # System resources health check
        if "error" not in performance_stats:
            cpu_percent = performance_stats["system_stats"]["cpu_percent"]
            memory_percent = performance_stats["system_stats"]["memory_percent"]
            
            resources_healthy = cpu_percent < 80 and memory_percent < 85
            health_checks.append({
                "component": "System Resources",
                "status": "healthy" if resources_healthy else "warning",
                "score": 100 if resources_healthy else 60,
                "details": f"CPU: {cpu_percent}%, Memory: {memory_percent}%"
            })
        
        # Calculate overall health score
        overall_score = sum(check["score"] for check in health_checks) / len(health_checks)
        
        if overall_score >= 90:
            overall_status = "healthy"
        elif overall_score >= 70:
            overall_status = "warning"
        else:
            overall_status = "critical"
        
        # Recent alerts (mock - would come from monitoring system)
        recent_alerts = []
        if overall_score < 90:
            recent_alerts.append({
                "id": "alert_001",
                "severity": "warning" if overall_score >= 70 else "critical",
                "message": f"System health score below optimal: {overall_score:.1f}%",
                "timestamp": datetime.utcnow().isoformat(),
                "component": "overall"
            })
        
        # System metrics summary
        health_data = {
            "overall_status": overall_status,
            "overall_score": round(overall_score, 1),
            "component_health": health_checks,
            "system_metrics": {
                "uptime_hours": 168,  # Mock uptime - 1 week
                "total_requests_24h": performance_stats.get("request_stats", {}).get("total_requests", 0),
                "error_rate_24h": len(system_health.get("errors", {}).get("top_errors", [])),
                "avg_response_time": performance_stats.get("request_stats", {}).get("avg_response_time", 0)
            },
            "performance_metrics": performance_stats,
            "cache_metrics": cache_stats,
            "database_metrics": db_stats,
            "background_job_metrics": job_stats,
            "recent_alerts": recent_alerts,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        advanced_logger.info(
            f"System health check completed - Status: {overall_status}",
            extra={
                "user_id": current_user.id,
                "health_score": overall_score,
                "component_count": len(health_checks)
            }
        )
        
        return health_data
        
    except Exception as e:
        advanced_logger.error(
            "Failed to get system health metrics",
            exception=e,
            category=ErrorCategory.SYSTEM,
            extra={"user_id": current_user.id}
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve system health metrics")


@router.get("/alerts", response_model=SystemAlertsResponse)
@log_exceptions(category=ErrorCategory.SYSTEM)
async def get_critical_alerts(
    limit: int = Query(50, description="Maximum number of alerts to return"),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical"),
    current_user: User = Depends(require_super_admin)
) -> Dict[str, Any]:
    """
    Get critical system alerts and notifications.
    
    Args:
        limit: Maximum number of alerts to return
        severity: Filter alerts by severity level
        current_user: Authenticated super admin user
        
    Returns:
        Dict containing system alerts
    """
    try:
        advanced_logger.info(
            f"Fetching system alerts - limit: {limit}, severity: {severity}",
            extra={"user_id": current_user.id}
        )
        
        # Get error summary from our error handling system
        from app.core.error_handling import get_error_summary
        error_summary = get_error_summary(24)  # Last 24 hours
        
        alerts = []
        
        # Convert errors to alerts
        for error in error_summary.get("top_errors", []):
            alert_severity = "critical" if error["count"] > 10 else "warning"
            
            if severity and alert_severity != severity:
                continue
                
            alerts.append({
                "id": f"error_{error['error_id']}",
                "type": "error",
                "severity": alert_severity,
                "title": f"Recurring Error: {error['category']}",
                "message": error["message"][:200],  # Truncate long messages
                "count": error["count"],
                "affected_users": error["affected_users"],
                "first_seen": error["last_seen"],  # Use last_seen as we don't have first_seen
                "last_seen": error["last_seen"],
                "category": error["category"],
                "component": "application"
            })
        
        # Add system health alerts
        system_health = await get_system_health(current_user)
        
        if system_health["overall_score"] < 90:
            alert_severity = "critical" if system_health["overall_score"] < 70 else "warning"
            
            if not severity or alert_severity == severity:
                alerts.append({
                    "id": "health_001",
                    "type": "system_health",
                    "severity": alert_severity,
                    "title": "System Health Below Optimal",
                    "message": f"Overall system health score: {system_health['overall_score']}%",
                    "count": 1,
                    "affected_users": 0,
                    "first_seen": datetime.utcnow().isoformat(),
                    "last_seen": datetime.utcnow().isoformat(),
                    "category": "system",
                    "component": "health_monitor"
                })
        
        # Add performance alerts
        perf_stats = system_health.get("performance_metrics", {})
        if "error" not in perf_stats:
            avg_response = perf_stats.get("request_stats", {}).get("avg_response_time", 0)
            if avg_response > 2.0:  # More than 2 seconds
                alert_severity = "critical" if avg_response > 5.0 else "warning"
                
                if not severity or alert_severity == severity:
                    alerts.append({
                        "id": "perf_001",
                        "type": "performance",
                        "severity": alert_severity,
                        "title": "High Response Times Detected",
                        "message": f"Average response time: {avg_response:.2f}s",
                        "count": 1,
                        "affected_users": 0,
                        "first_seen": datetime.utcnow().isoformat(),
                        "last_seen": datetime.utcnow().isoformat(),
                        "category": "performance",
                        "component": "api"
                    })
        
        # Add resource usage alerts
        if "system_stats" in perf_stats:
            cpu_percent = perf_stats["system_stats"].get("cpu_percent", 0)
            memory_percent = perf_stats["system_stats"].get("memory_percent", 0)
            
            if cpu_percent > 85:
                alert_severity = "critical" if cpu_percent > 95 else "warning"
                
                if not severity or alert_severity == severity:
                    alerts.append({
                        "id": "resource_cpu",
                        "type": "resource_usage",
                        "severity": alert_severity,
                        "title": "High CPU Usage",
                        "message": f"CPU usage at {cpu_percent}%",
                        "count": 1,
                        "affected_users": 0,
                        "first_seen": datetime.utcnow().isoformat(),
                        "last_seen": datetime.utcnow().isoformat(),
                        "category": "system",
                        "component": "cpu"
                    })
            
            if memory_percent > 90:
                alert_severity = "critical" if memory_percent > 95 else "warning"
                
                if not severity or alert_severity == severity:
                    alerts.append({
                        "id": "resource_memory",
                        "type": "resource_usage",
                        "severity": alert_severity,
                        "title": "High Memory Usage",
                        "message": f"Memory usage at {memory_percent}%",
                        "count": 1,
                        "affected_users": 0,
                        "first_seen": datetime.utcnow().isoformat(),
                        "last_seen": datetime.utcnow().isoformat(),
                        "category": "system",
                        "component": "memory"
                    })
        
        # Sort alerts by severity and timestamp
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda x: (severity_order.get(x["severity"], 3), x["last_seen"]), reverse=True)
        
        # Limit results
        alerts = alerts[:limit]
        
        # Calculate alert summary
        alert_counts = {"critical": 0, "warning": 0, "info": 0}
        for alert in alerts:
            alert_counts[alert["severity"]] += 1
        
        result = {
            "alerts": alerts,
            "summary": {
                "total_alerts": len(alerts),
                "critical_count": alert_counts["critical"],
                "warning_count": alert_counts["warning"],
                "info_count": alert_counts["info"],
                "last_24h_errors": error_summary.get("total_errors", 0)
            },
            "filters_applied": {
                "limit": limit,
                "severity": severity
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        advanced_logger.info(
            f"Retrieved {len(alerts)} system alerts",
            extra={
                "user_id": current_user.id,
                "alert_summary": alert_counts,
                "filters": {"limit": limit, "severity": severity}
            }
        )
        
        return result
        
    except Exception as e:
        advanced_logger.error(
            "Failed to retrieve system alerts",
            exception=e,
            category=ErrorCategory.SYSTEM,
            extra={"user_id": current_user.id}
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve system alerts")


# Background task to warm dashboard caches
@cached('dashboard_cache_warming', ttl=3600)  # Run once per hour
def warm_dashboard_caches():
    """Background task to pre-warm dashboard caches."""
    try:
        advanced_logger.info("Starting dashboard cache warming")
        
        # This would typically be called by a background job
        # For now, it's just a placeholder for the caching strategy
        
        cache_tasks = [
            ('dashboard_stats', 'platform_stats'),
            ('dashboard_revenue', 'revenue_analytics'),
            ('dashboard_growth', 'growth_trends')
        ]
        
        for cache_key, description in cache_tasks:
            # In a real implementation, you'd call the actual functions here
            # to pre-populate the cache
            advanced_logger.info(f"Cache warming: {description}")
        
        return {"status": "completed", "tasks": len(cache_tasks)}
        
    except Exception as e:
        advanced_logger.error(
            "Dashboard cache warming failed",
            exception=e,
            category=ErrorCategory.SYSTEM
        )
        return {"status": "failed", "error": str(e)}
