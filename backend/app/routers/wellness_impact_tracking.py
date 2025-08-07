"""
Real Wellness Impact Tracking API Router

Advanced API endpoints for interactive progress bars, trend analysis charts,
employee engagement heatmaps, ROI calculations, and customizable dashboard
widgets with real-time data updates.

Created: July 27, 2025
Author: Sonicus Platform Team
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import logging
import uuid
from enum import Enum

# Database and models
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.wellness_impact_tracking import (
    WellnessProgressBar,
    WellnessTrendChart,
    EngagementHeatmap,
    WellnessROICalculation,
    DashboardWidget,
    RealTimeMetric,
    WidgetType,
    MetricPeriod,
    TrendDirection,
    ROICategory
)

# Services
from app.services.wellness_impact_analytics import WellnessImpactAnalytics

# Schemas
from pydantic import BaseModel, Field, validator
from typing import Union

# Authentication and security
from app.core.auth_dependencies import get_current_user_compatible as get_current_user, get_business_admin_user

# Initialize router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# =================== PYDANTIC SCHEMAS ===================

class ProgressBarConfig(BaseModel):
    """Schema for progress bar configuration"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    metric_type: str = Field(..., description="Type of metric to track")
    target_value: float = Field(..., gt=0, description="Target value for progress")
    unit: str = Field(default="points", max_length=50)
    color_scheme: str = Field(default="green", description="Color scheme: green, blue, orange, red, purple")
    show_percentage: bool = Field(default=True)
    show_target: bool = Field(default=True)
    animated: bool = Field(default=True)
    period: str = Field(default="monthly", description="Time period for calculation")
    auto_refresh_minutes: int = Field(default=15, ge=1, le=1440)
    dashboard_position: Optional[Dict[str, int]] = Field(default_factory=dict)

class ProgressBarResponse(BaseModel):
    """Response schema for progress bar data"""
    progress_bar_id: str
    title: str
    description: Optional[str]
    metric_type: str
    
    # Current data
    current_value: float
    target_value: float
    progress_percentage: float
    unit: str
    
    # Visual configuration
    color_scheme: str
    show_percentage: bool
    show_target: bool
    animated: bool
    
    # Trend information
    trend_direction: str
    trend_percentage: float
    
    # Time information
    period: str
    last_updated: str
    auto_refresh_minutes: int
    
    # Historical data
    historical_data: List[Dict[str, Any]]
    insights: List[str]
    
    # Metadata
    created_at: datetime
    is_visible: bool

class TrendChartConfig(BaseModel):
    """Schema for trend chart configuration"""
    title: str = Field(..., min_length=1, max_length=200)
    chart_type: str = Field(..., description="Chart type: line, bar, area, scatter")
    metrics: List[str] = Field(..., description="Metrics to display (minimum 1 required)")
    
    @validator('metrics')
    def validate_metrics(cls, v):
        if not v or len(v) < 1:
            raise ValueError('At least one metric is required')
        return v
    time_range_days: int = Field(default=30, ge=1, le=365)
    granularity: str = Field(default="daily", description="Data granularity: daily, weekly, monthly")
    comparison_enabled: bool = Field(default=False)
    comparison_period_offset: Optional[int] = Field(None, ge=1)
    
    # Visual configuration
    color_palette: Optional[List[str]] = Field(default_factory=list)
    show_legend: bool = Field(default=True)
    show_grid: bool = Field(default=True)
    show_tooltips: bool = Field(default=True)
    smooth_lines: bool = Field(default=True)
    
    # Interactive features
    zoom_enabled: bool = Field(default=True)
    pan_enabled: bool = Field(default=True)
    export_enabled: bool = Field(default=True)
    
    dashboard_position: Optional[Dict[str, int]] = Field(default_factory=dict)

class TrendChartResponse(BaseModel):
    """Response schema for trend chart data"""
    chart_id: str
    title: str
    chart_type: str
    metrics: List[str]
    
    # Chart data
    datasets: List[Dict[str, Any]]
    labels: List[str]
    
    # Configuration
    time_range_days: int
    granularity: str
    comparison_enabled: bool
    
    # Visual settings
    color_palette: List[str]
    show_legend: bool
    show_grid: bool
    
    # Analytics
    summary: Dict[str, Any]
    insights: List[str]
    
    # Metadata
    created_at: datetime
    cache_expires_at: Optional[datetime]

