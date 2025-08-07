"""
Organization Metrics and Analytics Models

Comprehensive models for tracking employee wellness, engagement, and productivity
metrics within organizations. Includes measurement algorithms and custom goal tracking.

Created: July 27, 2025
Author: Sonicus Platform Team
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from enum import Enum
import uuid
from app.db.base import Base

# =================== ENUMS ===================

class MetricType(str, Enum):
    """Types of wellness metrics tracked"""
    STRESS_REDUCTION = "stress_reduction"
    SLEEP_IMPROVEMENT = "sleep_improvement"
    FOCUS_ENHANCEMENT = "focus_enhancement"
    MOOD_IMPROVEMENT = "mood_improvement"
    PRODUCTIVITY = "productivity"
    ENGAGEMENT = "engagement"
    ANXIETY_RELIEF = "anxiety_relief"
    ENERGY_LEVEL = "energy_level"
    WORK_SATISFACTION = "work_satisfaction"
    TEAM_COLLABORATION = "team_collaboration"

class MeasurementPeriod(str, Enum):
    """Time periods for metric measurement"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class GoalStatus(str, Enum):
    """Status of wellness goals"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

class EngagementLevel(str, Enum):
    """Employee engagement levels"""
    VERY_LOW = "very_low"      # 0-20%
    LOW = "low"                # 21-40%
    MODERATE = "moderate"      # 41-60%
    HIGH = "high"             # 61-80%
    VERY_HIGH = "very_high"   # 81-100%

class WellnessCategory(str, Enum):
    """Categories of wellness metrics"""
    MENTAL_HEALTH = "mental_health"
    PHYSICAL_WELLNESS = "physical_wellness"
    WORK_PERFORMANCE = "work_performance"
    SOCIAL_ENGAGEMENT = "social_engagement"
    STRESS_MANAGEMENT = "stress_management"
    SLEEP_QUALITY = "sleep_quality"

# =================== CORE METRICS MODELS ===================

class OrganizationMetrics(Base):
    """Core organization-wide metrics and KPIs"""
    __tablename__ = "organization_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Time period for these metrics
    measurement_period = Column(String(20), nullable=False)  # MetricType enum
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Overall organization scores (0-100)
    overall_wellness_score = Column(Float, nullable=True)
    overall_engagement_score = Column(Float, nullable=True)
    overall_productivity_score = Column(Float, nullable=True)
    
    # Participation metrics
    total_employees = Column(Integer, nullable=False, default=0)
    active_participants = Column(Integer, nullable=False, default=0)
    participation_rate = Column(Float, nullable=True)  # Percentage
    
    # Usage metrics
    total_sessions = Column(Integer, nullable=False, default=0)
    total_listening_minutes = Column(Float, nullable=False, default=0.0)
    avg_session_duration = Column(Float, nullable=True)
    
    # Engagement metrics
    daily_active_users = Column(Integer, nullable=False, default=0)
    weekly_retention_rate = Column(Float, nullable=True)
    feature_adoption_rate = Column(Float, nullable=True)
    
    # Wellness impact metrics
    stress_reduction_average = Column(Float, nullable=True)
    sleep_improvement_average = Column(Float, nullable=True)
    focus_enhancement_average = Column(Float, nullable=True)
    mood_improvement_average = Column(Float, nullable=True)
    
    # Productivity metrics
    productivity_increase_reported = Column(Float, nullable=True)
    work_satisfaction_score = Column(Float, nullable=True)
    team_collaboration_score = Column(Float, nullable=True)
    
    # ROI and business metrics
    estimated_roi_percentage = Column(Float, nullable=True)
    cost_per_engaged_employee = Column(Float, nullable=True)
    wellness_program_efficiency = Column(Float, nullable=True)
    
    # Additional metrics as JSON for flexibility
    custom_metrics = Column(JSON, nullable=True)
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # organization = relationship("Organization", back_populates="metrics")  # Commented out due to circular reference
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_org_metrics_period', 'organization_id', 'measurement_period', 'period_start'),
        Index('idx_org_metrics_calculated', 'calculated_at'),
    )

class EmployeeWellnessMetrics(Base):
    """Individual employee wellness and engagement metrics"""
    __tablename__ = "employee_wellness_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Time period
    measurement_date = Column(DateTime(timezone=True), nullable=False)
    measurement_period = Column(String(20), nullable=False)
    
    # Core wellness scores (0-100)
    stress_level_score = Column(Float, nullable=True)  # Lower is better
    sleep_quality_score = Column(Float, nullable=True)
    focus_level_score = Column(Float, nullable=True)
    mood_score = Column(Float, nullable=True)
    energy_level_score = Column(Float, nullable=True)
    anxiety_level_score = Column(Float, nullable=True)  # Lower is better
    
    # Engagement metrics (0-100)
    app_engagement_score = Column(Float, nullable=True)
    content_interaction_score = Column(Float, nullable=True)
    feature_usage_score = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    
    # Productivity metrics (0-100)
    work_performance_score = Column(Float, nullable=True)
    task_completion_score = Column(Float, nullable=True)
    collaboration_score = Column(Float, nullable=True)
    innovation_score = Column(Float, nullable=True)
    
    # Usage patterns
    total_sessions = Column(Integer, nullable=False, default=0)
    total_minutes_listened = Column(Float, nullable=False, default=0.0)
    avg_session_duration = Column(Float, nullable=True)
    preferred_content_categories = Column(JSON, nullable=True)
    peak_usage_hours = Column(JSON, nullable=True)
    
    # Self-reported metrics (surveys/check-ins)
    self_reported_stress = Column(Integer, nullable=True)  # 1-10 scale
    self_reported_sleep_quality = Column(Integer, nullable=True)  # 1-10 scale
    self_reported_focus = Column(Integer, nullable=True)  # 1-10 scale
    self_reported_mood = Column(Integer, nullable=True)  # 1-10 scale
    self_reported_productivity = Column(Integer, nullable=True)  # 1-10 scale
    
    # Behavioral indicators
    login_frequency = Column(Integer, nullable=False, default=0)
    feature_adoption_count = Column(Integer, nullable=False, default=0)
    goal_completion_rate = Column(Float, nullable=True)
    streak_days = Column(Integer, nullable=False, default=0)
    
    # Risk indicators
    burnout_risk_score = Column(Float, nullable=True)  # 0-100, higher is riskier
    disengagement_risk_score = Column(Float, nullable=True)
    wellness_decline_trend = Column(Boolean, nullable=False, default=False)
    
    # Contextual data
    device_type = Column(String(50), nullable=True)
    location_context = Column(String(100), nullable=True)  # office, home, travel
    time_zone = Column(String(50), nullable=True)
    
    # Metadata
    data_quality_score = Column(Float, nullable=True)  # Confidence in metrics
    metrics_version = Column(String(10), nullable=False, default="1.0")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    employee = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_employee_metrics_date', 'employee_id', 'measurement_date'),
        Index('idx_employee_metrics_period', 'organization_id', 'measurement_period'),
        Index('idx_employee_wellness_scores', 'stress_level_score', 'mood_score', 'focus_level_score'),
    )

class WellnessGoals(Base):
    """Custom wellness goals for employees and organizations"""
    __tablename__ = "wellness_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for org-wide goals
    
    # Goal definition
    goal_name = Column(String(255), nullable=False)
    goal_description = Column(Text, nullable=True)
    goal_category = Column(String(50), nullable=False)  # WellnessCategory enum
    goal_type = Column(String(50), nullable=False)  # MetricType enum
    
    # Goal parameters
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False, default=0.0)
    measurement_unit = Column(String(50), nullable=False)  # "minutes", "sessions", "score", "percentage"
    
    # Time parameters
    start_date = Column(DateTime(timezone=True), nullable=False)
    target_date = Column(DateTime(timezone=True), nullable=False)
    duration_days = Column(Integer, nullable=False)
    
    # Status and progress
    status = Column(String(20), nullable=False, default=GoalStatus.DRAFT)
    progress_percentage = Column(Float, nullable=False, default=0.0)
    completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Goal configuration
    is_recurring = Column(Boolean, nullable=False, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # For recurring goals
    reminder_settings = Column(JSON, nullable=True)
    
    # Milestone tracking
    milestones = Column(JSON, nullable=True)  # Array of milestone objects
    achieved_milestones = Column(JSON, nullable=True)
    
    # Contextual information
    priority_level = Column(String(20), nullable=False, default="medium")  # low, medium, high
    difficulty_level = Column(String(20), nullable=False, default="medium")
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Manager/admin who assigned
    
    # Tracking and analytics
    tracking_frequency = Column(String(20), nullable=False, default="daily")
    auto_tracking_enabled = Column(Boolean, nullable=False, default=True)
    manual_check_ins_required = Column(Boolean, nullable=False, default=False)
    
    # Motivation and rewards
    reward_points = Column(Integer, nullable=False, default=0)
    celebration_message = Column(Text, nullable=True)
    team_visibility = Column(Boolean, nullable=False, default=False)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    tags = Column(JSON, nullable=True)  # For categorization
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    employee = relationship("User", foreign_keys=[employee_id])
    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User", foreign_keys=[assigned_by])
    progress_logs = relationship("GoalProgressLog", back_populates="goal")
    
    # Indexes
    __table_args__ = (
        Index('idx_wellness_goals_org_employee', 'organization_id', 'employee_id'),
        Index('idx_wellness_goals_status_date', 'status', 'target_date'),
        Index('idx_wellness_goals_category', 'goal_category', 'goal_type'),
    )

class GoalProgressLog(Base):
    """Detailed progress tracking for wellness goals"""
    __tablename__ = "goal_progress_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("wellness_goals.id"), nullable=False)
    
    # Progress data
    logged_date = Column(DateTime(timezone=True), nullable=False)
    logged_value = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=True)
    progress_delta = Column(Float, nullable=True)
    
    # Context
    log_source = Column(String(50), nullable=False)  # "auto", "manual", "survey", "api"
    activity_context = Column(JSON, nullable=True)  # Related activities/sessions
    
    # Notes and feedback
    employee_notes = Column(Text, nullable=True)
    mood_context = Column(String(50), nullable=True)
    external_factors = Column(JSON, nullable=True)  # Weather, workload, etc.
    
    # Validation
    data_confidence = Column(Float, nullable=True)  # 0-1 confidence score
    verified = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    goal = relationship("WellnessGoals", back_populates="progress_logs")
    
    # Index
    __table_args__ = (
        Index('idx_goal_progress_date', 'goal_id', 'logged_date'),
    )

class EngagementEvents(Base):
    """Track specific engagement events and behaviors"""
    __tablename__ = "engagement_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # "session_start", "goal_created", "milestone_reached"
    event_category = Column(String(50), nullable=False)  # "usage", "achievement", "social", "content"
    event_description = Column(Text, nullable=True)
    
    # Event data
    event_value = Column(Float, nullable=True)  # Numeric value if applicable
    event_metadata = Column(JSON, nullable=True)  # Additional event data
    
    # Context
    session_id = Column(String(100), nullable=True)
    content_id = Column(String(100), nullable=True)
    feature_name = Column(String(100), nullable=True)
    
    # Engagement scoring
    engagement_weight = Column(Float, nullable=False, default=1.0)
    quality_score = Column(Float, nullable=True)  # Quality of engagement
    
    # Device and environment
    device_type = Column(String(50), nullable=True)
    platform = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization")
    employee = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_engagement_events_employee_time', 'employee_id', 'event_timestamp'),
        Index('idx_engagement_events_org_type', 'organization_id', 'event_type'),
        Index('idx_engagement_events_category', 'event_category', 'event_timestamp'),
    )

class WellnessAlgorithmConfig(Base):
    """Configuration for wellness measurement algorithms"""
    __tablename__ = "wellness_algorithm_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Algorithm configuration
    algorithm_name = Column(String(100), nullable=False)
    algorithm_version = Column(String(20), nullable=False, default="1.0")
    algorithm_description = Column(Text, nullable=True)
    
    # Scoring weights and parameters
    metric_weights = Column(JSON, nullable=False)  # Weights for different metrics
    calculation_parameters = Column(JSON, nullable=False)  # Algorithm-specific parameters
    
    # Thresholds and boundaries
    score_thresholds = Column(JSON, nullable=True)  # Risk/success thresholds
    outlier_detection_params = Column(JSON, nullable=True)
    
    # Configuration status
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)
    
    # Validation and testing
    validation_results = Column(JSON, nullable=True)
    test_accuracy_score = Column(Float, nullable=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    activated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_algorithm_config_org_active', 'organization_id', 'is_active'),
        Index('idx_algorithm_config_name_version', 'algorithm_name', 'algorithm_version'),
    )

# =================== RELATIONSHIP UPDATES ===================

# Update Organization model to include new relationships
# (This would be added to the existing Organization model)
"""
Additional relationships to add to Organization model:

metrics = relationship("OrganizationMetrics", back_populates="organization")
employee_metrics = relationship("EmployeeWellnessMetrics", back_populates="organization") 
wellness_goals = relationship("WellnessGoals", back_populates="organization")
engagement_events = relationship("EngagementEvents", back_populates="organization")
algorithm_configs = relationship("WellnessAlgorithmConfig", back_populates="organization")
"""
