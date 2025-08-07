"""
Real Wellness Impact Tracking Models

Comprehensive data models for tracking real-time wellness impact,
employee engagement analytics, ROI calculations, and interactive
dashboard components.

Created: July 27, 2025
Author: Sonicus Platform Team
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from app.db.base import Base
from datetime import datetime
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any

# =================== ENUMS ===================

class WidgetType(str, Enum):
    """Dashboard widget types"""
    PROGRESS_BAR = "progress_bar"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    METRIC_CARD = "metric_card"
    TREND_INDICATOR = "trend_indicator"
    COMPARISON_CHART = "comparison_chart"
    CALENDAR_HEATMAP = "calendar_heatmap"

class MetricPeriod(str, Enum):
    """Time periods for metric calculation"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class TrendDirection(str, Enum):
    """Trend direction indicators"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    VOLATILE = "volatile"

class EngagementLevel(str, Enum):
    """Employee engagement levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class ROICategory(str, Enum):
    """ROI calculation categories"""
    PRODUCTIVITY = "productivity"
    ABSENTEEISM = "absenteeism"
    TURNOVER = "turnover"
    HEALTHCARE_COSTS = "healthcare_costs"
    ENGAGEMENT = "engagement"
    SATISFACTION = "satisfaction"
    STRESS_REDUCTION = "stress_reduction"
    OVERALL = "overall"

# =================== CORE MODELS ===================

class WellnessProgressBar(Base):
    """Model for interactive progress bar configurations and data"""
    __tablename__ = "wellness_progress_bars"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Progress bar configuration
    title = Column(String(200), nullable=False)
    description = Column(Text)
    metric_type = Column(String(100), nullable=False)  # stress_reduction, engagement, etc.
    
    # Data configuration
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=False, default="points")
    
    # Visual configuration
    color_scheme = Column(String(50), default="green")  # green, blue, orange, red, purple
    show_percentage = Column(Boolean, default=True)
    show_target = Column(Boolean, default=True)
    animated = Column(Boolean, default=True)
    
    # Time settings
    period = Column(String(50), default=MetricPeriod.MONTHLY.value)
    auto_refresh_minutes = Column(Integer, default=15)
    
    # Position and visibility
    dashboard_position = Column(JSON)  # {"x": 0, "y": 0, "width": 4, "height": 2}
    is_visible = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Historical data for trends
    historical_data = Column(JSON)  # Array of {date, value} objects
    
    # Relationships
    # Temporarily commented out to avoid circular import issues
    # organization = relationship("Organization", back_populates="wellness_progress_bars")
    creator = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_progress_bar_org_metric', 'organization_id', 'metric_type'),
        Index('idx_progress_bar_visible', 'organization_id', 'is_visible'),
    )

class WellnessTrendChart(Base):
    """Model for trend analysis charts and visualizations"""
    __tablename__ = "wellness_trend_charts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Chart configuration
    title = Column(String(200), nullable=False)
    chart_type = Column(String(50), nullable=False)  # line, bar, area, scatter
    metrics = Column(ARRAY(String))  # Array of metric types to display
    
    # Data configuration
    time_range_days = Column(Integer, default=30)
    granularity = Column(String(50), default="daily")  # daily, weekly, monthly
    comparison_enabled = Column(Boolean, default=False)
    comparison_period_offset = Column(Integer)  # Days to offset for comparison
    
    # Visual configuration
    color_palette = Column(JSON)  # Array of colors for different metrics
    show_legend = Column(Boolean, default=True)
    show_grid = Column(Boolean, default=True)
    show_tooltips = Column(Boolean, default=True)
    smooth_lines = Column(Boolean, default=True)
    
    # Interactive features
    zoom_enabled = Column(Boolean, default=True)
    pan_enabled = Column(Boolean, default=True)
    export_enabled = Column(Boolean, default=True)
    
    # Position and visibility
    dashboard_position = Column(JSON)
    is_visible = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Chart data cache for performance
    cached_data = Column(JSON)
    cache_expires_at = Column(DateTime)
    
    # Relationships
    # organization = relationship("Organization", back_populates="wellness_trend_charts")  # Commented out due to circular reference
    creator = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_trend_chart_org', 'organization_id'),
        Index('idx_trend_chart_visible', 'organization_id', 'is_visible'),
    )

