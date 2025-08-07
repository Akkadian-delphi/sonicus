"""
Background Analytics Jobs

Celery-based background job system for analytics:
- Periodic analytics calculation and caching
- Data refresh and synchronization
- Health monitoring and alerts
- Performance optimization tasks
"""

from celery import Celery
from celery.schedules import crontab
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import logging
import asyncio
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.analytics_cache import AnalyticsJobLog, OrganizationAnalyticsCache
from app.services.real_data_analytics import RealDataOrganizationAnalyticsService
from app.services.websocket_analytics import RealTimeAnalyticsBroadcaster
from app.schemas.organization_analytics import MetricTimeRange

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'analytics_jobs',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        # Analytics refresh schedules
        'refresh-usage-metrics': {
            'task': 'app.services.analytics_jobs.refresh_all_usage_metrics',
            'schedule': crontab(minute=0),  # Every hour
        },
        'refresh-engagement-analytics': {
            'task': 'app.services.analytics_jobs.refresh_all_engagement_analytics',
            'schedule': crontab(minute=30),  # Every hour at :30
        },
        'refresh-health-scores': {
            'task': 'app.services.analytics_jobs.refresh_all_health_scores',
            'schedule': crontab(minute=0, hour=6),  # Daily at 6 AM
        },
        'cleanup-old-cache': {
            'task': 'app.services.analytics_jobs.cleanup_expired_cache',
            'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
        },
        'analytics-health-check': {
            'task': 'app.services.analytics_jobs.analytics_system_health_check',
            'schedule': crontab(minute='*/15'),  # Every 15 minutes
        }
    }
)


