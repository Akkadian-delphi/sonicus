"""
Real Data Organization Analytics Service - Fixed Version

Production analytics service using actual database data with proper SQLAlchemy handling.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text, desc, case
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
import logging
import uuid
from collections import defaultdict
import statistics
import json

from app.models.organization import Organization, OrganizationStatus, SubscriptionTier
from app.models.user import User, UserRole
from app.models.therapy_sound import TherapySound
from app.models.user_session import UserSession, ContentPlay, UserEngagementMetric
from app.models.analytics_cache import OrganizationAnalyticsCache, PlatformAnalyticsSummary
from app.models.invoice import Invoice
from app.models.subscription import Subscription

from app.schemas.organization_analytics import (
    MetricTimeRange, EngagementLevel, HealthStatus,
    UsageMetricPoint, UsageMetrics, RealTimeUsageMetrics,
    UserEngagementData, EngagementAnalytics, UserEngagementAnalyticsResponse,
    RevenueBreakdown, RevenueMetrics, RevenueAttributionResponse,
    ContentUsagePattern, ContentRecommendation, ContentUsageAnalytics,
    ContentUsageAnalyticsResponse, HealthFactor, OrganizationHealthMetrics,
    OrganizationHealthScoreResponse, ComprehensiveAnalytics,
    ComprehensiveAnalyticsResponse, OrganizationAnalyticsSummary,
    BulkAnalyticsResponse, AnalyticsFilters
)

logger = logging.getLogger(__name__)


class RealDataOrganizationAnalyticsService:
    """Service class for real-data organization analytics operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _safe_get_value(self, obj, attr, default=None):
        """Safely get value from SQLAlchemy model attribute."""
        try:
            value = getattr(obj, attr)
            return value if value is not None else default
        except:
            return default
    
    def _safe_get_str(self, obj, attr, default=""):
        """Safely get string value from SQLAlchemy model attribute."""
        try:
            value = getattr(obj, attr)
            return str(value) if value is not None else default
        except:
            return default
    
    def _safe_float(self, value, default=0.0):
        """Safely convert value to float."""
        try:
            return float(value) if value is not None else default
        except:
            return default
    
    def _safe_int(self, value, default=0):
        """Safely convert value to int."""
        try:
            return int(value) if value is not None else default
        except:
            return default
    
    # ==================== CACHE MANAGEMENT ====================
    
    def _get_cached_metrics(
        self, 
        organization_id: str, 
        metric_type: str, 
        time_range: MetricTimeRange,
        start_date: date,
        end_date: date
    ) -> Optional[Dict[str, Any]]:
        """Get cached analytics if available and not expired."""
        try:
            cache_entry = self.db.query(OrganizationAnalyticsCache).filter(
                OrganizationAnalyticsCache.organization_id == organization_id,
                OrganizationAnalyticsCache.metric_type == metric_type,
                OrganizationAnalyticsCache.time_range == time_range.value,
                OrganizationAnalyticsCache.period_start == start_date,
                OrganizationAnalyticsCache.period_end == end_date,
                OrganizationAnalyticsCache.expires_at > datetime.utcnow(),
                OrganizationAnalyticsCache.is_stale == False
            ).first()
            
            if cache_entry:
                # Update hit count properly
                self.db.query(OrganizationAnalyticsCache).filter(
                    OrganizationAnalyticsCache.id == cache_entry.id
                ).update({"cache_hit_count": OrganizationAnalyticsCache.cache_hit_count + 1})
                self.db.commit()
                logger.info(f"Cache hit for {metric_type} metrics for organization {organization_id}")
                
                # Return the actual metric data value
                return self._safe_get_value(cache_entry, 'metric_data', {})
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached metrics: {e}")
            return None
    
    def _cache_metrics(
        self,
        organization_id: str,
        metric_type: str,
        time_range: MetricTimeRange,
        start_date: date,
        end_date: date,
        data: Dict[str, Any],
        calculation_time_ms: Optional[int] = None
    ):
        """Cache analytics data for future use."""
        try:
            # Remove old cache entries for same parameters
            self.db.query(OrganizationAnalyticsCache).filter(
                OrganizationAnalyticsCache.organization_id == organization_id,
                OrganizationAnalyticsCache.metric_type == metric_type,
                OrganizationAnalyticsCache.time_range == time_range.value,
                OrganizationAnalyticsCache.period_start == start_date,
                OrganizationAnalyticsCache.period_end == end_date
            ).delete()
            
            # Calculate expiry time based on metric type
            if metric_type == "usage":
                expires_in_hours = 1  # Real-time metrics expire quickly
            elif metric_type == "engagement":
                expires_in_hours = 6  # Engagement updates less frequently
            elif metric_type == "health":
                expires_in_hours = 24  # Health scores update daily
            else:
                expires_in_hours = 12  # Default cache duration
            
            cache_entry = OrganizationAnalyticsCache(
                organization_id=organization_id,
                metric_type=metric_type,
                time_range=time_range.value,
                period_start=start_date,
                period_end=end_date,
                metric_data=data,
                calculation_time_ms=calculation_time_ms,
                expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
                cache_version="2.0"
            )
            
            self.db.add(cache_entry)
            self.db.commit()
            logger.info(f"Cached {metric_type} metrics for organization {organization_id}")
            
        except Exception as e:
            logger.error(f"Error caching metrics: {e}")
            self.db.rollback()
    
    # ==================== DATE RANGE HELPERS ====================
    
    def _get_date_range(self, time_range: MetricTimeRange, 
                       start_date: Optional[date] = None,
                       end_date: Optional[date] = None) -> Tuple[date, date]:
        """Get start and end dates based on time range."""
        today = date.today()
        
        if time_range == MetricTimeRange.CUSTOM and start_date and end_date:
            return start_date, end_date
        
        if time_range == MetricTimeRange.LAST_7_DAYS:
            return today - timedelta(days=7), today
        elif time_range == MetricTimeRange.LAST_30_DAYS:
            return today - timedelta(days=30), today
        elif time_range == MetricTimeRange.LAST_90_DAYS:
            return today - timedelta(days=90), today
        elif time_range == MetricTimeRange.LAST_YEAR:
            return today - timedelta(days=365), today
        else:
            return today - timedelta(days=30), today
    
    def _generate_date_series(self, start_date: date, end_date: date) -> List[date]:
        """Generate list of dates between start and end date."""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates
    
    # ==================== REAL USAGE METRICS ====================
    
    async def get_real_time_usage_metrics(
        self, 
        organization_id: str,
        time_range: MetricTimeRange = MetricTimeRange.LAST_30_DAYS,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> RealTimeUsageMetrics:
        """Get real-time usage metrics from actual user session data."""
        start_time = datetime.utcnow()
        
        try:
            # Get organization
            organization = self.db.query(Organization).filter(
                Organization.id == organization_id
            ).first()
            
            if not organization:
                raise ValueError(f"Organization {organization_id} not found")
            
            start_dt, end_dt = self._get_date_range(time_range, start_date, end_date)
            
            # Check cache first
            cached_data = self._get_cached_metrics(
                organization_id, "usage", time_range, start_dt, end_dt
            )
            if cached_data:
                return RealTimeUsageMetrics(**cached_data)
            
            # Calculate date range for queries
            start_datetime = datetime.combine(start_dt, datetime.min.time())
            end_datetime = datetime.combine(end_dt, datetime.max.time())
            
            # Query real session data
            sessions = self.db.query(UserSession).filter(
                UserSession.organization_id == organization_id,
                UserSession.session_start >= start_datetime,
                UserSession.session_start <= end_datetime
            ).all()
            
            total_sessions = len(sessions)
            
            if total_sessions == 0:
                # Return empty metrics if no data
                empty_dates = self._generate_date_series(start_dt, end_dt)
                empty_metrics = UsageMetrics(
                    total_sessions=0,
                    total_minutes_listened=0.0,
                    unique_active_users=0,
                    average_session_duration=0.0,
                    most_popular_content_id=None,
                    most_popular_content_title="No content played",
                    peak_usage_hour=None,
                    sessions_by_day=[UsageMetricPoint(date=dt, value=0) for dt in empty_dates],
                    minutes_by_day=[UsageMetricPoint(date=dt, value=0) for dt in empty_dates],
                    users_by_day=[UsageMetricPoint(date=dt, value=0) for dt in empty_dates]
                )
                
                result = RealTimeUsageMetrics(
                    organization_id=organization_id,
                    organization_name=self._safe_get_str(organization, 'name', 'Unknown Organization'),
                    time_range=time_range,
                    start_date=start_dt,
                    end_date=end_dt,
                    usage_metrics=empty_metrics,
                    compared_to_previous_period=None,
                    generated_at=datetime.utcnow()
                )
                
                return result
            
            # Calculate total listening time and average session duration
            total_minutes = 0.0
            valid_durations = []
            
            for session in sessions:
                listening_time = self._safe_float(self._safe_get_value(session, 'total_listening_time', 0))
                total_minutes += listening_time
                
                duration = self._safe_float(self._safe_get_value(session, 'duration_minutes'))
                if duration and duration > 0:
                    valid_durations.append(duration)
            
            avg_session_duration = statistics.mean(valid_durations) if valid_durations else 0.0
            
            # Count unique active users
            unique_user_ids = set()
            for session in sessions:
                user_id = self._safe_get_value(session, 'user_id')
                if user_id:
                    unique_user_ids.add(user_id)
            unique_active_users = len(unique_user_ids)
            
            # Find most popular content
            content_plays = self.db.query(ContentPlay).filter(
                ContentPlay.organization_id == organization_id,
                ContentPlay.play_start >= start_datetime,
                ContentPlay.play_start <= end_datetime
            ).all()
            
            if content_plays:
                # Count plays per content
                play_counts = defaultdict(int)
                for play in content_plays:
                    content_id = self._safe_get_value(play, 'content_id')
                    if content_id:
                        play_counts[content_id] += 1
                
                if play_counts:
                    most_popular_content_id = max(play_counts.keys(), key=lambda k: play_counts[k])
                    most_popular_content = self.db.query(TherapySound).filter(
                        TherapySound.id == most_popular_content_id
                    ).first()
                    most_popular_content_title = self._safe_get_value(most_popular_content, 'title', 'Unknown Content') if most_popular_content else 'Unknown Content'
                    most_popular_content_id = str(most_popular_content_id)
                else:
                    most_popular_content_id = None
                    most_popular_content_title = "No content played"
            else:
                most_popular_content_id = None
                most_popular_content_title = "No content played"
            
            # Calculate peak usage hour
            hourly_sessions = defaultdict(int)
            for session in sessions:
                start_time_val = self._safe_get_value(session, 'session_start')
                if start_time_val:
                    hour = start_time_val.hour
                    hourly_sessions[hour] += 1
            
            peak_usage_hour = max(hourly_sessions.keys(), key=lambda k: hourly_sessions[k]) if hourly_sessions else None
            
            # Generate daily data points
            dates = self._generate_date_series(start_dt, end_dt)
            sessions_by_day = []
            minutes_by_day = []
            users_by_day = []
            
            for dt in dates:
                day_start = datetime.combine(dt, datetime.min.time())
                day_end = datetime.combine(dt, datetime.max.time())
                
                day_session_count = 0
                day_minutes = 0.0
                day_user_ids = set()
                
                for session in sessions:
                    session_start = self._safe_get_value(session, 'session_start')
                    if session_start and day_start <= session_start <= day_end:
                        day_session_count += 1
                        day_minutes += self._safe_float(self._safe_get_value(session, 'total_listening_time', 0))
                        user_id = self._safe_get_value(session, 'user_id')
                        if user_id:
                            day_user_ids.add(user_id)
                
                sessions_by_day.append(UsageMetricPoint(date=dt, value=day_session_count))
                minutes_by_day.append(UsageMetricPoint(date=dt, value=day_minutes))
                users_by_day.append(UsageMetricPoint(date=dt, value=len(day_user_ids)))
            
            usage_metrics = UsageMetrics(
                total_sessions=total_sessions,
                total_minutes_listened=total_minutes,
                unique_active_users=unique_active_users,
                average_session_duration=avg_session_duration,
                most_popular_content_id=most_popular_content_id,
                most_popular_content_title=most_popular_content_title,
                peak_usage_hour=peak_usage_hour,
                sessions_by_day=sessions_by_day,
                minutes_by_day=minutes_by_day,
                users_by_day=users_by_day
            )
            
            # Calculate comparison to previous period
            prev_start_dt = start_dt - (end_dt - start_dt)
            prev_end_dt = start_dt
            
            prev_start_datetime = datetime.combine(prev_start_dt, datetime.min.time())
            prev_end_datetime = datetime.combine(prev_end_dt, datetime.max.time())
            
            prev_sessions = self.db.query(UserSession).filter(
                UserSession.organization_id == organization_id,
                UserSession.session_start >= prev_start_datetime,
                UserSession.session_start <= prev_end_datetime
            ).all()
            
            prev_total_sessions = len(prev_sessions)
            prev_total_minutes = sum(self._safe_float(self._safe_get_value(s, 'total_listening_time', 0)) for s in prev_sessions)
            prev_active_users = len(set(self._safe_get_value(s, 'user_id') for s in prev_sessions if self._safe_get_value(s, 'user_id')))
            
            comparison = {
                "sessions_growth": ((total_sessions - prev_total_sessions) / prev_total_sessions * 100) if prev_total_sessions > 0 else 0,
                "minutes_growth": ((total_minutes - prev_total_minutes) / prev_total_minutes * 100) if prev_total_minutes > 0 else 0,
                "users_growth": ((unique_active_users - prev_active_users) / prev_active_users * 100) if prev_active_users > 0 else 0,
            }
            
            result = RealTimeUsageMetrics(
                organization_id=organization_id,
                organization_name=self._safe_get_str(organization, 'name', 'Unknown Organization'),
                time_range=time_range,
                start_date=start_dt,
                end_date=end_dt,
                usage_metrics=usage_metrics,
                compared_to_previous_period=comparison,
                generated_at=datetime.utcnow()
            )
            
            # Cache the result
            calculation_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._cache_metrics(
                organization_id, "usage", time_range, start_dt, end_dt,
                result.dict(), calculation_time
            )
            
            return result

        except Exception as e:
            logger.error(f"Error getting real usage metrics for organization {organization_id}: {e}")
            raise
    
    # ==================== INVALIDATE CACHE ====================
    
    def invalidate_organization_cache(self, organization_id: str, metric_types: Optional[List[str]] = None):
        """Invalidate cached analytics for an organization."""
        try:
            query = self.db.query(OrganizationAnalyticsCache).filter(
                OrganizationAnalyticsCache.organization_id == organization_id
            )
            
            if metric_types:
                query = query.filter(OrganizationAnalyticsCache.metric_type.in_(metric_types))
            
            query.update({
                "is_stale": True,
                "invalidated_at": datetime.utcnow()
            })
            
            self.db.commit()
            logger.info(f"Invalidated cache for organization {organization_id}, types: {metric_types}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            self.db.rollback()
