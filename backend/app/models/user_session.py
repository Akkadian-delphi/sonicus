"""
User Session Tracking Model

Tracks user sessions for analytics and engagement metrics.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class UserSession(Base):
    """User session tracking for analytics."""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
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
    
    # Flags
    is_active = Column(Boolean, default=True)
    completed_successfully = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (temporarily disabled to fix login)
    # user = relationship("User", back_populates="sessions")
    # organization = relationship("Organization", back_populates="sessions")
    # content_plays = relationship("ContentPlay", back_populates="session")


class ContentPlay(Base):
    """Individual content play tracking within sessions."""
    __tablename__ = "content_plays"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
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
    # organization = relationship("Organization", back_populates="content_plays")
    # content = relationship("TherapySound", back_populates="plays")


class UserEngagementMetric(Base):
    """Pre-calculated user engagement metrics for performance."""
    __tablename__ = "user_engagement_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
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
    
    # Comparison metrics
    previous_period_score = Column(Float, nullable=True)
    score_trend = Column(String(20), nullable=True)  # "improving", "stable", "declining"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # user = relationship("User", back_populates="engagement_metrics")  # Commented out due to circular reference
    # organization = relationship("Organization", back_populates="engagement_metrics")  # Commented out due to circular reference
