"""
Dashboard Metrics API Schemas

Pydantic models for Super Admin dashboard API responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class TimeRangeEnum(str, Enum):
    """Supported time ranges for analytics"""
    ONE_DAY = "1d"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"
    ONE_YEAR = "1y"


class BreakdownEnum(str, Enum):
    """Supported data breakdown types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AlertSeverityEnum(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class HealthStatusEnum(str, Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DEGRADED = "degraded"


# Platform Stats Schemas
class PlatformOverview(BaseModel):
    """Platform overview metrics"""
    total_users: int = Field(..., description="Total registered users")
    total_organizations: int = Field(..., description="Total organizations")
    active_subscriptions: int = Field(..., description="Active paid subscriptions")
    total_sounds: int = Field(..., description="Total therapy sounds available")
    total_revenue: float = Field(..., description="Total revenue generated")
    revenue_growth_percent: float = Field(..., description="Revenue growth percentage")


class GrowthMetrics(BaseModel):
    """Growth metrics for specified time range"""
    time_range: str = Field(..., description="Time range analyzed")
    new_users: int = Field(..., description="New users in time range")
    new_organizations: int = Field(..., description="New organizations in time range")
    user_growth_rate: float = Field(..., description="User growth rate percentage")
    org_growth_rate: float = Field(..., description="Organization growth rate percentage")


class ContentCategory(BaseModel):
    """Popular content category"""
    name: str = Field(..., description="Category name")
    plays: int = Field(..., description="Number of plays")


class EngagementMetrics(BaseModel):
    """User engagement metrics"""
    daily_active_users: int = Field(..., description="Daily active users")
    monthly_active_users: int = Field(..., description="Monthly active users")
    avg_session_duration: int = Field(..., description="Average session duration in seconds")
    total_content_plays: int = Field(..., description="Total content plays")
    popular_categories: List[ContentCategory] = Field(..., description="Popular content categories")


class SystemPerformanceMetrics(BaseModel):
    """System performance overview"""
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")
    background_jobs: Dict[str, Any] = Field(..., description="Background job statistics")
    database: Dict[str, Any] = Field(..., description="Database connection statistics")


class PlatformStatsResponse(BaseModel):
    """Complete platform statistics response"""
    overview: PlatformOverview
    growth: GrowthMetrics
    engagement: EngagementMetrics
    system_performance: SystemPerformanceMetrics
    generated_at: datetime = Field(..., description="Timestamp when stats were generated")
    time_range_days: int = Field(..., description="Number of days analyzed")


# Revenue Analytics Schemas
class TimeSeriesDataPoint(BaseModel):
    """Time series data point for revenue analytics"""
    date: Optional[str] = Field(None, description="Date (for daily breakdown)")
    week_start: Optional[str] = Field(None, description="Week start date (for weekly breakdown)")
    month: Optional[str] = Field(None, description="Month (for monthly breakdown)")
    revenue: float = Field(..., description="Revenue amount")
    subscriptions: int = Field(..., description="Total subscriptions")
    new_subscriptions: int = Field(..., description="New subscriptions")


class OrganizationTypeRevenue(BaseModel):
    """Revenue breakdown by organization type"""
    type: str = Field(..., description="Organization type")
    revenue: float = Field(..., description="Revenue from this type")
    count: int = Field(..., description="Number of organizations")


class SubscriptionPlanBreakdown(BaseModel):
    """Revenue breakdown by subscription plan"""
    plan: str = Field(..., description="Subscription plan name")
    revenue: float = Field(..., description="Revenue from this plan")
    subscribers: int = Field(..., description="Number of subscribers")


class RevenueSummary(BaseModel):
    """Revenue analytics summary"""
    total_revenue: float = Field(..., description="Total revenue in period")
    avg_revenue_per_period: float = Field(..., description="Average revenue per time period")
    growth_rate_percent: float = Field(..., description="Revenue growth rate percentage")
    active_subscriptions: int = Field(..., description="Active subscriptions count")
    time_range: str = Field(..., description="Time range analyzed")
    breakdown: str = Field(..., description="Data breakdown type")


class RevenueMetrics(BaseModel):
    """Additional revenue metrics"""
    monthly_recurring_revenue: float = Field(..., description="Monthly recurring revenue")
    average_revenue_per_user: float = Field(..., description="Average revenue per user")
    churn_rate_percent: float = Field(..., description="Customer churn rate percentage")
    customer_lifetime_value: float = Field(..., description="Customer lifetime value")


class RevenueAnalyticsResponse(BaseModel):
    """Complete revenue analytics response"""
    summary: RevenueSummary
    time_series: List[TimeSeriesDataPoint]
    revenue_by_organization_type: List[OrganizationTypeRevenue]
    subscription_plan_breakdown: List[SubscriptionPlanBreakdown]
    metrics: RevenueMetrics
    generated_at: datetime = Field(..., description="Timestamp when analytics were generated")


# Growth Trends Schemas
class UserGrowthDataPoint(BaseModel):
    """User growth data point"""
    date: str = Field(..., description="Date")
    total_users: int = Field(..., description="Total users on this date")
    new_users: int = Field(..., description="New users on this date")
    active_users: int = Field(..., description="Active users on this date")


class OrganizationGrowthDataPoint(BaseModel):
    """Organization growth data point"""
    date: str = Field(..., description="Date")
    total_organizations: int = Field(..., description="Total organizations on this date")
    new_organizations: int = Field(..., description="New organizations on this date")
    active_organizations: int = Field(..., description="Active organizations on this date")


class AcquisitionChannel(BaseModel):
    """User acquisition channel data"""
    channel: str = Field(..., description="Acquisition channel name")
    users: int = Field(..., description="Users acquired through this channel")
    cost_per_acquisition: float = Field(..., description="Cost per acquisition")


class GeographicDistribution(BaseModel):
    """Geographic distribution data"""
    region: str = Field(..., description="Geographic region")
    users: int = Field(..., description="Users in this region")
    organizations: int = Field(..., description="Organizations in this region")


class RetentionMetrics(BaseModel):
    """User retention metrics"""
    day_1_retention: float = Field(..., description="Day 1 retention rate")
    day_7_retention: float = Field(..., description="Day 7 retention rate")
    day_30_retention: float = Field(..., description="Day 30 retention rate")
    day_90_retention: float = Field(..., description="Day 90 retention rate")


class GrowthForecast(BaseModel):
    """Growth forecast data"""
    forecasted_users: int = Field(..., description="Forecasted user count")
    forecasted_organizations: int = Field(..., description="Forecasted organization count")
    confidence_level: int = Field(..., description="Confidence level percentage")


class GrowthSummary(BaseModel):
    """Growth trends summary"""
    current_users: int = Field(..., description="Current total users")
    current_organizations: int = Field(..., description="Current total organizations")
    user_growth_rate_percent: float = Field(..., description="User growth rate percentage")
    organization_growth_rate_percent: float = Field(..., description="Organization growth rate percentage")
    time_range: str = Field(..., description="Time range analyzed")


class GrowthTrendsResponse(BaseModel):
    """Complete growth trends response"""
    summary: GrowthSummary
    user_growth_timeline: List[UserGrowthDataPoint]
    organization_growth_timeline: List[OrganizationGrowthDataPoint]
    acquisition_channels: List[AcquisitionChannel]
    geographic_distribution: List[GeographicDistribution]
    retention_metrics: RetentionMetrics
    forecast_30_days: GrowthForecast
    key_insights: List[str] = Field(..., description="Key insights from the analysis")
    generated_at: datetime = Field(..., description="Timestamp when trends were generated")


# System Health Schemas
class ComponentHealthCheck(BaseModel):
    """Individual component health check"""
    component: str = Field(..., description="Component name")
    status: HealthStatusEnum = Field(..., description="Component health status")
    score: int = Field(..., description="Health score (0-100)")
    details: str = Field(..., description="Additional details about component health")


class SystemMetricsSummary(BaseModel):
    """System metrics summary"""
    uptime_hours: int = Field(..., description="System uptime in hours")
    total_requests_24h: int = Field(..., description="Total requests in last 24 hours")
    error_rate_24h: int = Field(..., description="Error count in last 24 hours")
    avg_response_time: float = Field(..., description="Average response time in seconds")


class SystemHealthResponse(BaseModel):
    """Complete system health response"""
    overall_status: HealthStatusEnum = Field(..., description="Overall system health status")
    overall_score: float = Field(..., description="Overall health score")
    component_health: List[ComponentHealthCheck] = Field(..., description="Individual component health checks")
    system_metrics: SystemMetricsSummary = Field(..., description="System metrics summary")
    performance_metrics: Dict[str, Any] = Field(..., description="Detailed performance metrics")
    cache_metrics: Dict[str, Any] = Field(..., description="Cache performance metrics")
    database_metrics: Dict[str, Any] = Field(..., description="Database connection metrics")
    background_job_metrics: Dict[str, Any] = Field(..., description="Background job metrics")
    recent_alerts: List['SystemAlert'] = Field(..., description="Recent system alerts")
    last_updated: datetime = Field(..., description="Last update timestamp")


# System Alerts Schemas
class SystemAlert(BaseModel):
    """System alert model"""
    id: str = Field(..., description="Alert identifier")
    type: str = Field(..., description="Alert type")
    severity: AlertSeverityEnum = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    count: int = Field(..., description="Number of occurrences")
    affected_users: int = Field(..., description="Number of affected users")
    first_seen: str = Field(..., description="First occurrence timestamp")
    last_seen: str = Field(..., description="Last occurrence timestamp")
    category: str = Field(..., description="Alert category")
    component: str = Field(..., description="Affected component")


class AlertSummary(BaseModel):
    """Alert summary statistics"""
    total_alerts: int = Field(..., description="Total number of alerts")
    critical_count: int = Field(..., description="Number of critical alerts")
    warning_count: int = Field(..., description="Number of warning alerts")
    info_count: int = Field(..., description="Number of info alerts")
    last_24h_errors: int = Field(..., description="Errors in last 24 hours")


class AlertFilters(BaseModel):
    """Applied alert filters"""
    limit: int = Field(..., description="Maximum alerts returned")
    severity: Optional[str] = Field(None, description="Severity filter applied")


class SystemAlertsResponse(BaseModel):
    """Complete system alerts response"""
    alerts: List[SystemAlert] = Field(..., description="List of system alerts")
    summary: AlertSummary = Field(..., description="Alert summary statistics")
    filters_applied: AlertFilters = Field(..., description="Filters applied to results")
    generated_at: datetime = Field(..., description="Timestamp when alerts were retrieved")


# Update forward references
SystemHealthResponse.model_rebuild()