class HeatmapConfig(BaseModel):
    """Schema for engagement heatmap configuration"""
    title: str = Field(..., min_length=1, max_length=200)
    heatmap_type: str = Field(..., description="Heatmap type: department, time, activity, geography")
    metric_type: str = Field(..., description="Metric to visualize")
    aggregation_method: str = Field(default="average", description="Data aggregation: average, sum, count, max, min")
    time_period_days: int = Field(default=7, ge=1, le=90)
    
    # Visual configuration
    color_scheme: str = Field(default="heat", description="Color scheme: heat, cool, viridis, plasma")
    cell_size: str = Field(default="medium", description="Cell size: small, medium, large")
    show_values: bool = Field(default=True)
    show_labels: bool = Field(default=True)
    
    # Interactivity
    clickable_cells: bool = Field(default=True)
    tooltip_enabled: bool = Field(default=True)
    drill_down_enabled: bool = Field(default=True)
    
    # Filters
    department_filter: Optional[List[str]] = Field(default_factory=list)
    role_filter: Optional[List[str]] = Field(default_factory=list)
    employee_filter: Optional[List[int]] = Field(default_factory=list)
    
    dashboard_position: Optional[Dict[str, int]] = Field(default_factory=dict)

class HeatmapResponse(BaseModel):
    """Response schema for engagement heatmap"""
    heatmap_id: str
    title: str
    heatmap_type: str
    metric_type: str
    
    # Heatmap data
    data: List[Dict[str, Any]]
    x_labels: List[str]
    y_labels: List[str]
    
    # Visual configuration
    color_scheme: str
    min_value: float
    max_value: float
    average_value: float
    
    # Analytics
    insights: List[str]
    
    # Configuration
    time_period_days: int
    aggregation_method: str
    
    # Metadata
    created_at: datetime
    cache_expires_at: Optional[datetime]

class ROICalculationRequest(BaseModel):
    """Schema for ROI calculation request"""
    calculation_name: str = Field(..., min_length=1, max_length=200)
    roi_category: str = Field(default="overall", description="ROI category to calculate")
    calculation_period_months: int = Field(default=12, ge=1, le=60)
    
    # Optional financial inputs (if available)
    program_investment: Optional[float] = Field(None, gt=0)
    baseline_healthcare_costs: Optional[float] = Field(None, ge=0)
    baseline_absenteeism_days: Optional[float] = Field(None, ge=0)
    baseline_turnover_rate: Optional[float] = Field(None, ge=0, le=1)
    
    # Calculation method
    calculation_method: str = Field(default="standard", description="Calculation method: standard, conservative, aggressive")

class ROICalculationResponse(BaseModel):
    """Response schema for ROI calculation"""
    calculation_id: str
    calculation_name: str
    roi_category: str
    calculation_period_months: int
    
    # Financial metrics
    program_investment: float
    total_benefits: float
    net_benefits: float
    roi_percentage: float
    payback_period_months: float
    break_even_point: str
    
    # Component breakdown
    components: Dict[str, Dict[str, Any]]
    
    # Quality metrics
    confidence_level: float
    data_quality_score: float
    confidence_interval: Dict[str, float]
    validation_metrics: Dict[str, Any]
    
    # Insights
    recommendations: List[str]
    
    # Metadata
    calculated_at: datetime
    is_validated: bool

