"""
Organization Analytics Cache Model

Caches computed analytics for performance optimization.
"""

from sqlalchemy import Column, String, DateTime, Float, Integer, JSON, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class OrganizationAnalyticsCache(Base):
    """Cached analytics data for organizations."""
    __tablename__ = "organization_analytics_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Cache metadata
    metric_type = Column(String(50), nullable=False, index=True)  # "usage", "engagement", "revenue", "content", "health"
    time_range = Column(String(20), nullable=False)  # "7d", "30d", "90d", "1y", "custom"
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Cached data
    metric_data = Column(JSON, nullable=False)  # Serialized analytics data
    summary_stats = Column(JSON, nullable=True)  # Key summary statistics
    
    # Performance metadata
    calculation_time_ms = Column(Integer, nullable=True)  # Time taken to calculate
    data_points_count = Column(Integer, nullable=True)   # Number of data points processed
    confidence_score = Column(Float, nullable=True)      # 0-100 data quality score
    
    # Cache management
    cache_hit_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=False)
    is_stale = Column(Boolean, default=False, nullable=False)
    invalidated_at = Column(DateTime, nullable=True)
    
    # Version tracking
    cache_version = Column(String(20), default="1.0")
    calculation_method = Column(String(100), nullable=True)  # Algorithm used
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # organization = relationship("Organization", back_populates="analytics_cache")  # Temporarily disabled to fix login


class PlatformAnalyticsSummary(Base):
    """Platform-wide analytics summary for super admin dashboard."""
    __tablename__ = "platform_analytics_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    summary_date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # "daily", "weekly", "monthly"
    
    # Platform metrics
    total_organizations = Column(Integer, default=0)
    active_organizations = Column(Integer, default=0)
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    
    # Usage metrics
    total_sessions = Column(Integer, default=0)
    total_listening_minutes = Column(Float, default=0.0)
    average_session_duration = Column(Float, default=0.0)
    content_plays = Column(Integer, default=0)
    
    # Revenue metrics
    total_revenue = Column(Float, default=0.0)
    subscription_revenue = Column(Float, default=0.0)
    usage_revenue = Column(Float, default=0.0)
    new_subscriptions = Column(Integer, default=0)
    churned_subscriptions = Column(Integer, default=0)
    
    # Health metrics
    average_health_score = Column(Float, default=0.0)
    organizations_at_risk = Column(Integer, default=0)  # Health score < 50
    high_performing_orgs = Column(Integer, default=0)   # Health score > 80
    
    # Growth metrics
    user_growth_rate = Column(Float, default=0.0)      # Percentage
    revenue_growth_rate = Column(Float, default=0.0)   # Percentage
    organization_growth_rate = Column(Float, default=0.0) # Percentage
    
    # Trends
    top_content_categories = Column(JSON, nullable=True) # Top categories by usage
    geographic_distribution = Column(JSON, nullable=True) # Usage by region
    device_distribution = Column(JSON, nullable=True)    # Usage by device type
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalyticsJobLog(Base):
    """Log of analytics calculation jobs for monitoring."""
    __tablename__ = "analytics_job_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Job details
    job_type = Column(String(50), nullable=False)  # "daily_metrics", "weekly_summary", etc.
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    # Execution details
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")  # "running", "completed", "failed", "cancelled"
    
    # Performance metrics
    duration_seconds = Column(Float, nullable=True)
    records_processed = Column(Integer, nullable=True)
    memory_used_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    
    # Results
    result_summary = Column(JSON, nullable=True)
    cache_entries_created = Column(Integer, default=0)
    cache_entries_updated = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # organization = relationship("Organization", back_populates="analytics_jobs")  # Temporarily disabled to fix login
