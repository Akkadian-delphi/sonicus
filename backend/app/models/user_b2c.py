"""
B2C User Models - Direct User Experience

Updated models for B2C architecture without organization dependencies.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Date, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class UserSubscription(Base):
    """Direct user subscriptions for B2C model."""
    __tablename__ = "user_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Subscription details
    subscription_tier = Column(String(50), nullable=False, default="starter")  # starter, premium, pro
    subscription_status = Column(String(50), nullable=False, default="trial")  # trial, active, expired, canceled
    billing_cycle = Column(String(20), default="monthly")  # monthly, yearly
    
    # Pricing
    price_per_cycle = Column(DECIMAL(10, 2), nullable=True)
    currency = Column(String(3), default="USD")
    
    # Trial management
    trial_start_date = Column(DateTime, nullable=True)
    trial_end_date = Column(DateTime, nullable=True)
    
    # Subscription lifecycle
    subscription_start_date = Column(DateTime, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)
    
    # Payment info
    payment_method_id = Column(String(255), nullable=True)  # Stripe payment method ID
    last_payment_date = Column(DateTime, nullable=True)
    next_payment_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (temporarily disabled to fix login)
    # user = relationship("User", back_populates="subscription")


class UserSoundPackage(Base):
    """Direct user-to-sound package assignments for B2C model."""
    __tablename__ = "user_sound_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sound_package_id = Column(UUID(as_uuid=True), ForeignKey("sound_packages.id"), nullable=False, index=True)
    
    # Access management
    access_granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_expires_at = Column(DateTime, nullable=True)  # For time-limited access
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint
    __table_args__ = (
        {"schema": "sonicus"},
    )
    
    # Relationships (temporarily disabled to fix login)
    # user = relationship("User", back_populates="sound_packages")
    # sound_package = relationship("SoundPackage", back_populates="user_assignments")


class UserPreferences(Base):
    """User personal preferences and settings."""
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Session preferences
    preferred_session_length = Column(Integer, default=20)  # minutes
    preferred_time_of_day = Column(String(20), nullable=True)  # morning, afternoon, evening
    
    # Notification preferences
    notification_preferences = Column(JSONB, default={})
    # Example: {"email": True, "push": False, "session_reminders": True, "weekly_summary": True}
    
    # UI/UX preferences
    theme_preferences = Column(JSONB, default={})
    # Example: {"theme": "dark", "language": "en", "animations": True}
    
    # Audio preferences
    audio_preferences = Column(JSONB, default={})
    # Example: {"default_volume": 80, "fade_in": True, "fade_out": True, "preferred_quality": "high"}
    
    # Privacy settings
    privacy_settings = Column(JSONB, default={})
    # Example: {"share_stats": False, "anonymous_analytics": True, "marketing_emails": False}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (temporarily disabled)
    # user = relationship("User", back_populates="preferences", uselist=False)


class UserAnalytics(Base):
    """Personal user analytics for B2C model."""
    __tablename__ = "user_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Time period
    date = Column(Date, nullable=False, index=True)
    
    # Session metrics
    sessions_count = Column(Integer, default=0)
    total_listening_time_minutes = Column(Integer, default=0)
    unique_sounds_played = Column(Integer, default=0)
    average_session_length = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)  # 0-100%
    
    # Wellness metrics
    stress_level_before = Column(Float, nullable=True)  # 1-10 scale
    stress_level_after = Column(Float, nullable=True)   # 1-10 scale
    mood_improvement_score = Column(Float, nullable=True)  # Calculated improvement
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint on user and date
    __table_args__ = (
        {"schema": "sonicus"},
    )
    
    # Relationships (temporarily disabled)
    # user = relationship("User", back_populates="analytics")


class UserSession(Base):
    """Updated user session tracking for B2C model (no organization dependency)."""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Session details
    session_start = Column(DateTime, default=datetime.utcnow, nullable=False)
    session_end = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)  # Calculated when session ends
    
    # Device and platform info
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    platform = Column(String(50), nullable=True)    # iOS, Android, Web
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    
    # Location (optional)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Session quality metrics
    content_items_played = Column(Integer, default=0)
    total_listening_time = Column(Float, default=0.0)  # Minutes of actual content consumption
    session_quality_score = Column(Float, nullable=True)  # 0-100 engagement score
    
    # Wellness tracking
    stress_level_before = Column(Float, nullable=True)  # User-reported 1-10
    stress_level_after = Column(Float, nullable=True)   # User-reported 1-10
    session_goal = Column(String(100), nullable=True)  # "relaxation", "focus", "sleep", etc.
    goal_achieved = Column(Boolean, nullable=True)     # User-reported success
    
    # Flags
    is_active = Column(Boolean, default=True)
    completed_successfully = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (temporarily disabled to fix login)
    # user = relationship("User", back_populates="sessions")
    # content_plays = relationship("ContentPlay", back_populates="session")


class ContentPlay(Base):
    """Individual content play tracking within sessions (updated for B2C)."""
    __tablename__ = "content_plays"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("therapy_sounds.id"), nullable=False, index=True)
    
    # Play details
    play_start = Column(DateTime, default=datetime.utcnow, nullable=False)
    play_end = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)  # Actual play duration
    content_duration_seconds = Column(Float, nullable=True)  # Total content length
    completion_percentage = Column(Float, default=0.0)  # 0-100%
    
    # User interaction
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    liked = Column(Boolean, nullable=True)
    bookmarked = Column(Boolean, default=False)
    shared = Column(Boolean, default=False)
    
    # Play quality
    buffer_events = Column(Integer, default=0)  # Number of buffering events
    skip_events = Column(Integer, default=0)    # Number of skips/seeks
    volume_level = Column(Float, nullable=True) # 0-100 volume level
    playback_speed = Column(Float, default=1.0) # Playback speed multiplier
    
    # Context
    play_context = Column(String(100), nullable=True)  # "recommendation", "search", "category", "playlist"
    referrer_content_id = Column(Integer, nullable=True)  # If played from recommendation
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (temporarily disabled to fix login)
    # session = relationship("UserSession", back_populates="content_plays")
    # user = relationship("User", back_populates="content_plays") 
    # content = relationship("TherapySound", back_populates="plays")


class UserEngagementMetric(Base):
    """Personal user engagement metrics for B2C (no organization dependency)."""
    __tablename__ = "user_engagement_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Time period
    metric_date = Column(DateTime, nullable=False, index=True)  # Date this metric represents
    period_type = Column(String(20), nullable=False)  # "daily", "weekly", "monthly"
    
    # Engagement metrics
    sessions_count = Column(Integer, default=0)
    total_session_time = Column(Float, default=0.0)  # Minutes
    content_items_played = Column(Integer, default=0)
    unique_content_count = Column(Integer, default=0) # Unique content pieces
    average_session_duration = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)  # 0-100%
    
    # Behavioral metrics
    days_active = Column(Integer, default=0)  # Days active in period
    peak_usage_hour = Column(Integer, nullable=True)  # 0-23
    favorite_categories = Column(String(500), nullable=True)  # JSON array of categories
    engagement_score = Column(Float, default=0.0)  # 0-100 calculated score
    
    # Wellness metrics
    average_stress_improvement = Column(Float, nullable=True)  # Average improvement per session
    wellness_streak_days = Column(Integer, default=0)  # Consecutive days of usage
    goal_achievement_rate = Column(Float, default=0.0)  # 0-100% of sessions where goal was achieved
    
    # Comparison metrics
    previous_period_score = Column(Float, nullable=True)
    score_trend = Column(String(20), nullable=True)  # "improving", "stable", "declining"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # user = relationship("User", back_populates="engagement_metrics")  # Temporarily disabled to fix login
