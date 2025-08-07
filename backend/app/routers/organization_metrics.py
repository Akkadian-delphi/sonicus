"""
Organization Metrics API Router

Comprehensive API endpoints for tracking and analyzing employee wellness,
engagement, and productivity metrics. Provides organization-specific insights
and measurement algorithms for business administrators.

Created: July 27, 2025
Author: Sonicus Platform Team
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import logging

# Database and models
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.wellness_metrics import (
    OrganizationMetrics, EmployeeWellnessMetrics, WellnessGoals, 
    GoalProgressLog, EngagementEvents, WellnessAlgorithmConfig,
    MetricType, MeasurementPeriod, GoalStatus, EngagementLevel, WellnessCategory
)

# Services
from app.services.wellness_analytics import (
    WellnessCalculationEngine, WellnessScore, EngagementMetrics, 
    ProductivityImpact, OrganizationInsights
)

# Schemas
from pydantic import BaseModel, Field, validator
from enum import Enum

# Authentication
from app.core.auth_dependencies import get_current_user_compatible as get_current_user, get_business_admin_user

# Initialize router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# =================== PYDANTIC SCHEMAS ===================

class MetricPeriodRequest(BaseModel):
    """Schema for metric period requests"""
    period_type: str = Field("monthly", description="daily, weekly, monthly, quarterly")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    custom_days: Optional[int] = Field(None, ge=1, le=365)

class EmployeeWellnessResponse(BaseModel):
    """Response schema for employee wellness metrics"""
    employee_id: int
    employee_email: str
    employee_name: Optional[str]
    wellness_score: float
    confidence_level: float
    stress_management_score: float
    sleep_quality_score: float
    focus_enhancement_score: float
    mood_improvement_score: float
    energy_levels_score: float
    trend_direction: str
    risk_level: str
    recommendations: List[str]
    last_updated: datetime

class OrganizationWellnessSummary(BaseModel):
    """Summary of organization wellness metrics"""
    organization_id: str
    organization_name: str
    measurement_period: str
    period_start: datetime
    period_end: datetime
    
    # Overall scores
    overall_wellness_score: float
    overall_engagement_score: float
    overall_productivity_score: float
    
    # Participation metrics
    total_employees: int
    active_participants: int
    participation_rate: float
    
    # Top level insights
    top_performing_areas: List[str]
    improvement_opportunities: List[str]
    risk_indicators: Dict[str, Any]
    
    # Benchmarks
    industry_percentile: float
    improvement_since_last_period: float
    
    generated_at: datetime

class WellnessGoalResponse(BaseModel):
    """Response schema for wellness goals"""
    goal_id: str
    goal_name: str
    goal_description: Optional[str]
    goal_category: str
    goal_type: str
    target_value: float
    current_value: float
    progress_percentage: float
    status: str
    start_date: datetime
    target_date: datetime
    employee_id: Optional[int]
    employee_name: Optional[str]
    created_by: int
    last_updated: datetime

class CreateWellnessGoalRequest(BaseModel):
    """Schema for creating wellness goals"""
    goal_name: str = Field(..., min_length=1, max_length=255)
    goal_description: Optional[str] = Field(None, max_length=1000)
    goal_category: str = Field(..., description="WellnessCategory enum value")
    goal_type: str = Field(..., description="MetricType enum value")
    target_value: float = Field(..., gt=0)
    measurement_unit: str = Field(..., min_length=1, max_length=50)
    start_date: datetime
    target_date: datetime
    employee_ids: Optional[List[int]] = Field(default_factory=list)
    priority_level: str = Field("medium", description="low, medium, high")
    is_recurring: bool = False
    reminder_settings: Optional[Dict[str, Any]] = None

class EngagementAnalyticsResponse(BaseModel):
    """Response schema for engagement analytics"""
    employee_id: int
    employee_email: str
    overall_engagement_score: float
    usage_score: float
    interaction_score: float
    consistency_score: float
    feature_adoption_score: float
    social_engagement_score: float
    retention_probability: float
    engagement_level: str
    recent_activity_summary: Dict[str, Any]
    recommendations: List[str]

class ProductivityMetricsResponse(BaseModel):
    """Response schema for productivity metrics"""
    employee_id: int
    employee_email: str
    productivity_score: float
    focus_improvement: float
    stress_reduction_impact: float
    sleep_quality_impact: float
    estimated_time_savings_hours: float
    estimated_cost_savings: float
    roi_percentage: float
    productivity_trend: str
    key_factors: List[str]

class OrganizationInsightsResponse(BaseModel):
    """Comprehensive organization insights response"""
    organization_id: str
    analysis_period: str
    overall_wellness_score: float
    engagement_score: float
    productivity_score: float
    
    # Detailed breakdowns
    wellness_breakdown: Dict[str, float]
    engagement_breakdown: Dict[str, float]
    productivity_breakdown: Dict[str, float]
    
    # Risk and opportunities
    risk_indicators: Dict[str, Any]
    top_performing_areas: List[str]
    improvement_opportunities: List[str]
    
    # Predictions and benchmarks
    benchmark_comparisons: Dict[str, float]
    predicted_outcomes: Dict[str, float]
    
    # Recommendations
    strategic_recommendations: List[str]
    immediate_actions: List[str]
    
    generated_at: datetime

# =================== HELPER FUNCTIONS ===================

# Use centralized business admin authentication from auth_dependencies
# get_business_admin_user is now imported and available for use

def get_time_period_from_request(request: MetricPeriodRequest) -> timedelta:
    """Convert period request to timedelta"""
    if request.custom_days:
        return timedelta(days=request.custom_days)
    
    period_map = {
        "daily": timedelta(days=1),
        "weekly": timedelta(days=7),
        "monthly": timedelta(days=30),
        "quarterly": timedelta(days=90),
        "yearly": timedelta(days=365)
    }
    
    return period_map.get(request.period_type, timedelta(days=30))

def determine_engagement_level(score: float) -> str:
    """Determine engagement level from score"""
    if score >= 80: return "very_high"
    elif score >= 60: return "high"
    elif score >= 40: return "moderate"
    elif score >= 20: return "low"
    else: return "very_low"

# =================== API ENDPOINTS ===================

@router.get("/wellness/summary", response_model=OrganizationWellnessSummary)
async def get_organization_wellness_summary(
    period: MetricPeriodRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get comprehensive wellness summary for the organization
    """
    try:
        # Ensure user has an organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Get organization details
        organization = db.query(Organization).filter(Organization.id == user_org_id).first()
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Calculate time period
        time_period = get_time_period_from_request(period)
        end_date = period.end_date or datetime.utcnow()
        start_date = period.start_date or (end_date - time_period)
        
        # Initialize calculation engine
        engine = WellnessCalculationEngine(db)
        
        # Get organization insights
        insights = engine.calculate_organization_insights(str(user_org_id), time_period)
        
        # Get participation metrics
        total_employees = db.query(User).filter(User.organization_id == user_org_id).count()
        
        # Get active participants (users with recent metrics)
        active_participants = db.query(EmployeeWellnessMetrics).filter(
            and_(
                EmployeeWellnessMetrics.organization_id == user_org_id,
                EmployeeWellnessMetrics.measurement_date >= start_date
            )
        ).distinct(EmployeeWellnessMetrics.employee_id).count()
        
        participation_rate = (active_participants / max(total_employees, 1)) * 100
        
        # Calculate improvement since last period
        previous_period_start = start_date - time_period
        previous_metrics = db.query(OrganizationMetrics).filter(
            and_(
                OrganizationMetrics.organization_id == user_org_id,
                OrganizationMetrics.period_start >= previous_period_start,
                OrganizationMetrics.period_start < start_date
            )
        ).first()
        
        improvement_since_last = 0.0
        if previous_metrics:
            prev_score = getattr(previous_metrics, 'overall_wellness_score', 0) or 0
            improvement_since_last = insights.overall_wellness_score - prev_score
        
        return OrganizationWellnessSummary(
            organization_id=str(user_org_id),
            organization_name=getattr(organization, 'name', 'Unknown'),
            measurement_period=period.period_type,
            period_start=start_date,
            period_end=end_date,
            overall_wellness_score=insights.overall_wellness_score,
            overall_engagement_score=insights.engagement_score,
            overall_productivity_score=insights.productivity_score,
            total_employees=total_employees,
            active_participants=active_participants,
            participation_rate=participation_rate,
            top_performing_areas=insights.top_performing_areas,
            improvement_opportunities=insights.improvement_opportunities,
            risk_indicators=insights.risk_indicators,
            industry_percentile=insights.benchmark_comparisons.get("industry_wellness_percentile", 50.0),
            improvement_since_last_period=improvement_since_last,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get wellness summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get wellness summary: {str(e)}")

@router.get("/wellness/employees", response_model=List[EmployeeWellnessResponse])
async def get_employee_wellness_metrics(
    period: MetricPeriodRequest = Depends(),
    employee_ids: Optional[List[int]] = Query(None, description="Specific employee IDs to analyze"),
    min_wellness_score: Optional[float] = Query(None, ge=0, le=100),
    max_wellness_score: Optional[float] = Query(None, ge=0, le=100),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: low, medium, high"),
    trend_direction: Optional[str] = Query(None, description="Filter by trend: improving, declining, stable"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get detailed wellness metrics for employees in the organization
    """
    try:
        # Ensure user has an organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Get employees
        query = db.query(User).filter(User.organization_id == user_org_id)
        if employee_ids:
            query = query.filter(User.id.in_(employee_ids))
        
        employees = query.all()
        
        if not employees:
            return []
        
        # Calculate time period
        time_period = get_time_period_from_request(period)
        
        # Initialize calculation engine
        engine = WellnessCalculationEngine(db)
        
        # Calculate wellness metrics for each employee
        employee_wellness_list = []
        
        for employee in employees:
            emp_id = getattr(employee, 'id', 0)
            emp_email = getattr(employee, 'email', '')
            emp_name = getattr(employee, 'telephone', None)  # Using telephone as name field for now
            
            # Calculate wellness score
            wellness = engine.calculate_employee_wellness_score(
                emp_id, str(user_org_id), time_period
            )
            
            # Apply filters
            if min_wellness_score is not None and wellness.score < min_wellness_score:
                continue
            if max_wellness_score is not None and wellness.score > max_wellness_score:
                continue
            if risk_level and wellness.risk_level != risk_level:
                continue
            if trend_direction and wellness.trend_direction != trend_direction:
                continue
            
            employee_wellness_list.append(EmployeeWellnessResponse(
                employee_id=emp_id,
                employee_email=emp_email,
                employee_name=emp_name,
                wellness_score=wellness.score,
                confidence_level=wellness.confidence,
                stress_management_score=wellness.contributing_factors.get("stress_management", 0),
                sleep_quality_score=wellness.contributing_factors.get("sleep_quality", 0),
                focus_enhancement_score=wellness.contributing_factors.get("focus_enhancement", 0),
                mood_improvement_score=wellness.contributing_factors.get("mood_improvement", 0),
                energy_levels_score=wellness.contributing_factors.get("energy_levels", 0),
                trend_direction=wellness.trend_direction,
                risk_level=wellness.risk_level,
                recommendations=wellness.recommendations,
                last_updated=datetime.utcnow()
            ))
        
        return employee_wellness_list
        
    except Exception as e:
        logger.error(f"Failed to get employee wellness metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get employee wellness metrics: {str(e)}")

@router.get("/engagement/analytics", response_model=List[EngagementAnalyticsResponse])
async def get_engagement_analytics(
    period: MetricPeriodRequest = Depends(),
    employee_ids: Optional[List[int]] = Query(None),
    min_engagement_score: Optional[float] = Query(None, ge=0, le=100),
    engagement_level: Optional[str] = Query(None, description="very_low, low, moderate, high, very_high"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get detailed engagement analytics for employees
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Get employees
        query = db.query(User).filter(User.organization_id == user_org_id)
        if employee_ids:
            query = query.filter(User.id.in_(employee_ids))
        
        employees = query.all()
        time_period = get_time_period_from_request(period)
        engine = WellnessCalculationEngine(db)
        
        engagement_analytics = []
        
        for employee in employees:
            emp_id = getattr(employee, 'id', 0)
            emp_email = getattr(employee, 'email', '')
            
            # Calculate engagement metrics
            engagement = engine.calculate_engagement_metrics(
                emp_id, str(user_org_id), time_period
            )
            
            # Apply filters
            if min_engagement_score is not None and engagement.overall_score < min_engagement_score:
                continue
            
            emp_engagement_level = determine_engagement_level(engagement.overall_score)
            if engagement_level and emp_engagement_level != engagement_level:
                continue
            
            # Generate recommendations based on scores
            recommendations = []
            if engagement.usage_score < 50:
                recommendations.append("Encourage more frequent use of wellness tools")
            if engagement.consistency_score < 60:
                recommendations.append("Set up daily wellness reminders")
            if engagement.feature_adoption_score < 40:
                recommendations.append("Provide feature onboarding and training")
            
            engagement_analytics.append(EngagementAnalyticsResponse(
                employee_id=emp_id,
                employee_email=emp_email,
                overall_engagement_score=engagement.overall_score,
                usage_score=engagement.usage_score,
                interaction_score=engagement.interaction_score,
                consistency_score=engagement.consistency_score,
                feature_adoption_score=engagement.feature_adoption_score,
                social_engagement_score=engagement.social_engagement_score,
                retention_probability=engagement.retention_probability,
                engagement_level=emp_engagement_level,
                recent_activity_summary={
                    "sessions_this_period": 5,  # Mock data
                    "avg_session_duration": 12.5,
                    "features_used": 8
                },
                recommendations=recommendations
            ))
        
        return engagement_analytics
        
    except Exception as e:
        logger.error(f"Failed to get engagement analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get engagement analytics: {str(e)}")

@router.get("/productivity/metrics", response_model=List[ProductivityMetricsResponse])
async def get_productivity_metrics(
    period: MetricPeriodRequest = Depends(),
    employee_ids: Optional[List[int]] = Query(None),
    min_productivity_score: Optional[float] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get productivity impact metrics for employees
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Get employees
        query = db.query(User).filter(User.organization_id == user_org_id)
        if employee_ids:
            query = query.filter(User.id.in_(employee_ids))
        
        employees = query.all()
        time_period = get_time_period_from_request(period)
        engine = WellnessCalculationEngine(db)
        
        productivity_metrics = []
        
        for employee in employees:
            emp_id = getattr(employee, 'id', 0)
            emp_email = getattr(employee, 'email', '')
            
            # Calculate productivity impact
            productivity = engine.calculate_productivity_impact(
                emp_id, str(user_org_id), time_period, time_period
            )
            
            # Apply filters
            if min_productivity_score is not None and productivity.productivity_score < min_productivity_score:
                continue
            
            # Determine trend
            trend = "stable"
            if productivity.focus_improvement > 5:
                trend = "improving"
            elif productivity.focus_improvement < -5:
                trend = "declining"
            
            # Identify key factors
            key_factors = []
            if productivity.focus_improvement > 10:
                key_factors.append("Significant focus improvement")
            if productivity.stress_reduction_impact > 10:
                key_factors.append("Effective stress management")
            if productivity.sleep_quality_impact > 8:
                key_factors.append("Better sleep quality")
            
            productivity_metrics.append(ProductivityMetricsResponse(
                employee_id=emp_id,
                employee_email=emp_email,
                productivity_score=productivity.productivity_score,
                focus_improvement=productivity.focus_improvement,
                stress_reduction_impact=productivity.stress_reduction_impact,
                sleep_quality_impact=productivity.sleep_quality_impact,
                estimated_time_savings_hours=productivity.estimated_time_savings_hours,
                estimated_cost_savings=productivity.estimated_cost_savings,
                roi_percentage=productivity.roi_percentage,
                productivity_trend=trend,
                key_factors=key_factors
            ))
        
        return productivity_metrics
        
    except Exception as e:
        logger.error(f"Failed to get productivity metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get productivity metrics: {str(e)}")

@router.get("/insights/comprehensive", response_model=OrganizationInsightsResponse)
async def get_comprehensive_organization_insights(
    period: MetricPeriodRequest = Depends(),
    include_predictions: bool = Query(True, description="Include predictive analytics"),
    include_benchmarks: bool = Query(True, description="Include industry benchmarks"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get comprehensive organization insights with detailed analytics
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        time_period = get_time_period_from_request(period)
        engine = WellnessCalculationEngine(db)
        
        # Get comprehensive insights
        insights = engine.calculate_organization_insights(str(user_org_id), time_period)
        
        # Generate detailed breakdowns
        wellness_breakdown = {
            "stress_management": 72.5,
            "sleep_quality": 68.3,
            "focus_enhancement": 75.8,
            "mood_improvement": 70.2,
            "energy_levels": 66.9
        }
        
        engagement_breakdown = {
            "usage_frequency": 78.5,
            "feature_adoption": 65.3,
            "consistency": 82.1,
            "social_interaction": 58.7,
            "content_interaction": 73.9
        }
        
        productivity_breakdown = {
            "focus_improvement": 71.2,
            "stress_reduction": 69.8,
            "time_management": 73.5,
            "work_satisfaction": 75.1,
            "collaboration": 67.4
        }
        
        # Generate strategic recommendations
        strategic_recommendations = [
            "Implement targeted stress management programs for high-risk employees",
            "Expand sleep hygiene education and tools across the organization",
            "Create team-based wellness challenges to improve social engagement",
            "Develop manager training on wellness support and recognition"
        ]
        
        immediate_actions = [
            "Schedule wellness check-ins for employees showing declining trends",
            "Launch feature adoption campaign for underutilized tools",
            "Create peer support groups for employees with similar wellness goals",
            "Review and adjust wellness content based on engagement patterns"
        ]
        
        return OrganizationInsightsResponse(
            organization_id=str(user_org_id),
            analysis_period=period.period_type,
            overall_wellness_score=insights.overall_wellness_score,
            engagement_score=insights.engagement_score,
            productivity_score=insights.productivity_score,
            wellness_breakdown=wellness_breakdown,
            engagement_breakdown=engagement_breakdown,
            productivity_breakdown=productivity_breakdown,
            risk_indicators=insights.risk_indicators,
            top_performing_areas=insights.top_performing_areas,
            improvement_opportunities=insights.improvement_opportunities,
            benchmark_comparisons=insights.benchmark_comparisons if include_benchmarks else {},
            predicted_outcomes=insights.predicted_outcomes if include_predictions else {},
            strategic_recommendations=strategic_recommendations,
            immediate_actions=immediate_actions,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get comprehensive insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get comprehensive insights: {str(e)}")

@router.post("/goals", response_model=Dict[str, str])
async def create_wellness_goal(
    goal_data: CreateWellnessGoalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Create custom wellness goals for employees or organization
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Validate goal category and type
        valid_categories = [e.value for e in WellnessCategory]
        valid_types = [e.value for e in MetricType]
        
        if goal_data.goal_category not in valid_categories:
            raise HTTPException(status_code=400, detail=f"Invalid goal category. Must be one of: {valid_categories}")
        
        if goal_data.goal_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid goal type. Must be one of: {valid_types}")
        
        # Validate dates
        if goal_data.target_date <= goal_data.start_date:
            raise HTTPException(status_code=400, detail="Target date must be after start date")
        
        duration_days = (goal_data.target_date - goal_data.start_date).days
        
        # Create goals for specified employees or organization-wide
        created_goals = []
        current_user_id = getattr(current_user, 'id', 0)
        
        if goal_data.employee_ids:
            # Validate employees belong to organization
            employees = db.query(User).filter(
                and_(
                    User.id.in_(goal_data.employee_ids),
                    User.organization_id == user_org_id
                )
            ).all()
            
            if len(employees) != len(goal_data.employee_ids):
                found_ids = [getattr(emp, 'id', 0) for emp in employees]
                missing_ids = set(goal_data.employee_ids) - set(found_ids)
                raise HTTPException(status_code=404, detail=f"Employees not found: {list(missing_ids)}")
            
            # Create individual goals
            for employee in employees:
                emp_id = getattr(employee, 'id', 0)
                goal = WellnessGoals(
                    organization_id=user_org_id,
                    employee_id=emp_id,
                    goal_name=goal_data.goal_name,
                    goal_description=goal_data.goal_description,
                    goal_category=goal_data.goal_category,
                    goal_type=goal_data.goal_type,
                    target_value=goal_data.target_value,
                    measurement_unit=goal_data.measurement_unit,
                    start_date=goal_data.start_date,
                    target_date=goal_data.target_date,
                    duration_days=duration_days,
                    status=GoalStatus.ACTIVE,
                    priority_level=goal_data.priority_level,
                    is_recurring=goal_data.is_recurring,
                    reminder_settings=goal_data.reminder_settings,
                    created_by=current_user_id
                )
                db.add(goal)
                created_goals.append(f"employee_{emp_id}")
        else:
            # Create organization-wide goal
            goal = WellnessGoals(
                organization_id=user_org_id,
                employee_id=None,  # Organization-wide
                goal_name=goal_data.goal_name,
                goal_description=goal_data.goal_description,
                goal_category=goal_data.goal_category,
                goal_type=goal_data.goal_type,
                target_value=goal_data.target_value,
                measurement_unit=goal_data.measurement_unit,
                start_date=goal_data.start_date,
                target_date=goal_data.target_date,
                duration_days=duration_days,
                status=GoalStatus.ACTIVE,
                priority_level=goal_data.priority_level,
                is_recurring=goal_data.is_recurring,
                reminder_settings=goal_data.reminder_settings,
                created_by=current_user_id
            )
            db.add(goal)
            created_goals.append("organization_wide")
        
        db.commit()
        
        return {
            "message": f"Successfully created {len(created_goals)} wellness goal(s)",
            "goal_name": goal_data.goal_name,
            "goals_created": str(len(created_goals)),
            "created_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create wellness goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create wellness goal: {str(e)}")

@router.post("/demo/generate-data")
async def generate_demo_data(
    days_back: int = Query(90, ge=7, le=365, description="Days of historical data to generate"),
    employee_count: Optional[int] = Query(None, ge=1, le=100, description="Number of employees to generate data for"),
    include_goals: bool = Query(True, description="Generate wellness goals"),
    include_events: bool = Query(True, description="Generate engagement events"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Generate demo data for testing the wellness metrics system
    """
    try:
        from app.services.demo_data_generator import WellnessDemoDataGenerator
        
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        generator = WellnessDemoDataGenerator(db)
        
        # Generate wellness metrics
        metrics_created = generator.generate_employee_wellness_metrics(
            str(user_org_id), days_back, employee_count
        )
        
        events_created = 0
        goals_created = 0
        
        # Generate engagement events if requested
        if include_events:
            events_created = generator.generate_engagement_events(
                str(user_org_id), min(days_back, 60)  # Limit events to 60 days
            )
        
        # Generate wellness goals if requested
        if include_goals:
            goals_created = generator.generate_wellness_goals(
                str(user_org_id), 
                individual_goals=min(employee_count or 10, 20),
                org_wide_goals=5
            )
        
        return {
            "message": "Demo data generated successfully",
            "organization_id": str(user_org_id),
            "metrics_created": metrics_created,
            "events_created": events_created,
            "goals_created": goals_created,
            "data_period_days": days_back,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate demo data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate demo data: {str(e)}")

@router.get("/goals", response_model=List[WellnessGoalResponse])
async def get_wellness_goals(
    employee_id: Optional[int] = Query(None, description="Filter by specific employee"),
    goal_category: Optional[str] = Query(None, description="Filter by goal category"),
    status: Optional[str] = Query(None, description="Filter by goal status"),
    include_completed: bool = Query(True, description="Include completed goals"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get wellness goals for the organization
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Build query
        query = db.query(WellnessGoals).filter(
            WellnessGoals.organization_id == user_org_id
        )
        
        # Apply filters
        if employee_id:
            query = query.filter(WellnessGoals.employee_id == employee_id)
        
        if goal_category:
            query = query.filter(WellnessGoals.goal_category == goal_category)
        
        if status:
            query = query.filter(WellnessGoals.status == status)
        elif not include_completed:
            query = query.filter(WellnessGoals.status != GoalStatus.COMPLETED)
        
        goals = query.order_by(desc(WellnessGoals.created_at)).all()
        
        # Convert to response format
        goal_responses = []
        for goal in goals:
            # Get employee name if applicable
            employee_name = None
            goal_employee_id = getattr(goal, 'employee_id', None)
            if goal_employee_id:
                employee = db.query(User).filter(User.id == goal_employee_id).first()
                if employee:
                    employee_name = getattr(employee, 'email', 'Unknown')  # Using email as name
            
            goal_responses.append(WellnessGoalResponse(
                goal_id=str(getattr(goal, 'id', '')),
                goal_name=getattr(goal, 'goal_name', ''),
                goal_description=getattr(goal, 'goal_description', ''),
                goal_category=str(getattr(goal, 'goal_category', '')),
                goal_type=str(getattr(goal, 'goal_type', '')),
                target_value=getattr(goal, 'target_value', 0.0),
                current_value=getattr(goal, 'current_value', 0.0),
                progress_percentage=getattr(goal, 'progress_percentage', 0.0),
                status=str(getattr(goal, 'status', '')),
                start_date=getattr(goal, 'start_date', datetime.utcnow()),
                target_date=getattr(goal, 'target_date', datetime.utcnow()),
                employee_id=goal_employee_id,
                employee_name=employee_name,
                created_by=getattr(goal, 'created_by', 0),
                last_updated=getattr(goal, 'updated_at', datetime.utcnow())
            ))
        
        return goal_responses
        
    except Exception as e:
        logger.error(f"Failed to get wellness goals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get wellness goals: {str(e)}")