class EngagementHeatmap(Base):
    """Model for employee engagement heatmaps"""
    __tablename__ = "engagement_heatmaps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Heatmap configuration
    title = Column(String(200), nullable=False)
    heatmap_type = Column(String(50), nullable=False)  # department, time, activity, geography
    
    # Data configuration
    metric_type = Column(String(100), nullable=False)  # engagement_score, activity_level, etc.
    aggregation_method = Column(String(50), default="average")  # average, sum, count, max, min
    time_period_days = Column(Integer, default=7)
    
    # Visual configuration
    color_scheme = Column(String(50), default="heat")  # heat, cool, viridis, plasma
    cell_size = Column(String(50), default="medium")  # small, medium, large
    show_values = Column(Boolean, default=True)
    show_labels = Column(Boolean, default=True)
    
    # Interactivity
    clickable_cells = Column(Boolean, default=True)
    tooltip_enabled = Column(Boolean, default=True)
    drill_down_enabled = Column(Boolean, default=True)
    
    # Filters and grouping
    department_filter = Column(ARRAY(String))
    role_filter = Column(ARRAY(String))
    employee_filter = Column(ARRAY(Integer))
    
    # Position and visibility
    dashboard_position = Column(JSON)
    is_visible = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Heatmap data cache
    cached_heatmap_data = Column(JSON)
    cache_expires_at = Column(DateTime)
    
    # Relationships
    # organization = relationship("Organization", back_populates="engagement_heatmaps")  # Commented out due to circular reference
    creator = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_heatmap_org_type', 'organization_id', 'heatmap_type'),
        Index('idx_heatmap_visible', 'organization_id', 'is_visible'),
    )

class WellnessROICalculation(Base):
    """Model for wellness program ROI calculations and tracking"""
    __tablename__ = "wellness_roi_calculations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # ROI calculation configuration
    calculation_name = Column(String(200), nullable=False)
    roi_category = Column(String(100), nullable=False)  # ROICategory enum
    calculation_period_months = Column(Integer, default=12)
    
    # Financial data (all in organization's currency)
    program_investment = Column(Float, nullable=False)  # Total investment in wellness program
    baseline_costs = Column(Float)  # Pre-program costs (healthcare, absenteeism, etc.)
    current_costs = Column(Float)  # Current costs
    cost_savings = Column(Float)  # Calculated savings
    
    # Productivity metrics
    baseline_productivity_score = Column(Float)
    current_productivity_score = Column(Float)
    productivity_improvement_percent = Column(Float)
    
    # Healthcare metrics
    baseline_healthcare_costs = Column(Float)
    current_healthcare_costs = Column(Float)
    healthcare_cost_reduction = Column(Float)
    
    # Absenteeism metrics
    baseline_absenteeism_days = Column(Float)
    current_absenteeism_days = Column(Float)
    absenteeism_cost_per_day = Column(Float)
    absenteeism_savings = Column(Float)
    
    # Turnover metrics
    baseline_turnover_rate = Column(Float)
    current_turnover_rate = Column(Float)
    turnover_cost_per_employee = Column(Float)
    turnover_savings = Column(Float)
    
    # Engagement metrics
    baseline_engagement_score = Column(Float)
    current_engagement_score = Column(Float)
    engagement_roi_multiplier = Column(Float, default=1.5)
    
    # Calculated ROI metrics
    total_benefits = Column(Float)
    net_benefits = Column(Float)  # total_benefits - program_investment
    roi_percentage = Column(Float)  # (net_benefits / program_investment) * 100
    payback_period_months = Column(Float)
    break_even_point = Column(DateTime)
    
    # Confidence and accuracy
    confidence_level = Column(Float, default=0.8)  # 0-1 scale
    data_quality_score = Column(Float)  # 0-1 scale
    calculation_method = Column(String(100))  # standard, conservative, aggressive
    
    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculated_by = Column(Integer, ForeignKey("users.id"))
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Validation and approval
    is_validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"))
    validated_at = Column(DateTime)
    
    # Relationships
    # organization = relationship("Organization", back_populates="wellness_roi_calculations")  # Commented out due to circular reference
    calculator = relationship("User", foreign_keys=[calculated_by])
    validator = relationship("User", foreign_keys=[validated_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_roi_org_category', 'organization_id', 'roi_category'),
        Index('idx_roi_calculated_at', 'organization_id', 'calculated_at'),
    )

class DashboardWidget(Base):
    """Model for customizable dashboard widgets"""
    __tablename__ = "dashboard_widgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))  # For user-specific widgets
    
    # Widget identification
    widget_name = Column(String(200), nullable=False)
    widget_type = Column(String(50), nullable=False)  # WidgetType enum
    widget_category = Column(String(100))  # wellness, engagement, roi, productivity
    
    # Widget configuration
    title = Column(String(200), nullable=False)
    subtitle = Column(String(300))
    description = Column(Text)
    
    # Data source configuration
    data_source = Column(String(100), nullable=False)  # API endpoint or calculation method
    data_parameters = Column(JSON)  # Parameters for data fetching
    refresh_interval_minutes = Column(Integer, default=15)
    
    # Visual configuration
    visual_config = Column(JSON)  # Colors, fonts, sizes, etc.
    layout_config = Column(JSON)  # Position, dimensions, responsive settings
    interaction_config = Column(JSON)  # Click handlers, drill-down options
    
    # Display settings
    show_title = Column(Boolean, default=True)
    show_description = Column(Boolean, default=False)
    show_last_updated = Column(Boolean, default=True)
    show_export_button = Column(Boolean, default=True)
    
    # Dashboard positioning
    dashboard_id = Column(String(100))  # Which dashboard this belongs to
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=4)  # Grid units
    height = Column(Integer, default=3)  # Grid units
    z_index = Column(Integer, default=1)
    
    # Visibility and permissions
    is_visible = Column(Boolean, default=True)
    is_shared = Column(Boolean, default=False)  # Shared with other users
    view_permissions = Column(ARRAY(String))  # User IDs or roles
    edit_permissions = Column(ARRAY(String))  # User IDs or roles
    
    # Widget state
    is_loading = Column(Boolean, default=False)
    last_data_fetch = Column(DateTime)
    error_state = Column(Text)  # Last error message
    
    # Caching
    cached_data = Column(JSON)
    cache_expires_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    # organization = relationship("Organization", back_populates="dashboard_widgets")  # Commented out due to circular reference
    # user = relationship("User", foreign_keys=[user_id], back_populates="dashboard_widgets")  # Commented out due to circular reference
    creator = relationship("User", foreign_keys=[created_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_widget_org_user', 'organization_id', 'user_id'),
        Index('idx_widget_dashboard', 'organization_id', 'dashboard_id'),
        Index('idx_widget_visible', 'organization_id', 'is_visible'),
        Index('idx_widget_type', 'widget_type', 'widget_category'),
    )

class RealTimeMetric(Base):
    """Model for storing real-time wellness metrics for dashboard updates"""
    __tablename__ = "real_time_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"))
    
    # Metric identification
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(String(50), nullable=False)  # wellness, engagement, productivity
    metric_subcategory = Column(String(50))
    
    # Metric values
    current_value = Column(Float, nullable=False)
    previous_value = Column(Float)
    change_amount = Column(Float)
    change_percentage = Column(Float)
    
    # Trend analysis
    trend_direction = Column(String(20))  # TrendDirection enum
    trend_strength = Column(Float)  # 0-1 scale
    trend_confidence = Column(Float)  # 0-1 scale
    
    # Time information
    measurement_timestamp = Column(DateTime, nullable=False)
    aggregation_period = Column(String(20))  # daily, weekly, monthly
    
    # Data quality
    data_source = Column(String(100))  # Where the data came from
    confidence_score = Column(Float, default=1.0)  # 0-1 scale
    is_estimated = Column(Boolean, default=False)
    
    # Contextual information
    context_data = Column(JSON)  # Additional context about the measurement
    anomaly_detected = Column(Boolean, default=False)
    anomaly_score = Column(Float)  # If anomalous, how anomalous (0-1)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # organization = relationship("Organization", back_populates="real_time_metrics")  # Commented out due to circular reference
    # employee = relationship("User", back_populates="real_time_metrics")  # Commented out due to circular reference
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_realtime_org_metric', 'organization_id', 'metric_name'),
        Index('idx_realtime_employee', 'employee_id', 'metric_name'),
        Index('idx_realtime_timestamp', 'organization_id', 'measurement_timestamp'),
        Index('idx_realtime_category', 'organization_id', 'metric_category'),
    )