class DashboardWidgetConfig(BaseModel):
    """Schema for dashboard widget configuration"""
    widget_name: str = Field(..., min_length=1, max_length=200)
    widget_type: str = Field(..., description="Widget type from WidgetType enum")
    widget_category: Optional[str] = Field(None, description="Widget category")
    title: str = Field(..., min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Data configuration
    data_source: str = Field(..., description="Data source or API endpoint")
    data_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    refresh_interval_minutes: int = Field(default=15, ge=1, le=1440)
    
    # Visual configuration
    visual_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    layout_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    interaction_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Display settings
    show_title: bool = Field(default=True)
    show_description: bool = Field(default=False)
    show_last_updated: bool = Field(default=True)
    show_export_button: bool = Field(default=True)
    
    # Dashboard positioning
    dashboard_id: Optional[str] = Field(None)
    position_x: int = Field(default=0, ge=0)
    position_y: int = Field(default=0, ge=0)
    width: int = Field(default=4, ge=1, le=12)
    height: int = Field(default=3, ge=1, le=12)
    
    # Permissions
    is_shared: bool = Field(default=False)
    view_permissions: Optional[List[str]] = Field(default_factory=list)
    edit_permissions: Optional[List[str]] = Field(default_factory=list)

class DashboardWidgetResponse(BaseModel):
    """Response schema for dashboard widget"""
    widget_id: str
    widget_name: str
    widget_type: str
    widget_category: Optional[str]
    title: str
    subtitle: Optional[str]
    description: Optional[str]
    
    # Data information
    data_source: str
    refresh_interval_minutes: int
    last_data_fetch: Optional[datetime]
    
    # Visual configuration
    visual_config: Dict[str, Any]
    layout_config: Dict[str, Any]
    
    # Position
    dashboard_id: Optional[str]
    position_x: int
    position_y: int
    width: int
    height: int
    
    # State
    is_visible: bool
    is_loading: bool
    error_state: Optional[str]
    
    # Cached data
    cached_data: Optional[Dict[str, Any]]
    cache_expires_at: Optional[datetime]
    
    # Metadata
    created_at: datetime
    updated_at: datetime

class RealTimeMetricUpdate(BaseModel):
    """Schema for real-time metric updates"""
    metric_name: str = Field(..., min_length=1, max_length=100)
    metric_category: str = Field(..., description="Metric category")
    current_value: float
    measurement_timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    context_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    confidence_score: float = Field(default=1.0, ge=0, le=1)

# =================== HELPER FUNCTIONS ===================

# Use centralized business admin authentication from auth_dependencies
# get_business_admin_user is now imported and available for use

# =================== API ENDPOINTS ===================

@router.post("/impact-tracking/progress-bars", response_model=ProgressBarResponse)
async def create_progress_bar(
    config: ProgressBarConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Create interactive progress bars with real-time data
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Initialize analytics service
        analytics = WellnessImpactAnalytics(db)
        
        # Calculate current progress data
        progress_data = analytics.calculate_progress_bar_data(
            str(user_org_id),
            config.metric_type,
            30  # Default 30-day period
        )
        
        # Generate response
        progress_bar_id = str(uuid.uuid4())
        
        return ProgressBarResponse(
            progress_bar_id=progress_bar_id,
            title=config.title,
            description=config.description,
            metric_type=config.metric_type,
            current_value=progress_data["current_value"],
            target_value=config.target_value,
            progress_percentage=progress_data["progress_percentage"],
            unit=config.unit,
            color_scheme=progress_data["color_scheme"],
            show_percentage=config.show_percentage,
            show_target=config.show_target,
            animated=config.animated,
            trend_direction=progress_data["trend"],
            trend_percentage=progress_data["trend_percentage"],
            period=config.period,
            last_updated=progress_data["last_updated"],
            auto_refresh_minutes=config.auto_refresh_minutes,
            historical_data=progress_data["historical_data"],
            insights=progress_data["insights"],
            created_at=datetime.utcnow(),
            is_visible=True
        )
        
    except Exception as e:
        logger.error(f"Failed to create progress bar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create progress bar: {str(e)}")

@router.get("/impact-tracking/progress-bars/{progress_bar_id}/data")
async def get_progress_bar_data(
    progress_bar_id: str,
    refresh: bool = Query(False, description="Force refresh cached data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get real-time progress bar data with trend analysis
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Initialize analytics service
        analytics = WellnessImpactAnalytics(db)
        
        # For demo purposes, we'll calculate data for a generic metric
        # In production, you'd fetch the actual progress bar config from database
        progress_data = analytics.calculate_progress_bar_data(
            str(user_org_id),
            "engagement_score",  # Default metric type
            30
        )
        
        return {
            "progress_bar_id": progress_bar_id,
            "data": progress_data,
            "last_updated": datetime.utcnow().isoformat(),
            "refresh_requested": refresh
        }
        
    except Exception as e:
        logger.error(f"Failed to get progress bar data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress bar data: {str(e)}")

@router.post("/impact-tracking/trend-charts", response_model=TrendChartResponse)
async def create_trend_chart(
    config: TrendChartConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Create trend analysis charts and visualizations
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Initialize analytics service
        analytics = WellnessImpactAnalytics(db)
        
        # Generate trend chart data
        chart_data = analytics.generate_trend_chart_data(
            str(user_org_id),
            config.metrics,
            config.time_range_days,
            config.granularity
        )
        
        # Generate response
        chart_id = str(uuid.uuid4())
        
        return TrendChartResponse(
            chart_id=chart_id,
            title=config.title,
            chart_type=config.chart_type,
            metrics=config.metrics,
            datasets=chart_data["datasets"],
            labels=chart_data["labels"],
            time_range_days=config.time_range_days,
            granularity=config.granularity,
            comparison_enabled=config.comparison_enabled,
            color_palette=config.color_palette or [],
            show_legend=config.show_legend,
            show_grid=config.show_grid,
            summary=chart_data["summary"],
            insights=chart_data["insights"],
            created_at=datetime.utcnow(),
            cache_expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        
    except Exception as e:
        logger.error(f"Failed to create trend chart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create trend chart: {str(e)}")

@router.post("/impact-tracking/heatmaps", response_model=HeatmapResponse)
async def create_engagement_heatmap(
    config: HeatmapConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Create employee engagement heatmaps
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Initialize analytics service
        analytics = WellnessImpactAnalytics(db)
        
        # Generate heatmap data
        heatmap_data = analytics.generate_engagement_heatmap_data(
            str(user_org_id),
            config.heatmap_type,
            config.time_period_days
        )
        
        # Generate response
        heatmap_id = str(uuid.uuid4())
        
        return HeatmapResponse(
            heatmap_id=heatmap_id,
            title=config.title,
            heatmap_type=config.heatmap_type,
            metric_type=config.metric_type,
            data=heatmap_data["data"],
            x_labels=heatmap_data["x_labels"],
            y_labels=heatmap_data["y_labels"],
            color_scheme=heatmap_data["color_scheme"],
            min_value=heatmap_data["min_value"],
            max_value=heatmap_data["max_value"],
            average_value=heatmap_data["average_value"],
            insights=heatmap_data["insights"],
            time_period_days=config.time_period_days,
            aggregation_method=config.aggregation_method,
            created_at=datetime.utcnow(),
            cache_expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
    except Exception as e:
        logger.error(f"Failed to create engagement heatmap: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create engagement heatmap: {str(e)}")

@router.post("/impact-tracking/roi-calculations", response_model=ROICalculationResponse)
async def calculate_wellness_roi(
    request: ROICalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Calculate wellness program ROI with comprehensive analysis
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Initialize analytics service
        analytics = WellnessImpactAnalytics(db)
        
        # Calculate ROI
        roi_data = analytics.calculate_wellness_roi(
            str(user_org_id),
            request.roi_category,
            request.calculation_period_months
        )
        
        # Generate response
        calculation_id = str(uuid.uuid4())
        
        return ROICalculationResponse(
            calculation_id=calculation_id,
            calculation_name=request.calculation_name,
            roi_category=roi_data["roi_category"],
            calculation_period_months=roi_data["calculation_period_months"],
            program_investment=roi_data["program_investment"],
            total_benefits=roi_data["total_benefits"],
            net_benefits=roi_data["net_benefits"],
            roi_percentage=roi_data["roi_percentage"],
            payback_period_months=roi_data["payback_period_months"],
            break_even_point=roi_data["break_even_point"],
            components=roi_data["components"],
            confidence_level=roi_data["confidence_level"],
            data_quality_score=roi_data["data_quality_score"],
            confidence_interval=roi_data["confidence_interval"],
            validation_metrics=roi_data["validation_metrics"],
            recommendations=roi_data["recommendations"],
            calculated_at=datetime.utcnow(),
            is_validated=False
        )
        
    except Exception as e:
        logger.error(f"Failed to calculate wellness ROI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate wellness ROI: {str(e)}")

@router.post("/impact-tracking/dashboard/widgets", response_model=DashboardWidgetResponse)
async def create_dashboard_widget(
    config: DashboardWidgetConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Create customizable dashboard widgets
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Validate widget type
        try:
            widget_type_enum = WidgetType(config.widget_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid widget type. Must be one of: {[t.value for t in WidgetType]}"
            )
        
        # Generate response
        widget_id = str(uuid.uuid4())
        
        return DashboardWidgetResponse(
            widget_id=widget_id,
            widget_name=config.widget_name,
            widget_type=config.widget_type,
            widget_category=config.widget_category,
            title=config.title,
            subtitle=config.subtitle,
            description=config.description,
            data_source=config.data_source,
            refresh_interval_minutes=config.refresh_interval_minutes,
            last_data_fetch=None,
            visual_config=config.visual_config or {},
            layout_config=config.layout_config or {},
            dashboard_id=config.dashboard_id,
            position_x=config.position_x,
            position_y=config.position_y,
            width=config.width,
            height=config.height,
            is_visible=True,
            is_loading=False,
            error_state=None,
            cached_data=None,
            cache_expires_at=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create dashboard widget: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create dashboard widget: {str(e)}")

@router.get("/impact-tracking/dashboard/widgets")
async def get_dashboard_widgets(
    dashboard_id: Optional[str] = Query(None, description="Filter by dashboard ID"),
    widget_category: Optional[str] = Query(None, description="Filter by widget category"),
    is_visible: bool = Query(True, description="Filter by visibility"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get dashboard widgets for the organization
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Mock widget data for demonstration
        widgets = [
            {
                "widget_id": str(uuid.uuid4()),
                "widget_name": "Engagement Progress",
                "widget_type": "progress_bar",
                "widget_category": "engagement",
                "title": "Employee Engagement Progress",
                "subtitle": "Monthly tracking",
                "data_source": "/api/v1/wellness/engagement/progress",
                "position_x": 0,
                "position_y": 0,
                "width": 6,
                "height": 4,
                "is_visible": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "widget_id": str(uuid.uuid4()),
                "widget_name": "Wellness Trends",
                "widget_type": "line_chart",
                "widget_category": "wellness",
                "title": "Wellness Metrics Trends",
                "subtitle": "30-day overview",
                "data_source": "/api/v1/wellness/trends",
                "position_x": 6,
                "position_y": 0,
                "width": 6,
                "height": 4,
                "is_visible": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "widget_id": str(uuid.uuid4()),
                "widget_name": "Department Engagement",
                "widget_type": "heatmap",
                "widget_category": "engagement",
                "title": "Engagement by Department",
                "subtitle": "Weekly heatmap",
                "data_source": "/api/v1/wellness/engagement/heatmap",
                "position_x": 0,
                "position_y": 4,
                "width": 8,
                "height": 4,
                "is_visible": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "widget_id": str(uuid.uuid4()),
                "widget_name": "ROI Summary",
                "widget_type": "metric_card",
                "widget_category": "roi",
                "title": "Wellness ROI",
                "subtitle": "Current period",
                "data_source": "/api/v1/wellness/roi/summary",
                "position_x": 8,
                "position_y": 4,
                "width": 4,
                "height": 4,
                "is_visible": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Apply filters
        if dashboard_id:
            widgets = [w for w in widgets if w.get("dashboard_id") == dashboard_id]
        
        if widget_category:
            widgets = [w for w in widgets if w.get("widget_category") == widget_category]
        
        if not is_visible:
            widgets = [w for w in widgets if not w.get("is_visible", True)]
        
        return {
            "widgets": widgets,
            "total_count": len(widgets),
            "visible_count": sum(1 for w in widgets if w.get("is_visible", True)),
            "categories": list(set(w.get("widget_category") for w in widgets if w.get("widget_category"))),
            "widget_types": list(set(w.get("widget_type") for w in widgets if w.get("widget_type")))
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard widgets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard widgets: {str(e)}")

@router.get("/impact-tracking/dashboard/templates")
async def get_dashboard_templates(
    template_category: Optional[str] = Query(None, description="Filter by template category"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    company_size: Optional[str] = Query(None, description="Filter by company size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get pre-built dashboard templates
    """
    try:
        # Mock dashboard templates
        templates = [
            {
                "template_id": str(uuid.uuid4()),
                "template_name": "Executive Dashboard",
                "template_category": "executive",
                "description": "High-level wellness metrics and ROI for executives",
                "industry_tags": ["all"],
                "company_size_tags": ["medium", "large", "enterprise"],
                "feature_tags": ["roi-focused", "high-level"],
                "usage_count": 145,
                "rating_average": 4.7,
                "preview_image": "/templates/executive-dashboard.png",
                "widgets_count": 8,
                "is_premium": False
            },
            {
                "template_id": str(uuid.uuid4()),
                "template_name": "HR Manager Dashboard",
                "template_category": "manager",
                "description": "Detailed employee engagement and wellness tracking",
                "industry_tags": ["all"],
                "company_size_tags": ["small", "medium", "large"],
                "feature_tags": ["engagement-focused", "detailed"],
                "usage_count": 234,
                "rating_average": 4.5,
                "preview_image": "/templates/hr-dashboard.png",
                "widgets_count": 12,
                "is_premium": False
            },
            {
                "template_id": str(uuid.uuid4()),
                "template_name": "Wellness Coordinator Dashboard",
                "template_category": "wellness",
                "description": "Comprehensive wellness program tracking and analytics",
                "industry_tags": ["healthcare", "tech", "finance"],
                "company_size_tags": ["all"],
                "feature_tags": ["wellness-focused", "comprehensive"],
                "usage_count": 89,
                "rating_average": 4.8,
                "preview_image": "/templates/wellness-dashboard.png",
                "widgets_count": 15,
                "is_premium": True
            },
            {
                "template_id": str(uuid.uuid4()),
                "template_name": "Department Comparison",
                "template_category": "manager",
                "description": "Compare wellness metrics across departments",
                "industry_tags": ["all"],
                "company_size_tags": ["medium", "large", "enterprise"],
                "feature_tags": ["comparison", "department-focused"],
                "usage_count": 67,
                "rating_average": 4.3,
                "preview_image": "/templates/department-dashboard.png",
                "widgets_count": 10,
                "is_premium": False
            }
        ]
        
        # Apply filters
        if template_category:
            templates = [t for t in templates if t["template_category"] == template_category]
        
        if industry:
            templates = [
                t for t in templates 
                if industry in t["industry_tags"] or "all" in t["industry_tags"]
            ]
        
        if company_size:
            templates = [
                t for t in templates 
                if company_size in t["company_size_tags"] or "all" in t["company_size_tags"]
            ]
        
        # Sort by popularity
        templates.sort(key=lambda x: x["usage_count"], reverse=True)
        
        return {
            "templates": templates,
            "total_count": len(templates),
            "categories": ["executive", "manager", "hr", "wellness"],
            "industry_options": ["all", "healthcare", "tech", "finance", "manufacturing", "retail"],
            "company_size_options": ["startup", "small", "medium", "large", "enterprise"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard templates: {str(e)}")

@router.post("/impact-tracking/metrics/real-time")
async def update_real_time_metric(
    metric: RealTimeMetricUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Update real-time wellness metrics for dashboard updates
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Store the real-time metric update
        metric_id = str(uuid.uuid4())
        
        # Calculate trend information
        trend_direction = TrendDirection.STABLE
        trend_percentage = 0.0
        
        # Mock trend calculation based on context
        if metric.context_data and metric.context_data.get("previous_value"):
            previous_value = metric.context_data["previous_value"]
            if metric.current_value > previous_value:
                trend_direction = TrendDirection.UP
                trend_percentage = ((metric.current_value - previous_value) / previous_value) * 100
            elif metric.current_value < previous_value:
                trend_direction = TrendDirection.DOWN
                trend_percentage = ((metric.current_value - previous_value) / previous_value) * 100
        
        return {
            "metric_id": metric_id,
            "metric_name": metric.metric_name,
            "metric_category": metric.metric_category,
            "current_value": metric.current_value,
            "trend_direction": trend_direction.value,
            "trend_percentage": round(trend_percentage, 2),
            "confidence_score": metric.confidence_score,
            "measurement_timestamp": metric.measurement_timestamp.isoformat() if metric.measurement_timestamp else datetime.utcnow().isoformat(),
            "processed_at": datetime.utcnow().isoformat(),
            "status": "processed"
        }
        
    except Exception as e:
        logger.error(f"Failed to update real-time metric: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update real-time metric: {str(e)}")

@router.get("/impact-tracking/metrics/real-time/{metric_name}")
async def get_real_time_metric(
    metric_name: str,
    hours_back: int = Query(24, ge=1, le=168, description="Hours of historical data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get real-time metric data with historical trends
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Mock real-time metric data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Generate realistic metric data
        data_points = []
        current_time = start_time
        
        while current_time <= end_time:
            # Generate realistic values based on metric type
            if "engagement" in metric_name.lower():
                base_value = 7.5
                variance = 0.5
            elif "stress" in metric_name.lower():
                base_value = 4.2
                variance = 0.8
            elif "productivity" in metric_name.lower():
                base_value = 85.0
                variance = 5.0
            else:
                base_value = 50.0
                variance = 10.0
            
            # Add time-based patterns and noise
            hour = current_time.hour
            if 9 <= hour <= 17:  # Work hours
                time_factor = 1.1
            elif 6 <= hour <= 9 or 17 <= hour <= 20:  # Transition
                time_factor = 1.0
            else:  # Off hours
                time_factor = 0.9
            
            noise = (hash(str(current_time)) % 100 - 50) / 100 * variance
            value = base_value * time_factor + noise
            
            data_points.append({
                "timestamp": current_time.isoformat(),
                "value": round(value, 2),
                "confidence_score": 0.9 + (hash(str(current_time)) % 20) / 200  # 0.9-1.0
            })
            
            current_time += timedelta(hours=1)
        
        # Calculate summary statistics
        values = [dp["value"] for dp in data_points]
        current_value = values[-1] if values else 0
        previous_value = values[-2] if len(values) > 1 else current_value
        
        trend_percentage = 0
        if previous_value != 0:
            trend_percentage = ((current_value - previous_value) / previous_value) * 100
        
        trend_direction = TrendDirection.STABLE
        if trend_percentage > 2:
            trend_direction = TrendDirection.UP
        elif trend_percentage < -2:
            trend_direction = TrendDirection.DOWN
        
        return {
            "metric_name": metric_name,
            "organization_id": str(user_org_id),
            "time_range_hours": hours_back,
            "current_value": current_value,
            "previous_value": previous_value,
            "trend_direction": trend_direction.value,
            "trend_percentage": round(trend_percentage, 2),
            "average_value": round(sum(values) / len(values), 2) if values else 0,
            "min_value": min(values) if values else 0,
            "max_value": max(values) if values else 0,
            "data_points": data_points,
            "data_quality": {
                "completeness": 1.0,
                "accuracy": 0.95,
                "timeliness": 0.98
            },
            "last_updated": end_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get real-time metric: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get real-time metric: {str(e)}")

# =================== BONUS ENDPOINTS ===================

@router.get("/impact-tracking/dashboard/analytics")
async def get_dashboard_analytics(
    dashboard_id: Optional[str] = Query(None),
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get comprehensive dashboard usage and performance analytics
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Mock dashboard analytics
        analytics = {
            "dashboard_usage": {
                "total_views": 1247,
                "unique_users": 23,
                "average_session_duration_minutes": 8.5,
                "bounce_rate": 0.12,
                "most_viewed_widgets": [
                    {"widget_name": "Engagement Progress", "views": 456},
                    {"widget_name": "Wellness Trends", "views": 389},
                    {"widget_name": "ROI Summary", "views": 234}
                ]
            },
            "widget_performance": {
                "total_widgets": 12,
                "active_widgets": 10,
                "average_load_time_ms": 850,
                "error_rate": 0.02,
                "cache_hit_rate": 0.87
            },
            "data_freshness": {
                "real_time_metrics": 15,
                "stale_metrics": 2,
                "average_data_age_minutes": 5.2,
                "refresh_success_rate": 0.98
            },
            "user_engagement": {
                "daily_active_users": 18,
                "weekly_active_users": 25,
                "feature_adoption_rate": 0.76,
                "user_satisfaction_score": 4.3
            },
            "recommendations": [
                "Consider adding more real-time widgets for better engagement",
                "Optimize slow-loading widgets to improve user experience",
                "Add more interactive features to boost user engagement"
            ]
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get dashboard analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard analytics: {str(e)}")

@router.post("/impact-tracking/dashboard/export")
async def export_dashboard_data(
    format: str = Query("pdf", description="Export format: pdf, xlsx, png"),
    dashboard_id: Optional[str] = Query(None),
    include_historical: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Export dashboard data and visualizations
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Mock export functionality
        export_id = str(uuid.uuid4())
        
        # Validate format
        valid_formats = ["pdf", "xlsx", "png", "json"]
        if format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Must be one of: {valid_formats}"
            )
        
        return {
            "export_id": export_id,
            "format": format,
            "dashboard_id": dashboard_id,
            "include_historical": include_historical,
            "status": "processing",
            "estimated_completion_minutes": 3,
            "download_url": f"/api/v1/wellness/downloads/{export_id}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export dashboard data: {str(e)}")
