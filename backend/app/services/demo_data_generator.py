"""
Demo Data Generator for Wellness Metrics

Service to generate realistic sample data for testing and demonstration
of the wellness metrics system. Creates mock employee wellness data,
engagement events, and productivity metrics.

Created: July 27, 2025
Author: Sonicus Platform Team
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import uuid

# Import models
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.wellness_metrics import (
    OrganizationMetrics, EmployeeWellnessMetrics, WellnessGoals, 
    GoalProgressLog, EngagementEvents, WellnessAlgorithmConfig,
    MetricType, MeasurementPeriod, GoalStatus, EngagementLevel, WellnessCategory
)

import logging
logger = logging.getLogger(__name__)

class WellnessDemoDataGenerator:
    """Generate realistic demo data for wellness metrics system"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def generate_employee_wellness_metrics(
        self, 
        organization_id: str, 
        days_back: int = 90,
        employee_count: Optional[int] = None
    ) -> int:
        """
        Generate employee wellness metrics for testing
        """
        try:
            # Get employees from organization
            employees = self.db.query(User).filter(
                User.organization_id == organization_id
            ).all()
            
            if not employees:
                logger.warning(f"No employees found for organization {organization_id}")
                return 0
            
            if employee_count:
                employees = employees[:employee_count]
            
            metrics_created = 0
            base_date = datetime.utcnow()
            
            for employee in employees:
                emp_id = getattr(employee, 'id', 0)
                
                # Generate wellness data with realistic trends
                base_wellness_profile = self._generate_employee_profile()
                
                # Create daily metrics for the period
                for day_offset in range(days_back):
                    measurement_date = base_date - timedelta(days=day_offset)
                    
                    # Add some realistic variation over time
                    daily_variation = self._calculate_daily_variation(
                        day_offset, days_back, base_wellness_profile
                    )
                    
                    # Create wellness metrics record
                    wellness_metrics = EmployeeWellnessMetrics(
                        organization_id=organization_id,
                        employee_id=emp_id,
                        measurement_date=measurement_date,
                        measurement_period="daily",
                        
                        # Core wellness scores (with variation)
                        stress_level_score=max(0, min(100, 
                            base_wellness_profile["stress_baseline"] + daily_variation["stress"]
                        )),
                        sleep_quality_score=max(0, min(100,
                            base_wellness_profile["sleep_baseline"] + daily_variation["sleep"]
                        )),
                        focus_level_score=max(0, min(100,
                            base_wellness_profile["focus_baseline"] + daily_variation["focus"]
                        )),
                        mood_score=max(0, min(100,
                            base_wellness_profile["mood_baseline"] + daily_variation["mood"]
                        )),
                        energy_level_score=max(0, min(100,
                            base_wellness_profile["energy_baseline"] + daily_variation["energy"]
                        )),
                        anxiety_level_score=max(0, min(100,
                            base_wellness_profile["anxiety_baseline"] + daily_variation["anxiety"]
                        )),
                        
                        # Engagement metrics
                        app_engagement_score=random.uniform(40, 95),
                        content_interaction_score=random.uniform(30, 85),
                        feature_usage_score=random.uniform(25, 80),
                        consistency_score=random.uniform(45, 90),
                        
                        # Productivity metrics
                        work_performance_score=random.uniform(50, 90),
                        task_completion_score=random.uniform(60, 95),
                        collaboration_score=random.uniform(55, 85),
                        innovation_score=random.uniform(40, 80),
                        
                        # Usage patterns
                        total_sessions=random.randint(0, 8),
                        total_minutes_listened=random.uniform(0, 120),
                        avg_session_duration=random.uniform(5, 25),
                        
                        # Self-reported metrics (1-10 scale)
                        self_reported_stress=random.randint(2, 9),
                        self_reported_sleep_quality=random.randint(3, 9),
                        self_reported_focus=random.randint(4, 9),
                        self_reported_mood=random.randint(3, 9),
                        self_reported_productivity=random.randint(4, 9),
                        
                        # Behavioral indicators
                        login_frequency=random.randint(0, 5),
                        feature_adoption_count=random.randint(2, 12),
                        goal_completion_rate=random.uniform(0, 100),
                        streak_days=random.randint(0, min(30, day_offset + 1)),
                        
                        # Risk indicators
                        burnout_risk_score=random.uniform(10, 80),
                        disengagement_risk_score=random.uniform(5, 70),
                        wellness_decline_trend=(random.random() < 0.15),  # 15% chance
                        
                        # Metadata
                        data_quality_score=random.uniform(0.7, 1.0),
                        metrics_version="1.0"
                    )
                    
                    self.db.add(wellness_metrics)
                    metrics_created += 1
            
            self.db.commit()
            logger.info(f"Created {metrics_created} wellness metrics records")
            return metrics_created
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to generate wellness metrics: {str(e)}")
            return 0
    
    def generate_engagement_events(
        self,
        organization_id: str,
        days_back: int = 30,
        events_per_day_range: tuple = (5, 25)
    ) -> int:
        """
        Generate realistic engagement events for testing
        """
        try:
            # Get employees
            employees = self.db.query(User).filter(
                User.organization_id == organization_id
            ).all()
            
            if not employees:
                return 0
            
            events_created = 0
            base_date = datetime.utcnow()
            
            # Event types and their weights
            event_types = {
                "session_start": 0.20,
                "session_complete": 0.18,
                "feature_interaction": 0.15,
                "content_play": 0.12,
                "goal_progress": 0.10,
                "social_interaction": 0.08,
                "achievement_unlock": 0.05,
                "feedback_submit": 0.04,
                "settings_update": 0.03,
                "content_favorite": 0.03,
                "share_content": 0.02
            }
            
            event_categories = {
                "session_start": "usage",
                "session_complete": "usage",
                "feature_interaction": "interaction",
                "content_play": "content",
                "goal_progress": "achievement",
                "social_interaction": "social",
                "achievement_unlock": "achievement",
                "feedback_submit": "interaction",
                "settings_update": "usage",
                "content_favorite": "content",
                "share_content": "social"
            }
            
            for day_offset in range(days_back):
                event_date = base_date - timedelta(days=day_offset)
                events_today = random.randint(*events_per_day_range)
                
                for _ in range(events_today):
                    # Select random employee
                    employee = random.choice(employees)
                    emp_id = getattr(employee, 'id', 0)
                    
                    # Select event type based on weights
                    event_type = self._weighted_choice(event_types)
                    event_category = event_categories[event_type]
                    
                    # Generate event time within the day
                    event_time = event_date.replace(
                        hour=random.randint(7, 22),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )
                    
                    # Create engagement event
                    event = EngagementEvents(
                        organization_id=organization_id,
                        employee_id=emp_id,
                        event_type=event_type,
                        event_category=event_category,
                        event_description=self._generate_event_description(event_type),
                        event_value=random.uniform(1, 100) if random.random() > 0.5 else None,
                        event_metadata=self._generate_event_metadata(event_type),
                        session_id=f"session_{random.randint(1000, 9999)}",
                        content_id=f"content_{random.randint(100, 999)}" if "content" in event_type else None,
                        feature_name=self._get_random_feature_name() if "feature" in event_type else None,
                        engagement_weight=random.uniform(0.5, 2.0),
                        quality_score=random.uniform(0.6, 1.0),
                        device_type=random.choice(["mobile", "desktop", "tablet"]),
                        platform=random.choice(["ios", "android", "web"]),
                        event_timestamp=event_time
                    )
                    
                    self.db.add(event)
                    events_created += 1
            
            self.db.commit()
            logger.info(f"Created {events_created} engagement events")
            return events_created
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to generate engagement events: {str(e)}")
            return 0
    
    def generate_wellness_goals(
        self,
        organization_id: str,
        individual_goals: int = 20,
        org_wide_goals: int = 5
    ) -> int:
        """
        Generate sample wellness goals for testing
        """
        try:
            # Get employees and current user (admin)
            employees = self.db.query(User).filter(
                User.organization_id == organization_id
            ).all()
            
            admin_user = self.db.query(User).filter(
                User.organization_id == organization_id,
                User.role == UserRole.BUSINESS_ADMIN
            ).first()
            
            if not admin_user:
                admin_user = employees[0] if employees else None
            
            if not admin_user:
                return 0
            
            admin_id = getattr(admin_user, 'id', 0)
            goals_created = 0
            
            # Goal templates
            goal_templates = [
                {
                    "name": "Reduce Daily Stress Levels",
                    "category": WellnessCategory.STRESS_MANAGEMENT,
                    "type": MetricType.STRESS_REDUCTION,
                    "target": 80.0,
                    "unit": "score",
                    "duration_days": 30
                },
                {
                    "name": "Improve Sleep Quality",
                    "category": WellnessCategory.SLEEP_QUALITY,
                    "type": MetricType.SLEEP_IMPROVEMENT,
                    "target": 75.0,
                    "unit": "score",
                    "duration_days": 45
                },
                {
                    "name": "Enhance Daily Focus",
                    "category": WellnessCategory.MENTAL_HEALTH,
                    "type": MetricType.FOCUS_ENHANCEMENT,
                    "target": 85.0,
                    "unit": "score",
                    "duration_days": 21
                },
                {
                    "name": "Increase Energy Levels",
                    "category": WellnessCategory.PHYSICAL_WELLNESS,
                    "type": MetricType.ENERGY_LEVEL,
                    "target": 70.0,
                    "unit": "score",
                    "duration_days": 28
                },
                {
                    "name": "Complete 100 Meditation Sessions",
                    "category": WellnessCategory.MENTAL_HEALTH,
                    "type": MetricType.ENGAGEMENT,
                    "target": 100.0,
                    "unit": "sessions",
                    "duration_days": 90
                }
            ]
            
            # Create individual goals
            for _ in range(individual_goals):
                if not employees:
                    break
                
                employee = random.choice(employees)
                template = random.choice(goal_templates)
                
                start_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
                target_date = start_date + timedelta(days=template["duration_days"])
                
                goal = WellnessGoals(
                    organization_id=organization_id,
                    employee_id=getattr(employee, 'id', 0),
                    goal_name=template["name"],
                    goal_description=f"Personal wellness goal: {template['name']}",
                    goal_category=template["category"].value,
                    goal_type=template["type"].value,
                    target_value=template["target"],
                    current_value=random.uniform(0, template["target"] * 0.7),
                    measurement_unit=template["unit"],
                    start_date=start_date,
                    target_date=target_date,
                    duration_days=template["duration_days"],
                    status=random.choice([GoalStatus.ACTIVE, GoalStatus.ACTIVE, GoalStatus.COMPLETED]),
                    progress_percentage=random.uniform(10, 90),
                    priority_level=random.choice(["low", "medium", "high"]),
                    is_recurring=random.random() < 0.3,
                    created_by=admin_id
                )
                
                self.db.add(goal)
                goals_created += 1
            
            # Create organization-wide goals
            for _ in range(org_wide_goals):
                template = random.choice(goal_templates)
                
                start_date = datetime.utcnow() - timedelta(days=random.randint(0, 14))
                target_date = start_date + timedelta(days=template["duration_days"])
                
                goal = WellnessGoals(
                    organization_id=organization_id,
                    employee_id=None,  # Organization-wide
                    goal_name=f"Organization Goal: {template['name']}",
                    goal_description=f"Company-wide initiative to {template['name'].lower()}",
                    goal_category=template["category"].value,
                    goal_type=template["type"].value,
                    target_value=template["target"],
                    current_value=random.uniform(0, template["target"] * 0.5),
                    measurement_unit=template["unit"],
                    start_date=start_date,
                    target_date=target_date,
                    duration_days=template["duration_days"],
                    status=GoalStatus.ACTIVE,
                    progress_percentage=random.uniform(20, 70),
                    priority_level="high",
                    is_recurring=False,
                    created_by=admin_id
                )
                
                self.db.add(goal)
                goals_created += 1
            
            self.db.commit()
            logger.info(f"Created {goals_created} wellness goals")
            return goals_created
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to generate wellness goals: {str(e)}")
            return 0
    
    # =================== HELPER METHODS ===================
    
    def _generate_employee_profile(self) -> Dict[str, float]:
        """Generate a realistic baseline wellness profile for an employee"""
        # Create correlated baseline scores (some people are generally more/less well)
        base_wellness = random.uniform(40, 85)
        variation = random.uniform(5, 15)
        
        return {
            "stress_baseline": max(20, min(90, base_wellness + random.uniform(-variation, variation))),
            "sleep_baseline": max(30, min(95, base_wellness + random.uniform(-variation, variation))),
            "focus_baseline": max(25, min(90, base_wellness + random.uniform(-variation, variation))),
            "mood_baseline": max(30, min(95, base_wellness + random.uniform(-variation, variation))),
            "energy_baseline": max(20, min(90, base_wellness + random.uniform(-variation, variation))),
            "anxiety_baseline": max(10, min(80, 100 - base_wellness + random.uniform(-variation, variation))),
        }
    
    def _calculate_daily_variation(
        self, 
        day_offset: int, 
        total_days: int, 
        profile: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate realistic daily variation in wellness scores"""
        # Weekly patterns (weekends often different)
        day_of_week = day_offset % 7
        weekend_effect = 5 if day_of_week in [5, 6] else 0  # Saturday, Sunday
        
        # Seasonal/long-term trends
        progress_factor = (total_days - day_offset) / total_days  # Improvement over time
        seasonal_boost = progress_factor * 10  # Gradual improvement
        
        # Random daily variation
        daily_noise = random.uniform(-8, 8)
        
        base_variation = weekend_effect + seasonal_boost + daily_noise
        
        return {
            "stress": base_variation + random.uniform(-3, 3),
            "sleep": base_variation + random.uniform(-4, 4),
            "focus": base_variation + random.uniform(-5, 5),
            "mood": base_variation + random.uniform(-4, 4),
            "energy": base_variation + random.uniform(-3, 3),
            "anxiety": -base_variation + random.uniform(-3, 3)  # Inverse relationship
        }
    
    def _weighted_choice(self, choices: Dict[str, float]) -> str:
        """Select a random choice based on weights"""
        total = sum(choices.values())
        r = random.uniform(0, total)
        upto = 0
        for choice, weight in choices.items():
            if upto + weight >= r:
                return choice
            upto += weight
        return list(choices.keys())[-1]  # Fallback
    
    def _generate_event_description(self, event_type: str) -> str:
        """Generate descriptive text for event types"""
        descriptions = {
            "session_start": "User started a wellness session",
            "session_complete": "User completed a wellness session",
            "feature_interaction": "User interacted with a platform feature",
            "content_play": "User played wellness content",
            "goal_progress": "User made progress toward a wellness goal",
            "social_interaction": "User engaged with team wellness features",
            "achievement_unlock": "User unlocked a wellness achievement",
            "feedback_submit": "User provided feedback on content",
            "settings_update": "User updated their preferences",
            "content_favorite": "User favorited wellness content",
            "share_content": "User shared content with colleagues"
        }
        return descriptions.get(event_type, "User performed an action")
    
    def _generate_event_metadata(self, event_type: str) -> Dict[str, Any]:
        """Generate relevant metadata for event types"""
        base_metadata = {
            "user_agent": "Sonicus Mobile App 2.1.0",
            "location": random.choice(["office", "home", "commute", "other"]),
            "time_of_day": random.choice(["morning", "afternoon", "evening", "night"])
        }
        
        if "session" in event_type:
            session_metadata = {
                "session_duration": random.randint(300, 1800),  # 5-30 minutes
                "content_type": random.choice(["meditation", "breathing", "nature_sounds", "music"])
            }
            base_metadata = {**base_metadata, **session_metadata}
        elif "content" in event_type:
            content_metadata = {
                "content_category": random.choice(["stress_relief", "focus", "sleep", "energy"]),
                "content_duration": random.randint(60, 3600)
            }
            base_metadata = {**base_metadata, **content_metadata}
        
        return base_metadata
    
    def _get_random_feature_name(self) -> str:
        """Get a random feature name for feature interaction events"""
        features = [
            "breathing_exercises", "meditation_timer", "progress_tracker",
            "goal_setting", "mood_journal", "sleep_tracker", "focus_mode",
            "team_challenges", "achievement_center", "wellness_dashboard",
            "content_library", "personalized_recommendations"
        ]
        return random.choice(features)