class DashboardTemplate(Base):
    """Model for pre-built dashboard templates"""
    __tablename__ = "dashboard_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template identification
    template_name = Column(String(200), nullable=False)
    template_category = Column(String(100), nullable=False)  # executive, manager, hr, wellness
    description = Column(Text)
    
    # Template configuration
    layout_config = Column(JSON, nullable=False)  # Complete layout definition
    default_widgets = Column(JSON, nullable=False)  # Array of widget configurations
    
    # Template metadata
    industry_tags = Column(ARRAY(String))  # healthcare, tech, manufacturing, etc.
    company_size_tags = Column(ARRAY(String))  # startup, small, medium, large, enterprise
    feature_tags = Column(ARRAY(String))  # roi-focused, engagement-focused, etc.
    
    # Usage and popularity
    usage_count = Column(Integer, default=0)
    rating_average = Column(Float)
    rating_count = Column(Integer, default=0)
    
    # Template status
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    version = Column(String(20), default="1.0")
    
    # Customization options
    customization_level = Column(String(50), default="medium")  # low, medium, high
    required_data_sources = Column(ARRAY(String))
    optional_data_sources = Column(ARRAY(String))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))  # System or admin user
    
    # Indexes
    __table_args__ = (
        Index('idx_template_category', 'template_category'),
        Index('idx_template_active', 'is_active'),
        Index('idx_template_usage', 'usage_count'),
    )

# =================== RELATIONSHIP UPDATES ===================

# Add relationships to existing models (these would be added to the respective model files)

"""
# Add to Organization model:
# Temporarily commented out to avoid circular import issues
# wellness_progress_bars = relationship("WellnessProgressBar", back_populates="organization")
# wellness_trend_charts = relationship("WelnessTrendChart", back_populates="organization")
# engagement_heatmaps = relationship("EngagementHeatmap", back_populates="organization")
# wellness_roi_calculations = relationship("WellnessROICalculation", back_populates="organization")
# dashboard_widgets = relationship("DashboardWidget", back_populates="organization")
# real_time_metrics = relationship("RealTimeMetric", back_populates="organization")

# Add to User model:
# dashboard_widgets = relationship("DashboardWidget", foreign_keys="DashboardWidget.user_id", back_populates="user")
real_time_metrics = relationship("RealTimeMetric", back_populates="employee")
"""
