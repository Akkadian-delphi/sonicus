"""
Wellness Impact Analytics Service

Advanced analytics engine for calculating real-time wellness impact,
trend analysis, engagement metrics, ROI calculations, and dashboard
data generation with interactive visualizations.

Created: July 27, 2025
Author: Sonicus Platform Team
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, text
import logging
import json
import statistics
from enum import Enum

# Models
from app.models.wellness_impact_tracking import (
    WellnessProgressBar,
    WellnessTrendChart,
    EngagementHeatmap,
    WellnessROICalculation,
    DashboardWidget,
    RealTimeMetric,
    TrendDirection,
    EngagementLevel,
    ROICategory,
    WidgetType
)
from app.models.user import User
from app.models.organization import Organization

logger = logging.getLogger(__name__)

class WellnessImpactAnalytics:
    """Advanced analytics engine for wellness impact tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =================== PROGRESS BAR ANALYTICS ===================
    
    def calculate_progress_bar_data(
        self, 
        organization_id: str, 
        metric_type: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate real-time progress bar data with trends"""
        
        try:
            # Get current metric value
            current_date = datetime.utcnow()
            start_date = current_date - timedelta(days=period_days)
            
            # Mock calculation for demonstration (replace with actual metric calculation)
            progress_data = self._calculate_wellness_progress(
                organization_id, metric_type, start_date, current_date
            )
            
            # Calculate trend
            trend_data = self._calculate_progress_trend(
                organization_id, metric_type, period_days
            )
            
            # Determine color scheme based on performance
            color_scheme = self._determine_progress_color(progress_data["progress_percentage"])
            
            return {
                "current_value": progress_data["current_value"],
                "target_value": progress_data["target_value"],
                "progress_percentage": progress_data["progress_percentage"],
                "trend": trend_data["trend_direction"],
                "trend_percentage": trend_data["trend_percentage"],
                "color_scheme": color_scheme,
                "last_updated": current_date.isoformat(),
                "historical_data": progress_data["historical_points"],
                "insights": self._generate_progress_insights(progress_data, trend_data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating progress bar data: {str(e)}")
            return self._get_default_progress_data()
    
    def _calculate_wellness_progress(
        self, 
        organization_id: str, 
        metric_type: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate wellness progress over time period"""
        
        # Mock data generation (replace with actual calculations)
        if metric_type == "stress_reduction":
            target_value = 100.0
            current_value = 78.5
            
            # Generate historical data points
            historical_points = []
            days_diff = (end_date - start_date).days
            
            for i in range(0, days_diff + 1, max(1, days_diff // 20)):  # Up to 20 data points
                date = start_date + timedelta(days=i)
                # Simulate gradual improvement with some variance
                base_progress = (i / days_diff) * 0.6 + 0.2  # 20% to 80% range
                variance = (hash(str(date)) % 100) / 1000  # Small random variance
                value = min(100, max(0, (base_progress + variance) * target_value))
                
                historical_points.append({
                    "date": date.isoformat(),
                    "value": round(value, 1)
                })
        
        elif metric_type == "engagement_score":
            target_value = 10.0
            current_value = 8.3
            
            historical_points = []
            days_diff = (end_date - start_date).days
            
            for i in range(0, days_diff + 1, max(1, days_diff // 20)):
                date = start_date + timedelta(days=i)
                base_progress = (i / days_diff) * 0.7 + 0.15
                variance = (hash(str(date)) % 100) / 2000
                value = min(10, max(0, (base_progress + variance) * target_value))
                
                historical_points.append({
                    "date": date.isoformat(),
                    "value": round(value, 1)
                })
        
        elif metric_type == "productivity_index":
            target_value = 120.0  # 120% of baseline
            current_value = 108.7
            
            historical_points = []
            days_diff = (end_date - start_date).days
            
            for i in range(0, days_diff + 1, max(1, days_diff // 20)):
                date = start_date + timedelta(days=i)
                base_progress = (i / days_diff) * 0.5 + 0.8  # 80% to 130% range
                variance = (hash(str(date)) % 100) / 1500
                value = max(70, min(130, (base_progress + variance) * 100))
                
                historical_points.append({
                    "date": date.isoformat(),
                    "value": round(value, 1)
                })
        
        else:
            # Default metrics
            target_value = 100.0
            current_value = 72.8
            historical_points = []
        
        progress_percentage = min(100, (current_value / target_value) * 100)
        
        return {
            "current_value": current_value,
            "target_value": target_value,
            "progress_percentage": round(progress_percentage, 1),
            "historical_points": historical_points
        }
    
    def _calculate_progress_trend(
        self, 
        organization_id: str, 
        metric_type: str, 
        period_days: int
    ) -> Dict[str, Any]:
        """Calculate trend direction and percentage change"""
        
        # Mock trend calculation
        current_date = datetime.utcnow()
        comparison_date = current_date - timedelta(days=period_days // 2)
        
        # Simulate trend calculation
        if metric_type in ["stress_reduction", "engagement_score", "productivity_index"]:
            trend_percentage = 12.5  # Positive trend
            trend_direction = TrendDirection.UP
        else:
            trend_percentage = -2.3  # Negative trend
            trend_direction = TrendDirection.DOWN
        
        return {
            "trend_direction": trend_direction.value,
            "trend_percentage": trend_percentage,
            "trend_strength": abs(trend_percentage) / 20.0,  # Normalize to 0-1
            "comparison_period_days": period_days // 2
        }
    
    def _determine_progress_color(self, progress_percentage: float) -> str:
        """Determine color scheme based on progress percentage"""
        if progress_percentage >= 90:
            return "green"
        elif progress_percentage >= 70:
            return "blue"
        elif progress_percentage >= 50:
            return "orange"
        else:
            return "red"
    
    def _generate_progress_insights(
        self, 
        progress_data: Dict[str, Any], 
        trend_data: Dict[str, Any]
    ) -> List[str]:
        """Generate insights based on progress and trend data"""
        
        insights = []
        progress_pct = progress_data["progress_percentage"]
        trend_pct = trend_data["trend_percentage"]
        
        # Progress insights
        if progress_pct >= 90:
            insights.append("Excellent progress! You're very close to your target.")
        elif progress_pct >= 70:
            insights.append("Good progress towards your wellness goals.")
        elif progress_pct >= 50:
            insights.append("Steady progress, but there's room for improvement.")
        else:
            insights.append("Consider reviewing your wellness strategy for better results.")
        
        # Trend insights
        if trend_pct > 10:
            insights.append("Strong positive trend - keep up the great work!")
        elif trend_pct > 5:
            insights.append("Positive trend showing gradual improvement.")
        elif trend_pct > -5:
            insights.append("Progress is stable with minor fluctuations.")
        else:
            insights.append("Declining trend - consider additional wellness interventions.")
        
        return insights
    
    def _get_default_progress_data(self) -> Dict[str, Any]:
        """Return default progress data in case of errors"""
        return {
            "current_value": 0.0,
            "target_value": 100.0,
            "progress_percentage": 0.0,
            "trend": TrendDirection.STABLE.value,
            "trend_percentage": 0.0,
            "color_scheme": "gray",
            "last_updated": datetime.utcnow().isoformat(),
            "historical_data": [],
            "insights": ["No data available for analysis."]
        }
    
    # =================== TREND CHART ANALYTICS ===================
    
    def generate_trend_chart_data(
        self,
        organization_id: str,
        metrics: List[str],
        time_range_days: int = 30,
        granularity: str = "daily"
    ) -> Dict[str, Any]:
        """Generate comprehensive trend chart data"""
        
        try:
            chart_data = {
                "datasets": [],
                "labels": [],
                "summary": {},
                "insights": []
            }
            
            # Generate time labels based on granularity
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=time_range_days)
            
            time_labels = self._generate_time_labels(start_date, end_date, granularity)
            chart_data["labels"] = time_labels
            
            # Generate data for each metric
            for metric in metrics:
                metric_data = self._generate_metric_trend_data(
                    organization_id, metric, start_date, end_date, granularity
                )
                chart_data["datasets"].append(metric_data)
            
            # Calculate summary statistics
            chart_data["summary"] = self._calculate_trend_summary(chart_data["datasets"])
            
            # Generate insights
            chart_data["insights"] = self._generate_trend_insights(chart_data["datasets"])
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating trend chart data: {str(e)}")
            return self._get_default_trend_data()
    
    def _generate_time_labels(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        granularity: str
    ) -> List[str]:
        """Generate time labels for chart x-axis"""
        
        labels = []
        current_date = start_date
        
        if granularity == "daily":
            delta = timedelta(days=1)
            date_format = "%m/%d"
        elif granularity == "weekly":
            delta = timedelta(weeks=1)
            date_format = "%m/%d"
        elif granularity == "monthly":
            delta = timedelta(days=30)
            date_format = "%m/%Y"
        else:
            delta = timedelta(days=1)
            date_format = "%m/%d"
        
        while current_date <= end_date:
            labels.append(current_date.strftime(date_format))
            current_date += delta
        
        return labels
    
    def _generate_metric_trend_data(
        self,
        organization_id: str,
        metric: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str
    ) -> Dict[str, Any]:
        """Generate trend data for a specific metric"""
        
        # Mock data generation based on metric type
        data_points = []
        current_date = start_date
        
        if granularity == "daily":
            delta = timedelta(days=1)
        elif granularity == "weekly":
            delta = timedelta(weeks=1)
        elif granularity == "monthly":
            delta = timedelta(days=30)
        else:
            delta = timedelta(days=1)
        
        # Generate realistic trend data based on metric type
        base_value = self._get_metric_base_value(metric)
        trend_factor = self._get_metric_trend_factor(metric)
        
        point_index = 0
        while current_date <= end_date:
            # Create realistic trending data
            trend_value = trend_factor * (point_index / 30)  # Gradual trend
            noise = (hash(str(current_date) + metric) % 100 - 50) / 500  # Random noise
            value = base_value + trend_value + noise
            
            # Ensure realistic bounds
            value = max(0, min(self._get_metric_max_value(metric), value))
            data_points.append(round(value, 1))
            
            current_date += delta
            point_index += 1
        
        return {
            "label": self._get_metric_display_name(metric),
            "data": data_points,
            "borderColor": self._get_metric_color(metric),
            "backgroundColor": self._get_metric_color(metric, alpha=0.1),
            "tension": 0.4,  # Smooth curves
            "fill": False,
            "pointRadius": 3,
            "pointHoverRadius": 5
        }
    
    def _get_metric_base_value(self, metric: str) -> float:
        """Get base value for metric type"""
        base_values = {
            "stress_level": 6.5,
            "engagement_score": 7.2,
            "productivity_index": 85.0,
            "wellness_score": 78.0,
            "satisfaction_rating": 8.1,
            "sleep_quality": 7.8,
            "exercise_frequency": 3.2,
            "mindfulness_minutes": 12.5
        }
        return base_values.get(metric, 50.0)
    
    def _get_metric_trend_factor(self, metric: str) -> float:
        """Get trend factor (positive = improving, negative = declining)"""
        trend_factors = {
            "stress_level": -0.8,  # Stress should decrease
            "engagement_score": 0.6,  # Engagement should increase
            "productivity_index": 4.2,  # Productivity should increase
            "wellness_score": 2.1,  # Wellness should increase
            "satisfaction_rating": 0.3,  # Satisfaction should increase
            "sleep_quality": 0.4,  # Sleep quality should increase
            "exercise_frequency": 0.8,  # Exercise should increase
            "mindfulness_minutes": 2.3  # Mindfulness should increase
        }
        return trend_factors.get(metric, 0.5)
    
    def _get_metric_max_value(self, metric: str) -> float:
        """Get maximum realistic value for metric type"""
        max_values = {
            "stress_level": 10.0,
            "engagement_score": 10.0,
            "productivity_index": 150.0,
            "wellness_score": 100.0,
            "satisfaction_rating": 10.0,
            "sleep_quality": 10.0,
            "exercise_frequency": 7.0,
            "mindfulness_minutes": 60.0
        }
        return max_values.get(metric, 100.0)
    
    def _get_metric_display_name(self, metric: str) -> str:
        """Get display name for metric"""
        display_names = {
            "stress_level": "Stress Level",
            "engagement_score": "Engagement Score",
            "productivity_index": "Productivity Index",
            "wellness_score": "Overall Wellness",
            "satisfaction_rating": "Job Satisfaction",
            "sleep_quality": "Sleep Quality",
            "exercise_frequency": "Exercise Frequency",
            "mindfulness_minutes": "Daily Mindfulness"
        }
        return display_names.get(metric, metric.replace("_", " ").title())
    
    def _get_metric_color(self, metric: str, alpha: float = 1.0) -> str:
        """Get color for metric visualization"""
        colors = {
            "stress_level": f"rgba(255, 99, 132, {alpha})",  # Red
            "engagement_score": f"rgba(54, 162, 235, {alpha})",  # Blue
            "productivity_index": f"rgba(75, 192, 192, {alpha})",  # Teal
            "wellness_score": f"rgba(153, 102, 255, {alpha})",  # Purple
            "satisfaction_rating": f"rgba(255, 159, 64, {alpha})",  # Orange
            "sleep_quality": f"rgba(199, 199, 199, {alpha})",  # Gray
            "exercise_frequency": f"rgba(83, 102, 255, {alpha})",  # Indigo
            "mindfulness_minutes": f"rgba(255, 99, 255, {alpha})"  # Magenta
        }
        return colors.get(metric, f"rgba(128, 128, 128, {alpha})")
    
    def _calculate_trend_summary(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for trend data"""
        
        summary = {
            "total_metrics": len(datasets),
            "improving_metrics": 0,
            "declining_metrics": 0,
            "stable_metrics": 0,
            "average_change_percentage": 0.0,
            "best_performing_metric": None,
            "worst_performing_metric": None
        }
        
        if not datasets:
            return summary
        
        metric_changes = []
        
        for dataset in datasets:
            data = dataset["data"]
            if len(data) < 2:
                continue
            
            # Calculate percentage change from first to last value
            first_value = data[0]
            last_value = data[-1]
            
            if first_value != 0:
                change_pct = ((last_value - first_value) / first_value) * 100
            else:
                change_pct = 0
            
            metric_changes.append({
                "metric": dataset["label"],
                "change_percentage": change_pct
            })
            
            # Categorize trend
            if change_pct > 5:
                summary["improving_metrics"] += 1
            elif change_pct < -5:
                summary["declining_metrics"] += 1
            else:
                summary["stable_metrics"] += 1
        
        # Calculate averages and extremes
        if metric_changes:
            summary["average_change_percentage"] = round(
                sum(m["change_percentage"] for m in metric_changes) / len(metric_changes), 1
            )
            
            best_metric = max(metric_changes, key=lambda x: x["change_percentage"])
            worst_metric = min(metric_changes, key=lambda x: x["change_percentage"])
            
            summary["best_performing_metric"] = {
                "name": best_metric["metric"],
                "change_percentage": round(best_metric["change_percentage"], 1)
            }
            
            summary["worst_performing_metric"] = {
                "name": worst_metric["metric"],
                "change_percentage": round(worst_metric["change_percentage"], 1)
            }
        
        return summary
    
    def _generate_trend_insights(self, datasets: List[Dict[str, Any]]) -> List[str]:
        """Generate insights based on trend analysis"""
        
        insights = []
        
        if not datasets:
            return ["No trend data available for analysis."]
        
        # Analyze overall trend patterns
        positive_trends = 0
        negative_trends = 0
        
        for dataset in datasets:
            data = dataset["data"]
            if len(data) < 2:
                continue
            
            # Simple trend analysis
            if data[-1] > data[0]:
                positive_trends += 1
            else:
                negative_trends += 1
        
        total_trends = positive_trends + negative_trends
        
        if total_trends == 0:
            insights.append("Insufficient data for trend analysis.")
        elif positive_trends > negative_trends:
            insights.append(f"Overall positive trend: {positive_trends}/{total_trends} metrics improving.")
        elif negative_trends > positive_trends:
            insights.append(f"Mixed results: {negative_trends}/{total_trends} metrics declining.")
        else:
            insights.append("Balanced trends with equal improvements and declines.")
        
        # Add specific insights
        if positive_trends >= 3:
            insights.append("Strong wellness program impact across multiple metrics.")
        
        if negative_trends >= 2:
            insights.append("Some metrics need attention - consider targeted interventions.")
        
        insights.append("Continue monitoring trends to identify patterns and opportunities.")
        
        return insights
    
    def _get_default_trend_data(self) -> Dict[str, Any]:
        """Return default trend data in case of errors"""
        return {
            "datasets": [],
            "labels": [],
            "summary": {
                "total_metrics": 0,
                "improving_metrics": 0,
                "declining_metrics": 0,
                "stable_metrics": 0,
                "average_change_percentage": 0.0
            },
            "insights": ["No trend data available."]
        }
    
    # =================== ENGAGEMENT HEATMAP ANALYTICS ===================
    
    def generate_engagement_heatmap_data(
        self,
        organization_id: str,
        heatmap_type: str = "department",
        time_period_days: int = 7
    ) -> Dict[str, Any]:
        """Generate engagement heatmap data"""
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=time_period_days)
            
            if heatmap_type == "department":
                return self._generate_department_heatmap(organization_id, start_date, end_date)
            elif heatmap_type == "time":
                return self._generate_time_heatmap(organization_id, start_date, end_date)
            elif heatmap_type == "activity":
                return self._generate_activity_heatmap(organization_id, start_date, end_date)
            else:
                return self._generate_department_heatmap(organization_id, start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error generating heatmap data: {str(e)}")
            return self._get_default_heatmap_data()
    
    def _generate_department_heatmap(
        self, 
        organization_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate department-based engagement heatmap"""
        
        # Mock department data
        departments = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations"]
        metrics = ["Engagement", "Wellness Usage", "Stress Level", "Productivity"]
        
        heatmap_data = []
        insights = []
        
        for dept_idx, department in enumerate(departments):
            for metric_idx, metric in enumerate(metrics):
                # Generate realistic engagement scores
                base_score = 70 + (hash(department + metric) % 30)  # 70-100 range
                
                # Add some variation based on department and metric
                if department == "Engineering" and metric == "Wellness Usage":
                    base_score += 10  # Engineers using wellness more
                elif department == "Sales" and metric == "Stress Level":
                    base_score -= 15  # Sales has higher stress (lower is better for stress)
                elif department == "HR" and metric == "Engagement":
                    base_score += 15  # HR typically more engaged
                
                # Normalize to 0-100 range
                score = max(0, min(100, base_score))
                
                heatmap_data.append({
                    "x": metric_idx,
                    "y": dept_idx,
                    "value": score,
                    "department": department,
                    "metric": metric,
                    "label": f"{department} - {metric}",
                    "intensity": score / 100.0
                })
        
        # Generate insights
        avg_engagement = statistics.mean([d["value"] for d in heatmap_data if "Engagement" in d["metric"]])
        if avg_engagement > 85:
            insights.append("Excellent engagement levels across all departments!")
        elif avg_engagement > 70:
            insights.append("Good engagement levels with room for improvement in some areas.")
        else:
            insights.append("Engagement levels need attention across multiple departments.")
        
        # Find best and worst performing departments
        dept_averages = {}
        for dept in departments:
            dept_scores = [d["value"] for d in heatmap_data if d["department"] == dept]
            dept_averages[dept] = statistics.mean(dept_scores)
        
        best_dept = max(dept_averages.items(), key=lambda x: x[1])
        worst_dept = min(dept_averages.items(), key=lambda x: x[1])
        
        insights.append(f"Best performing department: {best_dept[0]} ({best_dept[1]:.1f})")
        insights.append(f"Focus area: {worst_dept[0]} ({worst_dept[1]:.1f})")
        
        return {
            "data": heatmap_data,
            "x_labels": metrics,
            "y_labels": departments,
            "color_scheme": "RdYlGn",  # Red-Yellow-Green
            "min_value": min(d["value"] for d in heatmap_data),
            "max_value": max(d["value"] for d in heatmap_data),
            "average_value": statistics.mean(d["value"] for d in heatmap_data),
            "insights": insights,
            "heatmap_type": "department"
        }
    
    def _generate_time_heatmap(
        self, 
        organization_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate time-based engagement heatmap"""
        
        # Days of week and hours of day
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        hours = [f"{h:02d}:00" for h in range(24)]
        
        heatmap_data = []
        insights = []
        
        for day_idx, day in enumerate(days):
            for hour_idx, hour in enumerate(hours):
                # Generate realistic engagement based on time patterns
                base_engagement = 50
                
                # Work hours (9-17) have higher engagement
                hour_num = hour_idx
                if 9 <= hour_num <= 17:
                    base_engagement += 30
                elif 7 <= hour_num <= 9 or 17 <= hour_num <= 19:
                    base_engagement += 15  # Transition hours
                
                # Weekdays vs weekends
                if day_idx < 5:  # Weekdays
                    base_engagement += 20
                else:  # Weekends
                    base_engagement -= 10
                
                # Add some randomness
                variance = (hash(day + hour) % 20) - 10
                engagement = max(0, min(100, base_engagement + variance))
                
                heatmap_data.append({
                    "x": hour_idx,
                    "y": day_idx,
                    "value": engagement,
                    "day": day,
                    "hour": hour,
                    "label": f"{day} {hour}",
                    "intensity": engagement / 100.0
                })
        
        # Generate insights
        weekday_avg = statistics.mean([d["value"] for d in heatmap_data if d["y"] < 5])
        weekend_avg = statistics.mean([d["value"] for d in heatmap_data if d["y"] >= 5])
        
        insights.append(f"Weekday engagement: {weekday_avg:.1f}% vs Weekend: {weekend_avg:.1f}%")
        
        # Find peak engagement times
        peak_data = max(heatmap_data, key=lambda x: x["value"])
        insights.append(f"Peak engagement: {peak_data['day']} at {peak_data['hour']}")
        
        # Work hours analysis
        work_hours_data = [d for d in heatmap_data if 9 <= d["x"] <= 17 and d["y"] < 5]
        work_hours_avg = statistics.mean([d["value"] for d in work_hours_data])
        insights.append(f"Work hours engagement: {work_hours_avg:.1f}%")
        
        return {
            "data": heatmap_data,
            "x_labels": hours,
            "y_labels": days,
            "color_scheme": "Blues",
            "min_value": min(d["value"] for d in heatmap_data),
            "max_value": max(d["value"] for d in heatmap_data),
            "average_value": statistics.mean(d["value"] for d in heatmap_data),
            "insights": insights,
            "heatmap_type": "time"
        }
    
    def _generate_activity_heatmap(
        self, 
        organization_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate activity-based engagement heatmap"""
        
        activities = ["Meditation", "Breathing", "Sleep", "Exercise", "Mindfulness", "Stress Relief"]
        time_slots = ["Morning", "Midday", "Afternoon", "Evening", "Night"]
        
        heatmap_data = []
        insights = []
        
        for activity_idx, activity in enumerate(activities):
            for time_idx, time_slot in enumerate(time_slots):
                # Generate realistic usage patterns
                base_usage = 40
                
                # Activity-specific patterns
                if activity == "Meditation" and time_slot in ["Morning", "Evening"]:
                    base_usage += 25
                elif activity == "Exercise" and time_slot in ["Morning", "Afternoon"]:
                    base_usage += 20
                elif activity == "Sleep" and time_slot == "Night":
                    base_usage += 40
                elif activity == "Breathing" and time_slot == "Midday":
                    base_usage += 15  # Stress relief during lunch
                
                # Add variance
                variance = (hash(activity + time_slot) % 20) - 10
                usage = max(0, min(100, base_usage + variance))
                
                heatmap_data.append({
                    "x": time_idx,
                    "y": activity_idx,
                    "value": usage,
                    "activity": activity,
                    "time_slot": time_slot,
                    "label": f"{activity} - {time_slot}",
                    "intensity": usage / 100.0
                })
        
        # Generate insights
        most_popular = max(heatmap_data, key=lambda x: x["value"])
        insights.append(f"Most popular: {most_popular['activity']} in the {most_popular['time_slot']}")
        
        # Activity averages
        activity_averages = {}
        for activity in activities:
            activity_scores = [d["value"] for d in heatmap_data if d["activity"] == activity]
            activity_averages[activity] = statistics.mean(activity_scores)
        
        top_activity = max(activity_averages.items(), key=lambda x: x[1])
        insights.append(f"Most engaged activity: {top_activity[0]} ({top_activity[1]:.1f}%)")
        
        return {
            "data": heatmap_data,
            "x_labels": time_slots,
            "y_labels": activities,
            "color_scheme": "Viridis",
            "min_value": min(d["value"] for d in heatmap_data),
            "max_value": max(d["value"] for d in heatmap_data),
            "average_value": statistics.mean(d["value"] for d in heatmap_data),
            "insights": insights,
            "heatmap_type": "activity"
        }
    
    def _get_default_heatmap_data(self) -> Dict[str, Any]:
        """Return default heatmap data in case of errors"""
        return {
            "data": [],
            "x_labels": [],
            "y_labels": [],
            "color_scheme": "Blues",
            "min_value": 0,
            "max_value": 100,
            "average_value": 50,
            "insights": ["No heatmap data available."],
            "heatmap_type": "default"
        }
    
    # =================== ROI CALCULATION ANALYTICS ===================
    
    def calculate_wellness_roi(
        self,
        organization_id: str,
        roi_category: str = "overall",
        calculation_period_months: int = 12
    ) -> Dict[str, Any]:
        """Calculate comprehensive wellness program ROI"""
        
        try:
            # Mock ROI calculation (replace with actual data)
            roi_data = self._perform_roi_calculation(
                organization_id, roi_category, calculation_period_months
            )
            
            # Add confidence intervals and validation
            roi_data["confidence_interval"] = self._calculate_roi_confidence_interval(roi_data)
            roi_data["validation_metrics"] = self._validate_roi_calculation(roi_data)
            roi_data["recommendations"] = self._generate_roi_recommendations(roi_data)
            
            return roi_data
            
        except Exception as e:
            logger.error(f"Error calculating wellness ROI: {str(e)}")
            return self._get_default_roi_data()
    
    def _perform_roi_calculation(
        self,
        organization_id: str,
        roi_category: str,
        period_months: int
    ) -> Dict[str, Any]:
        """Perform detailed ROI calculation"""
        
        # Mock financial data (replace with actual organization data)
        program_investment = 50000.0  # Annual wellness program cost
        
        # Calculate different ROI components
        productivity_roi = self._calculate_productivity_roi(organization_id, period_months)
        healthcare_roi = self._calculate_healthcare_roi(organization_id, period_months)
        absenteeism_roi = self._calculate_absenteeism_roi(organization_id, period_months)
        turnover_roi = self._calculate_turnover_roi(organization_id, period_months)
        engagement_roi = self._calculate_engagement_roi(organization_id, period_months)
        
        # Calculate total benefits
        total_benefits = (
            productivity_roi["savings"] +
            healthcare_roi["savings"] +
            absenteeism_roi["savings"] +
            turnover_roi["savings"] +
            engagement_roi["savings"]
        )
        
        # Calculate ROI metrics
        net_benefits = total_benefits - program_investment
        roi_percentage = (net_benefits / program_investment) * 100 if program_investment > 0 else 0
        payback_period_months = (program_investment / (total_benefits / 12)) if total_benefits > 0 else float('inf')
        
        return {
            "roi_category": roi_category,
            "calculation_period_months": period_months,
            "program_investment": program_investment,
            "total_benefits": total_benefits,
            "net_benefits": net_benefits,
            "roi_percentage": round(roi_percentage, 1),
            "payback_period_months": round(payback_period_months, 1),
            "break_even_point": self._calculate_break_even_date(payback_period_months),
            "components": {
                "productivity": productivity_roi,
                "healthcare": healthcare_roi,
                "absenteeism": absenteeism_roi,
                "turnover": turnover_roi,
                "engagement": engagement_roi
            },
            "confidence_level": 0.8,
            "data_quality_score": 0.85
        }
    
    def _calculate_productivity_roi(self, organization_id: str, period_months: int) -> Dict[str, Any]:
        """Calculate productivity-related ROI"""
        
        # Mock productivity metrics
        baseline_productivity = 85.0  # Baseline productivity score
        current_productivity = 92.5   # Current productivity score
        improvement_percentage = ((current_productivity - baseline_productivity) / baseline_productivity) * 100
        
        # Estimate financial impact
        average_salary = 65000  # Average employee salary
        employee_count = 50     # Number of employees
        
        annual_productivity_value = average_salary * employee_count
        productivity_savings = annual_productivity_value * (improvement_percentage / 100) * (period_months / 12)
        
        return {
            "baseline_score": baseline_productivity,
            "current_score": current_productivity,
            "improvement_percentage": round(improvement_percentage, 1),
            "savings": round(productivity_savings, 2),
            "methodology": "Productivity score improvement applied to total compensation"
        }
    
    def _calculate_healthcare_roi(self, organization_id: str, period_months: int) -> Dict[str, Any]:
        """Calculate healthcare cost reduction ROI"""
        
        # Mock healthcare data
        baseline_healthcare_cost = 8500   # Per employee per year
        current_healthcare_cost = 7650    # Per employee per year
        employee_count = 50
        
        annual_savings_per_employee = baseline_healthcare_cost - current_healthcare_cost
        total_healthcare_savings = annual_savings_per_employee * employee_count * (period_months / 12)
        
        return {
            "baseline_cost_per_employee": baseline_healthcare_cost,
            "current_cost_per_employee": current_healthcare_cost,
            "savings_per_employee": annual_savings_per_employee,
            "savings": round(total_healthcare_savings, 2),
            "methodology": "Reduction in health insurance claims and medical expenses"
        }
    
    def _calculate_absenteeism_roi(self, organization_id: str, period_months: int) -> Dict[str, Any]:
        """Calculate absenteeism reduction ROI"""
        
        # Mock absenteeism data
        baseline_sick_days = 8.5     # Days per employee per year
        current_sick_days = 6.2      # Days per employee per year
        employee_count = 50
        daily_cost_per_employee = 250  # Average daily compensation
        
        days_saved_per_employee = baseline_sick_days - current_sick_days
        total_absenteeism_savings = (
            days_saved_per_employee * employee_count * daily_cost_per_employee * (period_months / 12)
        )
        
        return {
            "baseline_sick_days": baseline_sick_days,
            "current_sick_days": current_sick_days,
            "days_saved_per_employee": round(days_saved_per_employee, 1),
            "savings": round(total_absenteeism_savings, 2),
            "methodology": "Reduction in sick days multiplied by daily compensation"
        }
    
    def _calculate_turnover_roi(self, organization_id: str, period_months: int) -> Dict[str, Any]:
        """Calculate turnover reduction ROI"""
        
        # Mock turnover data
        baseline_turnover_rate = 0.18    # 18% annual turnover
        current_turnover_rate = 0.12     # 12% annual turnover
        employee_count = 50
        replacement_cost_per_employee = 15000  # Cost to replace an employee
        
        turnover_reduction = baseline_turnover_rate - current_turnover_rate
        employees_retained = turnover_reduction * employee_count
        total_turnover_savings = employees_retained * replacement_cost_per_employee * (period_months / 12)
        
        return {
            "baseline_turnover_rate": baseline_turnover_rate,
            "current_turnover_rate": current_turnover_rate,
            "employees_retained": round(employees_retained, 1),
            "savings": round(total_turnover_savings, 2),
            "methodology": "Turnover reduction multiplied by replacement costs"
        }
    
    def _calculate_engagement_roi(self, organization_id: str, period_months: int) -> Dict[str, Any]:
        """Calculate engagement improvement ROI"""
        
        # Mock engagement data
        baseline_engagement = 6.8       # Out of 10
        current_engagement = 8.1        # Out of 10
        employee_count = 50
        average_salary = 65000
        engagement_multiplier = 0.12    # 12% productivity increase per engagement point
        
        engagement_improvement = current_engagement - baseline_engagement
        productivity_multiplier = engagement_improvement * engagement_multiplier
        engagement_savings = (
            average_salary * employee_count * productivity_multiplier * (period_months / 12)
        )
        
        return {
            "baseline_engagement": baseline_engagement,
            "current_engagement": current_engagement,
            "improvement_points": round(engagement_improvement, 1),
            "savings": round(engagement_savings, 2),
            "methodology": "Engagement improvement linked to productivity gains"
        }
    
    def _calculate_break_even_date(self, payback_period_months: float) -> str:
        """Calculate break-even date"""
        
        if payback_period_months == float('inf'):
            return "Never"
        
        break_even_date = datetime.utcnow() + timedelta(days=payback_period_months * 30)
        return break_even_date.strftime("%Y-%m-%d")
    
    def _calculate_roi_confidence_interval(self, roi_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence interval for ROI estimate"""
        
        roi_percentage = roi_data["roi_percentage"]
        confidence_level = roi_data["confidence_level"]
        
        # Mock confidence interval calculation
        margin_of_error = roi_percentage * 0.15  # 15% margin of error
        
        return {
            "lower_bound": round(roi_percentage - margin_of_error, 1),
            "upper_bound": round(roi_percentage + margin_of_error, 1),
            "confidence_level": confidence_level
        }
    
    def _validate_roi_calculation(self, roi_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ROI calculation quality"""
        
        validation_score = 0.0
        validation_issues = []
        validation_strengths = []
        
        # Check data quality
        if roi_data["data_quality_score"] >= 0.8:
            validation_score += 0.3
            validation_strengths.append("High data quality")
        else:
            validation_issues.append("Data quality could be improved")
        
        # Check ROI reasonableness
        roi_pct = roi_data["roi_percentage"]
        if 50 <= roi_pct <= 300:  # Reasonable ROI range
            validation_score += 0.3
            validation_strengths.append("ROI in reasonable range")
        elif roi_pct > 300:
            validation_issues.append("ROI seems unusually high - verify calculations")
        else:
            validation_issues.append("ROI below expected range - investigate factors")
        
        # Check payback period
        payback = roi_data["payback_period_months"]
        if payback <= 24:  # 2 years or less
            validation_score += 0.2
            validation_strengths.append("Reasonable payback period")
        else:
            validation_issues.append("Long payback period - consider program optimization")
        
        # Check component balance
        components = roi_data["components"]
        total_savings = sum(comp["savings"] for comp in components.values())
        if total_savings > 0:
            validation_score += 0.2
            validation_strengths.append("Positive savings across components")
        
        return {
            "validation_score": round(validation_score, 2),
            "validation_issues": validation_issues,
            "validation_strengths": validation_strengths,
            "overall_quality": "High" if validation_score >= 0.8 else "Medium" if validation_score >= 0.6 else "Low"
        }
    
    def _generate_roi_recommendations(self, roi_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on ROI analysis"""
        
        recommendations = []
        roi_pct = roi_data["roi_percentage"]
        payback = roi_data["payback_period_months"]
        
        # ROI-based recommendations
        if roi_pct > 200:
            recommendations.append("Excellent ROI! Consider expanding the wellness program.")
        elif roi_pct > 100:
            recommendations.append("Strong ROI indicates program effectiveness.")
        elif roi_pct > 50:
            recommendations.append("Positive ROI with room for optimization.")
        else:
            recommendations.append("ROI below expectations - review program effectiveness.")
        
        # Payback period recommendations
        if payback <= 12:
            recommendations.append("Quick payback period supports continued investment.")
        elif payback <= 24:
            recommendations.append("Reasonable payback period justifies program costs.")
        else:
            recommendations.append("Consider program modifications to improve payback period.")
        
        # Component-specific recommendations
        components = roi_data["components"]
        
        # Find highest impact component
        highest_component = max(components.items(), key=lambda x: x[1]["savings"])
        recommendations.append(f"Focus on {highest_component[0]} - highest ROI component.")
        
        # Find improvement opportunities
        lowest_component = min(components.items(), key=lambda x: x[1]["savings"])
        recommendations.append(f"Opportunity: Improve {lowest_component[0]} impact.")
        
        return recommendations
    
    def _get_default_roi_data(self) -> Dict[str, Any]:
        """Return default ROI data in case of errors"""
        return {
            "roi_category": "overall",
            "calculation_period_months": 12,
            "program_investment": 0.0,
            "total_benefits": 0.0,
            "net_benefits": 0.0,
            "roi_percentage": 0.0,
            "payback_period_months": float('inf'),
            "break_even_point": "Never",
            "components": {},
            "confidence_level": 0.0,
            "data_quality_score": 0.0,
            "confidence_interval": {"lower_bound": 0.0, "upper_bound": 0.0, "confidence_level": 0.0},
            "validation_metrics": {"validation_score": 0.0, "overall_quality": "Low"},
            "recommendations": ["No ROI data available for analysis."]
        }