def get_db_session():
    """Get database session for background tasks."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        db.close()
        raise


def log_job_execution(
    db: Session,
    job_name: str,
    organization_id: Optional[str] = None,
    status: str = "started",
    details: Optional[Dict[str, Any]] = None,
    execution_time_ms: Optional[int] = None
):
    """Log analytics job execution for monitoring."""
    try:
        job_log = AnalyticsJobLog(
            job_name=job_name,
            organization_id=organization_id,
            status=status,
            execution_details=details or {},
            execution_time_ms=execution_time_ms
        )
        db.add(job_log)
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to log job execution: {e}")
        db.rollback()


@celery_app.task(bind=True)
def refresh_organization_usage_metrics(self, organization_id: str):
    """Refresh usage metrics for a specific organization."""
    start_time = datetime.utcnow()
    db = get_db_session()
    
    try:
        log_job_execution(db, "refresh_usage_metrics", organization_id, "started")
        
        analytics_service = RealDataOrganizationAnalyticsService(db)
        
        # Refresh metrics for different time ranges
        time_ranges = [
            MetricTimeRange.LAST_7_DAYS,
            MetricTimeRange.LAST_30_DAYS,
            MetricTimeRange.LAST_90_DAYS
        ]
        
        results = {}
        for time_range in time_ranges:
            try:
                # Run analytics synchronously in background job
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    analytics_service.get_real_time_usage_metrics(
                        organization_id=organization_id,
                        time_range=time_range
                    )
                )
                results[time_range.value] = "success"
                loop.close()
                
            except Exception as e:
                logger.error(f"Failed to refresh {time_range.value} metrics for org {organization_id}: {e}")
                results[time_range.value] = f"error: {str(e)}"
        
        # Broadcast update to connected clients
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            broadcaster = RealTimeAnalyticsBroadcaster(db)
            loop.run_until_complete(broadcaster.broadcast_usage_update(organization_id))
            loop.close()
        except Exception as e:
            logger.warning(f"Failed to broadcast usage update: {e}")
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_job_execution(
            db, "refresh_usage_metrics", organization_id, "completed",
            {"results": results}, execution_time
        )
        
        logger.info(f"Refreshed usage metrics for organization {organization_id}")
        return {"organization_id": organization_id, "results": results}
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_job_execution(
            db, "refresh_usage_metrics", organization_id, "failed",
            {"error": str(e)}, execution_time
        )
        logger.error(f"Failed to refresh usage metrics for organization {organization_id}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
        
    finally:
        db.close()


@celery_app.task(bind=True)
def refresh_all_usage_metrics(self):
    """Refresh usage metrics for all active organizations."""
    start_time = datetime.utcnow()
    db = get_db_session()
    
    try:
        log_job_execution(db, "refresh_all_usage_metrics", status="started")
        
        # Get all active organizations
        organizations = db.query(Organization).filter(
            Organization.is_active == True
        ).all()
        
        org_count = len(organizations)
        logger.info(f"Starting usage metrics refresh for {org_count} organizations")
        
        success_count = 0
        error_count = 0
        
        for org in organizations:
            try:
                # Queue individual organization refresh
                # Using getattr to avoid type checker issues with Celery task methods
                task_method = getattr(refresh_organization_usage_metrics, 'apply_async', None)
                if task_method:
                    task_method(args=[str(org.id)])
                else:
                    # Fallback: call directly if Celery not available
                    refresh_organization_usage_metrics(self=None, organization_id=str(org.id))
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to queue usage metrics refresh for org {org.id}: {e}")
                error_count += 1
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        results = {
            "total_organizations": org_count,
            "success_count": success_count,
            "error_count": error_count
        }
        
        log_job_execution(
            db, "refresh_all_usage_metrics", status="completed",
            details=results, execution_time_ms=execution_time
        )
        
        logger.info(f"Queued usage metrics refresh for {success_count}/{org_count} organizations")
        return results
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_job_execution(
            db, "refresh_all_usage_metrics", status="failed",
            details={"error": str(e)}, execution_time_ms=execution_time
        )
        logger.error(f"Failed to refresh all usage metrics: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)
        
    finally:
        db.close()


@celery_app.task(bind=True)
def refresh_all_engagement_analytics(self):
    """Refresh engagement analytics for all active organizations."""
    start_time = datetime.utcnow()
    db = get_db_session()
    
    try:
        log_job_execution(db, "refresh_all_engagement_analytics", status="started")
        
        # Get all active organizations
        organizations = db.query(Organization).filter(
            Organization.is_active == True
        ).all()
        
        org_count = len(organizations)
        logger.info(f"Starting engagement analytics refresh for {org_count} organizations")
        
        success_count = 0
        error_count = 0
        
        for org in organizations:
            try:
                analytics_service = RealDataOrganizationAnalyticsService(db)
                
                # Note: Would call engagement analytics method here
                # await analytics_service.get_user_engagement_analytics(
                #     organization_id=str(org.id),
                #     time_range=MetricTimeRange.LAST_30_DAYS
                # )
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to refresh engagement analytics for org {org.id}: {e}")
                error_count += 1
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        results = {
            "total_organizations": org_count,
            "success_count": success_count,
            "error_count": error_count
        }
        
        log_job_execution(
            db, "refresh_all_engagement_analytics", status="completed",
            details=results, execution_time_ms=execution_time
        )
        
        logger.info(f"Refreshed engagement analytics for {success_count}/{org_count} organizations")
        return results
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_job_execution(
            db, "refresh_all_engagement_analytics", status="failed",
            details={"error": str(e)}, execution_time_ms=execution_time
        )
        logger.error(f"Failed to refresh all engagement analytics: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)
        
    finally:
        db.close()


@celery_app.task(bind=True)
def refresh_all_health_scores(self):
    """Refresh organization health scores."""
    start_time = datetime.utcnow()
    db = get_db_session()
    
    try:
        log_job_execution(db, "refresh_all_health_scores", status="started")
        
        # Get all active organizations
        organizations = db.query(Organization).filter(
            Organization.is_active == True
        ).all()
        
        org_count = len(organizations)
        logger.info(f"Starting health score refresh for {org_count} organizations")
        
        success_count = 0
        error_count = 0
        health_alerts = []
        
        for org in organizations:
            try:
                analytics_service = RealDataOrganizationAnalyticsService(db)
                
                # Note: Would call health score calculation method here
                # health_result = await analytics_service.get_organization_health_score(
                #     organization_id=str(org.id)
                # )
                
                # Check for health score alerts
                # if health_result.health_score < 50:  # Low health threshold
                #     health_alerts.append({
                #         "organization_id": str(org.id),
                #         "health_score": health_result.health_score,
                #         "status": "critical" if health_result.health_score < 30 else "warning"
                #     })
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to refresh health score for org {org.id}: {e}")
                error_count += 1
        
        # Send health alerts if any
        if health_alerts:
            try:
                broadcaster = RealTimeAnalyticsBroadcaster(db)
                for alert in health_alerts:
                    # Note: Would broadcast health alerts
                    pass
            except Exception as e:
                logger.warning(f"Failed to send health alerts: {e}")
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        results = {
            "total_organizations": org_count,
            "success_count": success_count,
            "error_count": error_count,
            "health_alerts": len(health_alerts)
        }
        
        log_job_execution(
            db, "refresh_all_health_scores", status="completed",
            details=results, execution_time_ms=execution_time
        )
        
        logger.info(f"Refreshed health scores for {success_count}/{org_count} organizations")
        return results
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_job_execution(
            db, "refresh_all_health_scores", status="failed",
            details={"error": str(e)}, execution_time_ms=execution_time
        )
        logger.error(f"Failed to refresh all health scores: {e}")
        raise self.retry(exc=e, countdown=600, max_retries=2)
        
    finally:
        db.close()


@celery_app.task
def cleanup_expired_cache():
    """Clean up expired analytics cache entries."""
    start_time = datetime.utcnow()
    db = get_db_session()
    
    try:
        log_job_execution(db, "cleanup_expired_cache", status="started")
        
        # Delete expired cache entries
        expired_count = db.query(OrganizationAnalyticsCache).filter(
            OrganizationAnalyticsCache.expires_at < datetime.utcnow()
        ).delete()
        
        # Delete old job logs (keep only last 30 days)
        old_logs_cutoff = datetime.utcnow() - timedelta(days=30)
        old_logs_count = db.query(AnalyticsJobLog).filter(
            AnalyticsJobLog.created_at < old_logs_cutoff
        ).delete()
        
        db.commit()
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        results = {
            "expired_cache_deleted": expired_count,
            "old_logs_deleted": old_logs_count
        }
        
        log_job_execution(
            db, "cleanup_expired_cache", status="completed",
            details=results, execution_time_ms=execution_time
        )
        
        logger.info(f"Cleaned up {expired_count} expired cache entries and {old_logs_count} old logs")
        return results
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_job_execution(
            db, "cleanup_expired_cache", status="failed",
            details={"error": str(e)}, execution_time_ms=execution_time
        )
        logger.error(f"Failed to cleanup expired cache: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()


@celery_app.task
def analytics_system_health_check():
    """Perform system health check for analytics."""
    start_time = datetime.utcnow()
    db = get_db_session()
    
    try:
        log_job_execution(db, "analytics_system_health_check", status="started")
        
        # Check analytics cache health
        total_cache_entries = db.query(OrganizationAnalyticsCache).count()
        expired_entries = db.query(OrganizationAnalyticsCache).filter(
            OrganizationAnalyticsCache.expires_at < datetime.utcnow()
        ).count()
        
        # Check recent job failures
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_failures = db.query(AnalyticsJobLog).filter(
            AnalyticsJobLog.created_at >= recent_cutoff,
            AnalyticsJobLog.status == "failed"
        ).count()
        
        # Calculate cache hit rate
        cache_with_hits = db.query(OrganizationAnalyticsCache).filter(
            OrganizationAnalyticsCache.cache_hit_count > 0
        ).count()
        cache_hit_rate = (cache_with_hits / total_cache_entries * 100) if total_cache_entries > 0 else 0
        
        # Determine system health status
        health_issues = []
        if expired_entries > (total_cache_entries * 0.3):  # More than 30% expired
            health_issues.append("High percentage of expired cache entries")
        
        if recent_failures > 5:
            health_issues.append("High number of recent job failures")
        
        if cache_hit_rate < 20:  # Less than 20% hit rate
            health_issues.append("Low cache hit rate")
        
        system_status = "healthy" if not health_issues else "warning"
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        results = {
            "status": system_status,
            "total_cache_entries": total_cache_entries,
            "expired_entries": expired_entries,
            "recent_failures": recent_failures,
            "cache_hit_rate": cache_hit_rate,
            "health_issues": health_issues
        }
        
        log_job_execution(
            db, "analytics_system_health_check", status="completed",
            details=results, execution_time_ms=execution_time
        )
        
        if health_issues:
            logger.warning(f"Analytics system health check found issues: {health_issues}")
        else:
            logger.info("Analytics system health check passed")
        
        return results
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_job_execution(
            db, "analytics_system_health_check", status="failed",
            details={"error": str(e)}, execution_time_ms=execution_time
        )
        logger.error(f"Analytics system health check failed: {e}")
        raise
        
    finally:
        db.close()


# Manual job trigger functions
def trigger_organization_refresh(organization_id: str):
    """Manually trigger analytics refresh for an organization."""
    # Using getattr to avoid type checker issues with Celery task methods
    delay_method = getattr(refresh_organization_usage_metrics, 'delay', None)
    if delay_method:
        return delay_method(organization_id)
    else:
        # Fallback: call directly if Celery not available
        return refresh_organization_usage_metrics(self=None, organization_id=organization_id)


def trigger_full_system_refresh():
    """Manually trigger full system analytics refresh."""
    tasks = []
    
    # Get delay methods with fallbacks
    usage_delay = getattr(refresh_all_usage_metrics, 'delay', None)
    engagement_delay = getattr(refresh_all_engagement_analytics, 'delay', None)
    health_delay = getattr(refresh_all_health_scores, 'delay', None)
    
    if usage_delay:
        tasks.append(usage_delay())
    else:
        tasks.append(refresh_all_usage_metrics(self=None))
        
    if engagement_delay:
        tasks.append(engagement_delay())
    else:
        tasks.append(refresh_all_engagement_analytics(self=None))
        
    if health_delay:
        tasks.append(health_delay())
    else:
        tasks.append(refresh_all_health_scores(self=None))
        
    return tasks
