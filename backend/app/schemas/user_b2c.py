"""
B2C User Schemas

Pydantic schemas for B2C user management endpoints.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID


class UserProfileResponse(BaseModel):
    """User profile response for B2C."""
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    is_premium: bool = False
    trial_end_date: Optional[datetime] = None
    total_sessions: int = 0
    total_listening_hours: float = 0.0
    wellness_streak_days: int = 0
    created_at: datetime
    has_subscription_details: bool = False
    has_preferences: bool = False


class UserSubscriptionUpdate(BaseModel):
    """Schema for updating user subscription."""
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    billing_cycle: Optional[str] = None
    auto_renew: Optional[bool] = None


class UserSubscriptionResponse(BaseModel):
    """User subscription response."""
    id: UUID
    subscription_tier: str
    subscription_status: str
    billing_cycle: Optional[str] = None
    price_per_cycle: Optional[float] = None
    currency: str = "USD"
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    auto_renew: bool = True
    next_payment_date: Optional[datetime] = None
    created_at: datetime


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    preferred_session_length: Optional[int] = None
    preferred_time_of_day: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    theme_preferences: Optional[Dict[str, Any]] = None
    audio_preferences: Optional[Dict[str, Any]] = None
    privacy_settings: Optional[Dict[str, Any]] = None


class UserPreferencesResponse(BaseModel):
    """User preferences response."""
    id: UUID
    preferred_session_length: int = 20
    preferred_time_of_day: Optional[str] = None
    notification_preferences: Dict[str, Any] = {}
    theme_preferences: Dict[str, Any] = {}
    audio_preferences: Dict[str, Any] = {}
    privacy_settings: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class UserSoundPackageResponse(BaseModel):
    """User sound package assignment response."""
    id: UUID
    sound_package_id: UUID
    package_name: str
    description: Optional[str] = None
    access_granted_at: datetime
    access_expires_at: Optional[datetime] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    is_active: bool = True


class DailyAnalytics(BaseModel):
    """Daily analytics data."""
    date: str  # ISO date string
    sessions_count: int
    listening_time_minutes: int
    completion_rate: float
    mood_improvement: Optional[float] = None


class UserAnalyticsResponse(BaseModel):
    """User analytics response."""
    period_days: int
    total_sessions: int
    total_listening_hours: float
    average_session_length: float
    completion_rate: float
    wellness_streak_days: int
    average_wellness_improvement: Optional[float] = None
    daily_analytics: List[DailyAnalytics]


class UserTrialResponse(BaseModel):
    """Response when starting user trial."""
    message: str
    trial_end_date: datetime
    days_remaining: int
