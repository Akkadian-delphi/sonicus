"""
Analytics Data Refresh Service

Simple service for refreshing analytics data without Celery complexity:
- Manual analytics refresh triggers
- Data synchronization utilities
- Cache management functions
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
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


class AnalyticsRefreshService:
    """Service for refreshing and managing analytics data."""
    
    def __init__(self):
        self.db_session = SessionLocal
    
    def get_db(self) -> Session:
        """Get database session."""
        return self.db_session()
    
    def log_operation(
        self,
        db: Session,
        operation: str,
        organization_id: Optional[str] = None,
        status: str = "started",
        details: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None
    ):
        """Log analytics operation for monitoring."""
        try:
            job_log = AnalyticsJobLog(
                job_name=operation,
                organization_id=organization_id,
                status=status,
                execution_details=details or {},
                execution_time_ms=execution_time_ms
            )
            db.add(job_log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log operation: {e}")
            db.rollback()
    
    async def refresh_organization_usage_metrics(
        self, 
        organization_id: str,
        time_ranges: Optional[List[MetricTimeRange]] = None
    ) -> Dict[str, Any]:
        """Refresh usage metrics for a specific organization."""
        start_time = datetime.utcnow()
        db = self.get_db()
        
        try:
            self.log_operation(db, "refresh_usage_metrics", organization_id, "started")
            
            analytics_service = RealDataOrganizationAnalyticsService(db)
            
            # Default time ranges if not specified
            if time_ranges is None:
                time_ranges = [
                    MetricTimeRange.LAST_7_DAYS,
                    MetricTimeRange.LAST_30_DAYS,
                    MetricTimeRange.LAST_90_DAYS
                ]
            
            results = {}
            for time_range in time_ranges:
                try:
                    result = await analytics_service.get_real_time_usage_metrics(
                        organization_id=organization_id,
                        time_range=time_range
                    )
                    results[time_range.value] = {
                        "status": "success",
                        "total_sessions": result.usage_metrics.total_sessions,
                        "total_minutes": result.usage_metrics.total_minutes_listened,
                        "unique_users": result.usage_metrics.unique_active_users
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to refresh {time_range.value} metrics for org {organization_id}: {e}")
                    results[time_range.value] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Broadcast update to connected clients
            try:
                broadcaster = RealTimeAnalyticsBroadcaster(db)
                await broadcaster.broadcast_usage_update(organization_id)
            except Exception as e:
                logger.warning(f"Failed to broadcast update: {e}")
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self.log_operation(
                db, "refresh_usage_metrics", organization_id, "completed",
                {"results": results}, execution_time
            )
            
            logger.info(f"Refreshed usage metrics for organization {organization_id}")
            return {
                "organization_id": organization_id,
                "execution_time_ms": execution_time,
                "results": results
            }
            
        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self.log_operation(
                db, "refresh_usage_metrics", organization_id, "failed",
                {"error": str(e)}, execution_time
            )
            logger.error(f"Failed to refresh usage metrics for organization {organization_id}: {e}")
            raise
            
        finally:
            db.close()
    
    async def refresh_all_organizations_usage_metrics(self) -> Dict[str, Any]:
        """Refresh usage metrics for all active organizations."""
        start_time = datetime.utcnow()
        db = self.get_db()
        
        try:
            self.log_operation(db, "refresh_all_usage_metrics", status="started")
            
            # Get all active organizations
            organizations = db.query(Organization).filter(
                Organization.is_active == True
            ).all()
            
            org_count = len(organizations)
            logger.info(f"Starting usage metrics refresh for {org_count} organizations")
            
            results = []
            success_count = 0
            error_count = 0
            
            for org in organizations:
                try:
                    org_result = await self.refresh_organization_usage_metrics(str(org.id))
                    results.append(org_result)
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to refresh metrics for org {org.id}: {e}")
                    results.append({
                        "organization_id": str(org.id),
                        "status": "error",
                        "error": str(e)
                    })
                    error_count += 1
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            summary = {
                "total_organizations": org_count,
                "success_count": success_count,
                "error_count": error_count,
                "execution_time_ms": execution_time,
                "results": results
            }
            
            self.log_operation(
                db, "refresh_all_usage_metrics", status="completed",
                details=summary, execution_time_ms=execution_time
            )
            
            logger.info(f"Completed usage metrics refresh: {success_count}/{org_count} successful")
            return summary
            
        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self.log_operation(
                db, "refresh_all_usage_metrics", status="failed",
                details={"error": str(e)}, execution_time_ms=execution_time
            )
            logger.error(f"Failed to refresh all usage metrics: {e}")
            raise
            
        finally:
            db.close()
    
    def cleanup_expired_cache(self) -> Dict[str, Any]:
        """Clean up expired analytics cache entries."""
        start_time = datetime.utcnow()
        db = self.get_db()
        
        try:
            self.log_operation(db, "cleanup_expired_cache", status="started")
            
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
                "old_logs_deleted": old_logs_count,
                "execution_time_ms": execution_time
            }
            
            self.log_operation(
                db, "cleanup_expired_cache", status="completed",
                details=results, execution_time_ms=execution_time
            )
            
            logger.info(f"Cleaned up {expired_count} expired cache entries and {old_logs_count} old logs")
            return results
            
        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self.log_operation(
                db, "cleanup_expired_cache", status="failed",
                details={"error": str(e)}, execution_time_ms=execution_time
            )
            logger.error(f"Failed to cleanup expired cache: {e}")
            db.rollback()
            raise
            
        finally:
            db.close()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get analytics cache statistics."""
        db = self.get_db()
        
        try:
            # Cache statistics
            total_cache_entries = db.query(OrganizationAnalyticsCache).count()
            expired_entries = db.query(OrganizationAnalyticsCache).filter(
                OrganizationAnalyticsCache.expires_at < datetime.utcnow()
            ).count()
            
            # Cache hit statistics
            cache_with_hits = db.query(OrganizationAnalyticsCache).filter(
                OrganizationAnalyticsCache.cache_hit_count > 0
            ).count()
            
            # Recent job statistics
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_jobs = db.query(AnalyticsJobLog).filter(
                AnalyticsJobLog.created_at >= recent_cutoff
            ).count()
            
            recent_failures = db.query(AnalyticsJobLog).filter(
                AnalyticsJobLog.created_at >= recent_cutoff,
                AnalyticsJobLog.status == "failed"
            ).count()
            
            cache_hit_rate = (cache_with_hits / total_cache_entries * 100) if total_cache_entries > 0 else 0
            failure_rate = (recent_failures / recent_jobs * 100) if recent_jobs > 0 else 0
            
            return {
                "cache_statistics": {
                    "total_entries": total_cache_entries,
                    "expired_entries": expired_entries,
                    "entries_with_hits": cache_with_hits,
                    "hit_rate_percentage": round(cache_hit_rate, 2)
                },
                "job_statistics": {
                    "recent_jobs_24h": recent_jobs,
                    "recent_failures_24h": recent_failures,
                    "failure_rate_percentage": round(failure_rate, 2)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            raise
            
        finally:
            db.close()
    
    def invalidate_organization_cache(self, organization_id: str, metric_types: Optional[List[str]] = None):
        """Invalidate cached analytics for an organization."""
        db = self.get_db()
        
        try:
            query = db.query(OrganizationAnalyticsCache).filter(
                OrganizationAnalyticsCache.organization_id == organization_id
            )
            
            if metric_types:
                query = query.filter(OrganizationAnalyticsCache.metric_type.in_(metric_types))
            
            invalidated_count = query.update({
                "is_stale": True,
                "invalidated_at": datetime.utcnow()
            })
            
            db.commit()
            
            logger.info(f"Invalidated {invalidated_count} cache entries for organization {organization_id}")
            return {
                "organization_id": organization_id,
                "invalidated_count": invalidated_count,
                "metric_types": metric_types or "all"
            }
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            db.rollback()
            raise
            
        finally:
            db.close()


# Global service instance
analytics_refresh_service = AnalyticsRefreshService()
