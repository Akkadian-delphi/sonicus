"""
Organization Analytics Schemas

Comprehensive Pydantic models for organization analytics including:
- Real-time usage metrics per organization
- User engagement analytics across organizations
- Revenue attribution per organization
- Content usage patterns and recommendations
- Organization health scoring algorithm
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from enum import Enum
import uuid


# ==================== ENUMS ====================

class MetricTimeRange(str, Enum):
    """Time range options for analytics."""
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    LAST_YEAR = "1y"
    CUSTOM = "custom"


class EngagementLevel(str, Enum):
    """User engagement classification levels."""
    CRITICAL = "critical"  # <10% usage
    LOW = "low"           # 10-30% usage
    MODERATE = "moderate" # 30-60% usage
    HIGH = "high"         # 60-85% usage
    EXCEPTIONAL = "exceptional"  # >85% usage


class HealthStatus(str, Enum):
    """Organization health status levels."""
    CRITICAL = "critical"  # Score 0-25
    POOR = "poor"         # Score 26-50
    FAIR = "fair"         # Score 51-70
    GOOD = "good"         # Score 71-85
    EXCELLENT = "excellent"  # Score 86-100


# ==================== USAGE METRICS ====================

class UsageMetricPoint(BaseModel):
    """Single usage metric data point."""
    date: date
    value: float
    label: Optional[str] = None


class UsageMetrics(BaseModel):
    """Real-time usage metrics for an organization."""
    total_sessions: int
    total_minutes_listened: float
    unique_active_users: int
    average_session_duration: float
    most_popular_content_id: Optional[str] = None
    most_popular_content_title: Optional[str] = None
    peak_usage_hour: Optional[int] = None
    sessions_by_day: List[UsageMetricPoint]
    minutes_by_day: List[UsageMetricPoint]
    users_by_day: List[UsageMetricPoint]


class RealTimeUsageMetrics(BaseModel):
    """Real-time usage metrics response."""
    organization_id: str
    organization_name: str
    time_range: MetricTimeRange
    start_date: date
    end_date: date
    usage_metrics: UsageMetrics
    compared_to_previous_period: Optional[Dict[str, float]] = None
    generated_at: datetime


# ==================== ENGAGEMENT ANALYTICS ====================

class UserEngagementData(BaseModel):
    """Individual user engagement data."""
    user_id: str
    user_email: Optional[str] = None
    total_sessions: int
    total_minutes: float
    days_active: int
    last_activity: datetime
    engagement_level: EngagementLevel
    favorite_content_types: List[str]
    engagement_score: float = Field(..., ge=0, le=100)


class EngagementAnalytics(BaseModel):
    """User engagement analytics across organization."""
    total_users: int
    active_users_period: int
    engagement_distribution: Dict[EngagementLevel, int]
    average_engagement_score: float
    top_engaged_users: List[UserEngagementData]
    engagement_trends: List[UsageMetricPoint]
    recommendations: List[str]


class UserEngagementAnalyticsResponse(BaseModel):
    """User engagement analytics response."""
    organization_id: str
    organization_name: str
    time_range: MetricTimeRange
    start_date: date
    end_date: date
    engagement_analytics: EngagementAnalytics
    generated_at: datetime


# ==================== REVENUE ANALYTICS ====================

class RevenueBreakdown(BaseModel):
    """Revenue breakdown by category."""
    subscription_revenue: float
    usage_based_revenue: float
    one_time_charges: float
    discounts_applied: float
    total_revenue: float


class RevenueMetrics(BaseModel):
    """Revenue attribution metrics."""
    current_period_revenue: RevenueBreakdown
    previous_period_revenue: RevenueBreakdown
    revenue_growth_rate: float
    monthly_recurring_revenue: float
    annual_recurring_revenue: float
    average_revenue_per_user: float
    customer_lifetime_value: float
    revenue_by_day: List[UsageMetricPoint]
    projected_revenue_next_month: float


class RevenueAttributionResponse(BaseModel):
    """Revenue attribution analytics response."""
    organization_id: str
    organization_name: str
    subscription_tier: str
    time_range: MetricTimeRange
    start_date: date
    end_date: date
    revenue_metrics: RevenueMetrics
    generated_at: datetime


# ==================== CONTENT ANALYTICS ====================

class ContentUsagePattern(BaseModel):
    """Content usage pattern data."""
    content_id: str
    content_title: str
    content_type: str
    total_plays: int
    total_minutes: float
    unique_users: int
    average_rating: Optional[float] = None
    completion_rate: float
    peak_usage_times: List[int]  # Hours of day (0-23)


class ContentRecommendation(BaseModel):
    """Content recommendation for organization."""
    content_id: str
    content_title: str
    content_type: str
    recommendation_reason: str
    predicted_engagement_score: float
    similar_organizations_using: int


class ContentUsageAnalytics(BaseModel):
    """Content usage patterns and recommendations."""
    top_content: List[ContentUsagePattern]
    content_categories_performance: Dict[str, Dict[str, Union[int, float]]]
    underutilized_content: List[ContentUsagePattern]
    recommended_content: List[ContentRecommendation]
    content_diversity_score: float = Field(..., ge=0, le=100)
    usage_patterns_by_time: Dict[str, List[int]]  # day_of_week -> [hourly_usage]


class ContentUsageAnalyticsResponse(BaseModel):
    """Content usage analytics response."""
    organization_id: str
    organization_name: str
    time_range: MetricTimeRange
    start_date: date
    end_date: date
    content_analytics: ContentUsageAnalytics
    generated_at: datetime


# ==================== HEALTH SCORING ====================

class HealthFactor(BaseModel):
    """Individual health factor scoring."""
    factor_name: str
    current_score: float = Field(..., ge=0, le=100)
    target_score: float = Field(..., ge=0, le=100)
    weight: float = Field(..., ge=0, le=1)
    description: str
    recommendations: List[str]


class OrganizationHealthMetrics(BaseModel):
    """Comprehensive organization health metrics."""
    overall_health_score: float = Field(..., ge=0, le=100)
    health_status: HealthStatus
    health_factors: List[HealthFactor]
    trend_direction: str  # "improving", "stable", "declining"
    days_since_last_activity: int
    risk_factors: List[str]
    success_indicators: List[str]
    action_items: List[str]


class OrganizationHealthScoreResponse(BaseModel):
    """Organization health scoring response."""
    organization_id: str
    organization_name: str
    subscription_tier: str
    health_metrics: OrganizationHealthMetrics
    comparison_to_similar_orgs: Optional[Dict[str, float]] = None
    historical_scores: List[UsageMetricPoint]
    generated_at: datetime


# ==================== COMPREHENSIVE ANALYTICS ====================

class ComprehensiveAnalytics(BaseModel):
    """Comprehensive analytics combining all metrics."""
    usage_summary: UsageMetrics
    engagement_summary: EngagementAnalytics
    revenue_summary: RevenueMetrics
    content_summary: ContentUsageAnalytics
    health_summary: OrganizationHealthMetrics


class ComprehensiveAnalyticsResponse(BaseModel):
    """Complete analytics response for an organization."""
    organization_id: str
    organization_name: str
    subscription_tier: str
    time_range: MetricTimeRange
    start_date: date
    end_date: date
    analytics: ComprehensiveAnalytics
    key_insights: List[str]
    generated_at: datetime


# ==================== BULK ANALYTICS ====================

class OrganizationAnalyticsSummary(BaseModel):
    """Summary analytics for organization list."""
    organization_id: str
    organization_name: str
    subscription_tier: str
    health_score: float
    health_status: HealthStatus
    total_users: int
    active_users: int
    engagement_score: float
    monthly_revenue: float
    last_activity: datetime


class BulkAnalyticsResponse(BaseModel):
    """Bulk analytics response for multiple organizations."""
    total_organizations: int
    time_range: MetricTimeRange
    start_date: date
    end_date: date
    organizations: List[OrganizationAnalyticsSummary]
    platform_averages: Dict[str, float]
    generated_at: datetime


# ==================== ANALYTICS FILTERS ====================

class AnalyticsFilters(BaseModel):
    """Filters for analytics queries."""
    time_range: MetricTimeRange = MetricTimeRange.LAST_30_DAYS
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    organization_ids: Optional[List[str]] = None
    subscription_tiers: Optional[List[str]] = None
    health_status_filter: Optional[List[HealthStatus]] = None
    engagement_level_filter: Optional[List[EngagementLevel]] = None
    include_inactive: bool = False
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date."""
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
