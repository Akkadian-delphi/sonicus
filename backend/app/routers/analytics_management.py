"""
Analytics Management API Routes

FastAPI endpoints for managing analytics data refresh and caching:
- Manual refresh triggers
- Cache management
- Analytics health monitoring
- System administration
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.db.session import get_db
from app.core.security import get_current_user, get_admin_user
from app.models.user import User
from app.services.analytics_refresh import analytics_refresh_service
from app.schemas.organization_analytics import MetricTimeRange
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analytics/refresh/{organization_id}")
async def refresh_organization_analytics(
    organization_id: str,
    background_tasks: BackgroundTasks,
    time_ranges: Optional[List[MetricTimeRange]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh analytics data for a specific organization.
    
    Triggers background refresh of usage metrics, engagement analytics,
    and other organization-specific data.
    """
    try:
        # Verify user has access to this organization
        # Note: Would implement proper authorization check here
        
        # Start refresh in background
        background_tasks.add_task(
            analytics_refresh_service.refresh_organization_usage_metrics,
            organization_id,
            time_ranges
        )
        
        logger.info(f"Triggered analytics refresh for organization {organization_id} by user {current_user.id}")
        
        return {
            "message": f"Analytics refresh started for organization {organization_id}",
            "organization_id": organization_id,
            "time_ranges": [tr.value for tr in time_ranges] if time_ranges else "default",
            "triggered_by": current_user.email,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger analytics refresh for organization {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger analytics refresh: {str(e)}"
        )


@router.post("/analytics/refresh/all")
async def refresh_all_analytics(
    background_tasks: BackgroundTasks,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Refresh analytics data for all organizations.
    Super admin only - triggers system-wide analytics refresh.
    """
    try:
        # Start system-wide refresh in background
        background_tasks.add_task(
            analytics_refresh_service.refresh_all_organizations_usage_metrics
        )
        
        logger.info(f"Triggered system-wide analytics refresh by admin user {admin_user.id}")
        
        return {
            "message": "System-wide analytics refresh started",
            "triggered_by": admin_user.email,
            "triggered_at": datetime.utcnow().isoformat(),
            "scope": "all_organizations"
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger system-wide analytics refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger system-wide refresh: {str(e)}"
        )


@router.get("/analytics/cache/statistics")
async def get_cache_statistics(
    admin_user: User = Depends(get_admin_user)
):
    """
    Get analytics cache statistics and health metrics.
    Super admin only.
    """
    try:
        stats = analytics_refresh_service.get_cache_statistics()
        
        return {
            "cache_health": stats,
            "retrieved_by": admin_user.email,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache statistics: {str(e)}"
        )


@router.post("/analytics/cache/cleanup")
async def cleanup_analytics_cache(
    background_tasks: BackgroundTasks,
    admin_user: User = Depends(get_admin_user)
):
    """
    Clean up expired analytics cache entries.
    Super admin only - removes expired cache and old logs.
    """
    try:
        # Start cleanup in background
        background_tasks.add_task(
            analytics_refresh_service.cleanup_expired_cache
        )
        
        logger.info(f"Triggered cache cleanup by admin user {admin_user.id}")
        
        return {
            "message": "Cache cleanup started",
            "triggered_by": admin_user.email,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger cache cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger cache cleanup: {str(e)}"
        )


@router.delete("/analytics/cache/{organization_id}")
async def invalidate_organization_cache(
    organization_id: str,
    metric_types: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Invalidate cached analytics for a specific organization.
    Forces fresh calculation on next request.
    """
    try:
        # Verify user has access to this organization
        # Note: Would implement proper authorization check here
        
        result = analytics_refresh_service.invalidate_organization_cache(
            organization_id, metric_types
        )
        
        logger.info(f"Invalidated cache for organization {organization_id} by user {current_user.id}")
        
        return {
            "message": f"Cache invalidated for organization {organization_id}",
            "invalidation_result": result,
            "triggered_by": current_user.email,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to invalidate cache for organization {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.get("/analytics/health")
async def get_analytics_health(
    admin_user: User = Depends(get_admin_user)
):
    """
    Get overall analytics system health status.
    Super admin only - provides system monitoring information.
    """
    try:
        # Get cache statistics for health assessment
        stats = analytics_refresh_service.get_cache_statistics()
        
        # Determine system health based on metrics
        cache_stats = stats["cache_statistics"]
        job_stats = stats["job_statistics"]
        
        health_issues = []
        
        # Check cache health
        if cache_stats["hit_rate_percentage"] < 20:
            health_issues.append("Low cache hit rate")
        
        if cache_stats["expired_entries"] > (cache_stats["total_entries"] * 0.3):
            health_issues.append("High percentage of expired cache entries")
        
        # Check job health
        if job_stats["failure_rate_percentage"] > 10:
            health_issues.append("High job failure rate")
        
        system_status = "healthy" if not health_issues else "warning"
        if job_stats["failure_rate_percentage"] > 25 or cache_stats["hit_rate_percentage"] < 10:
            system_status = "critical"
        
        health_report = {
            "system_status": system_status,
            "health_issues": health_issues,
            "cache_metrics": cache_stats,
            "job_metrics": job_stats,
            "recommendations": []
        }
        
        # Add recommendations based on issues
        if "Low cache hit rate" in health_issues:
            health_report["recommendations"].append("Consider increasing cache TTL or reviewing cache strategy")
        
        if "High percentage of expired cache entries" in health_issues:
            health_report["recommendations"].append("Run cache cleanup more frequently")
        
        if "High job failure rate" in health_issues:
            health_report["recommendations"].append("Investigate recent job failures and system issues")
        
        return {
            "analytics_health": health_report,
            "retrieved_by": admin_user.email,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics health: {str(e)}"
        )


@router.get("/analytics/jobs/recent")
async def get_recent_analytics_jobs(
    limit: int = 50,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get recent analytics job execution logs.
    Super admin only - for monitoring and debugging.
    """
    try:
        from app.models.analytics_cache import AnalyticsJobLog
        
        recent_jobs = db.query(AnalyticsJobLog).order_by(
            AnalyticsJobLog.created_at.desc()
        ).limit(limit).all()
        
        jobs_data = []
        for job in recent_jobs:
            jobs_data.append({
                "id": job.id,
                "job_name": job.job_name,
                "organization_id": job.organization_id,
                "status": job.status,
                "execution_time_ms": job.execution_time_ms,
                "execution_details": job.execution_details,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat() if getattr(job, 'updated_at', None) else None
            })
        
        return {
            "recent_jobs": jobs_data,
            "total_jobs": len(jobs_data),
            "retrieved_by": admin_user.email,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent analytics jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recent jobs: {str(e)}"
        )
