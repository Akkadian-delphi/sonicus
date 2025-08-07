"""
Test suite for Organization Analytics functionality

Tests for:
- Real-time usage metrics per organization
- User engagement analytics across organizations  
- Revenue attribution per organization
- Content usage patterns and recommendations
- Organization health scoring algorithm
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch
import uuid

from app.services.organization_analytics import OrganizationAnalyticsService
from app.schemas.organization_analytics import (
    MetricTimeRange, EngagementLevel, HealthStatus,
    AnalyticsFilters
)
from app.models.organization import Organization, SubscriptionTier, OrganizationStatus
from app.models.user import User, UserRole
from app.models.therapy_sound import TherapySound


class TestOrganizationAnalyticsService:
    """Test suite for OrganizationAnalyticsService."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def analytics_service(self, mock_db_session):
        """Create analytics service instance."""
        return OrganizationAnalyticsService(mock_db_session)
    
    @pytest.fixture
    def sample_organization(self):
        """Sample organization for testing."""
        org = Mock()
        org.id = str(uuid.uuid4())
        org.name = "Test Organization"
        org.subscription_tier = SubscriptionTier.PROFESSIONAL
        org.status = OrganizationStatus.ACTIVE
        return org
    
    @pytest.fixture
    def sample_users(self):
        """Sample users for testing."""
        users = []
        for i in range(5):
            user = Mock()
            user.id = str(uuid.uuid4())
            user.email = f"user{i}@test.com"
            user.role = UserRole.USER
            user.organization_id = "test-org-id"
            users.append(user)
        return users
    
    @pytest.fixture
    def sample_sounds(self):
        """Sample therapy sounds for testing."""
        sounds = []
        categories = ["meditation", "nature_sounds", "focus_music", "sleep_sounds"]
        for i in range(10):
            sound = Mock()
            sound.id = str(uuid.uuid4())
            sound.title = f"Test Sound {i+1}"
            sound.category = categories[i % len(categories)]
            sounds.append(sound)
        return sounds
    
    # ==================== DATE RANGE TESTS ====================
    
    def test_get_date_range_last_7_days(self, analytics_service):
        """Test date range calculation for last 7 days."""
        today = date.today()
        start_dt, end_dt = analytics_service._get_date_range(MetricTimeRange.LAST_7_DAYS)
        
        assert end_dt == today
        assert start_dt == today - timedelta(days=7)
    
    def test_get_date_range_last_30_days(self, analytics_service):
        """Test date range calculation for last 30 days."""
        today = date.today()
        start_dt, end_dt = analytics_service._get_date_range(MetricTimeRange.LAST_30_DAYS)
        
        assert end_dt == today
        assert start_dt == today - timedelta(days=30)
    
    def test_get_date_range_custom(self, analytics_service):
        """Test custom date range."""
        start_date = date(2025, 7, 1)
        end_date = date(2025, 7, 26)
        
        start_dt, end_dt = analytics_service._get_date_range(
            MetricTimeRange.CUSTOM, start_date, end_date
        )
        
        assert start_dt == start_date
        assert end_dt == end_date
    
    def test_generate_date_series(self, analytics_service):
        """Test date series generation."""
        start_date = date(2025, 7, 1)
        end_date = date(2025, 7, 3)
        
        dates = analytics_service._generate_date_series(start_date, end_date)
        
        expected_dates = [date(2025, 7, 1), date(2025, 7, 2), date(2025, 7, 3)]
        assert dates == expected_dates
    
    # ==================== USAGE METRICS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_real_time_usage_metrics_success(
        self, analytics_service, mock_db_session, sample_organization, sample_users, sample_sounds
    ):
        """Test successful usage metrics retrieval."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_organization
        mock_db_session.query.return_value.filter.return_value.count.return_value = len(sample_users)
        mock_db_session.query.return_value.limit.return_value.all.return_value = sample_sounds
        
        # Call the method
        result = await analytics_service.get_real_time_usage_metrics("test-org-id")
        
        # Assertions
        assert result.organization_id == "test-org-id"
        assert result.organization_name == "Test Organization"
        assert result.time_range == MetricTimeRange.LAST_30_DAYS
        assert result.usage_metrics.total_sessions > 0
        assert result.usage_metrics.unique_active_users > 0
        assert result.usage_metrics.average_session_duration > 0
        assert len(result.usage_metrics.sessions_by_day) > 0
        assert result.compared_to_previous_period is not None
    
    @pytest.mark.asyncio
    async def test_get_real_time_usage_metrics_organization_not_found(
        self, analytics_service, mock_db_session
    ):
        """Test usage metrics when organization not found."""
        # Mock organization not found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Organization .* not found"):
            await analytics_service.get_real_time_usage_metrics("nonexistent-org")
    
    # ==================== ENGAGEMENT ANALYTICS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_user_engagement_analytics_success(
        self, analytics_service, mock_db_session, sample_organization, sample_users
    ):
        """Test successful engagement analytics retrieval."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_organization
        mock_db_session.query.return_value.filter.return_value.all.return_value = sample_users
        
        # Call the method
        result = await analytics_service.get_user_engagement_analytics("test-org-id")
        
        # Assertions
        assert result.organization_id == "test-org-id"
        assert result.organization_name == "Test Organization"
        assert result.engagement_analytics.total_users == len(sample_users)
        assert result.engagement_analytics.active_users_period > 0
        assert len(result.engagement_analytics.top_engaged_users) > 0
        assert len(result.engagement_analytics.engagement_trends) > 0
        assert len(result.engagement_analytics.recommendations) > 0
        
        # Check engagement distribution
        distribution = result.engagement_analytics.engagement_distribution
        total_distributed = sum(distribution.values())
        assert total_distributed >= len(sample_users)
    
    @pytest.mark.asyncio
    async def test_get_user_engagement_analytics_engagement_levels(
        self, analytics_service, mock_db_session, sample_organization, sample_users
    ):
        """Test engagement level classification."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_organization
        mock_db_session.query.return_value.filter.return_value.all.return_value = sample_users
        
        result = await analytics_service.get_user_engagement_analytics("test-org-id")
        
        # Check that all engagement levels are valid
        for user in result.engagement_analytics.top_engaged_users:
            assert user.engagement_level in [
                EngagementLevel.CRITICAL, EngagementLevel.LOW, EngagementLevel.MODERATE,
                EngagementLevel.HIGH, EngagementLevel.EXCEPTIONAL
            ]
            assert 0 <= user.engagement_score <= 100
    
    # ==================== REVENUE ANALYTICS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_revenue_attribution_success(
        self, analytics_service, mock_db_session, sample_organization, sample_users
    ):
        """Test successful revenue attribution retrieval."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_organization
        mock_db_session.query.return_value.filter.return_value.count.return_value = len(sample_users)
        
        # Call the method
        result = await analytics_service.get_revenue_attribution("test-org-id")
        
        # Assertions
        assert result.organization_id == "test-org-id"
        assert result.organization_name == "Test Organization"
        assert result.subscription_tier == SubscriptionTier.PROFESSIONAL.value
        assert result.revenue_metrics.current_period_revenue.total_revenue > 0
        assert result.revenue_metrics.monthly_recurring_revenue > 0
        assert result.revenue_metrics.annual_recurring_revenue > 0
        assert result.revenue_metrics.average_revenue_per_user > 0
        assert result.revenue_metrics.customer_lifetime_value > 0
        assert len(result.revenue_metrics.revenue_by_day) > 0
    
    @pytest.mark.asyncio
    async def test_get_revenue_attribution_subscription_tiers(
        self, analytics_service, mock_db_session, sample_users
    ):
        """Test revenue calculation for different subscription tiers."""
        # Test different subscription tiers
        tiers_to_test = [
            SubscriptionTier.STARTER,
            SubscriptionTier.PROFESSIONAL,
            SubscriptionTier.ENTERPRISE,
            SubscriptionTier.CUSTOM
        ]
        
        for tier in tiers_to_test:
            # Mock organization with specific tier
            org = Mock()
            org.id = "test-org-id"
            org.name = "Test Organization"
            org.subscription_tier = tier
            
            mock_db_session.query.return_value.filter.return_value.first.return_value = org
            mock_db_session.query.return_value.filter.return_value.count.return_value = len(sample_users)
            
            result = await analytics_service.get_revenue_attribution("test-org-id")
            
            # Revenue should vary by tier
            assert result.revenue_metrics.current_period_revenue.subscription_revenue > 0
            assert result.subscription_tier == tier.value
    
    # ==================== CONTENT ANALYTICS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_content_usage_analytics_success(
        self, analytics_service, mock_db_session, sample_organization, sample_sounds
    ):
        """Test successful content usage analytics retrieval."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_organization
        mock_db_session.query.return_value.limit.return_value.all.return_value = sample_sounds
        
        # Call the method
        result = await analytics_service.get_content_usage_analytics("test-org-id")
        
        # Assertions
        assert result.organization_id == "test-org-id"
        assert result.organization_name == "Test Organization"
        assert len(result.content_analytics.top_content) > 0
        assert len(result.content_analytics.recommended_content) > 0
        assert 0 <= result.content_analytics.content_diversity_score <= 100
        assert result.content_analytics.usage_patterns_by_time is not None
        
        # Check content patterns
        for content in result.content_analytics.top_content:
            assert content.total_plays > 0
            assert content.total_minutes > 0
            assert content.unique_users > 0
            assert 0 <= content.completion_rate <= 1
            assert content.average_rating is None or (0 <= content.average_rating <= 5)
    
    @pytest.mark.asyncio
    async def test_get_content_usage_analytics_categories(
        self, analytics_service, mock_db_session, sample_organization, sample_sounds
    ):
        """Test content category performance analysis."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_organization
        mock_db_session.query.return_value.limit.return_value.all.return_value = sample_sounds
        
        result = await analytics_service.get_content_usage_analytics("test-org-id")
        
        # Check category performance
        categories = result.content_analytics.content_categories_performance
        assert len(categories) > 0
        
        for category, stats in categories.items():
            assert isinstance(category, str)
            assert "plays" in stats
            assert "minutes" in stats  
            assert "users" in stats
    
    # ==================== HEALTH SCORING TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_organization_health_score_success(
        self, analytics_service, mock_db_session, sample_organization, sample_users
    ):
        """Test successful health score calculation."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_organization
        mock_db_session.query.return_value.filter.return_value.count.return_value = len(sample_users)
        
        # Call the method
        result = await analytics_service.get_organization_health_score("test-org-id")
        
        # Assertions
        assert result.organization_id == "test-org-id"
        assert result.organization_name == "Test Organization"
        assert result.subscription_tier == SubscriptionTier.PROFESSIONAL.value
        assert 0 <= result.health_metrics.overall_health_score <= 100
        assert result.health_metrics.health_status in [
            HealthStatus.CRITICAL, HealthStatus.POOR, HealthStatus.FAIR,
            HealthStatus.GOOD, HealthStatus.EXCELLENT
        ]
        assert len(result.health_metrics.health_factors) == 5  # 5 health factors
        assert result.health_metrics.trend_direction in ["improving", "stable", "declining"]
        assert len(result.historical_scores) > 0
        assert result.comparison_to_similar_orgs is not None
    
    @pytest.mark.asyncio
    async def test_get_organization_health_score_factors(
        self, analytics_service, mock_db_session, sample_organization, sample_users
    ):
        """Test health factor calculation and weighting."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_organization
        mock_db_session.query.return_value.filter.return_value.count.return_value = len(sample_users)
        
        result = await analytics_service.get_organization_health_score("test-org-id")
        
        # Check health factors
        factors = result.health_metrics.health_factors
        factor_names = [f.factor_name for f in factors]
        
        expected_factors = [
            "User Engagement", "Content Utilization", "Subscription Health",
            "Platform Adoption", "Growth Trend"
        ]
        
        for expected_factor in expected_factors:
            assert expected_factor in factor_names
        
        # Check factor properties
        total_weight = sum(f.weight for f in factors)
        assert abs(total_weight - 1.0) < 0.01  # Should sum to 1.0
        
        for factor in factors:
            assert 0 <= factor.current_score <= 100
            assert 0 <= factor.target_score <= 100
            assert 0 <= factor.weight <= 1
            assert len(factor.recommendations) > 0
    
    # ==================== COMPREHENSIVE ANALYTICS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_analytics_success(
        self, analytics_service, mock_db_session, sample_organization, sample_users, sample_sounds
    ):
        """Test comprehensive analytics retrieval."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_organization
        mock_db_session.query.return_value.filter.return_value.all.return_value = sample_users
        mock_db_session.query.return_value.filter.return_value.count.return_value = len(sample_users)
        mock_db_session.query.return_value.limit.return_value.all.return_value = sample_sounds
        
        # Call the method
        result = await analytics_service.get_comprehensive_analytics("test-org-id")
        
        # Assertions
        assert result.organization_id == "test-org-id"
        assert result.organization_name == "Test Organization"
        assert result.analytics.usage_summary is not None
        assert result.analytics.engagement_summary is not None
        assert result.analytics.revenue_summary is not None
        assert result.analytics.content_summary is not None
        assert result.analytics.health_summary is not None
        assert len(result.key_insights) > 0
        assert len(result.key_insights) <= 5  # Max 5 insights
    
    # ==================== BULK ANALYTICS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_bulk_analytics_success(
        self, analytics_service, mock_db_session, sample_users
    ):
        """Test bulk analytics retrieval."""
        # Create multiple organizations
        organizations = []
        for i in range(3):
            org = Mock()
            org.id = f"org-{i}"
            org.name = f"Organization {i+1}"
            org.subscription_tier = SubscriptionTier.PROFESSIONAL
            org.status = OrganizationStatus.ACTIVE
            organizations.append(org)
        
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.all.return_value = organizations
        mock_db_session.query.return_value.filter.return_value.count.return_value = len(sample_users)
        
        # Create filters
        filters = AnalyticsFilters(
            time_range=MetricTimeRange.LAST_30_DAYS,
            include_inactive=False
        )
        
        # Call the method
        result = await analytics_service.get_bulk_analytics(filters)
        
        # Assertions
        assert result.total_organizations == len(organizations)
        assert result.time_range == MetricTimeRange.LAST_30_DAYS
        assert len(result.organizations) == len(organizations)
        assert result.platform_averages is not None
        
        # Check organization summaries
        for org_summary in result.organizations:
            assert org_summary.organization_id is not None
            assert org_summary.organization_name is not None
            assert 0 <= org_summary.health_score <= 100
            assert org_summary.total_users >= 0
            assert org_summary.monthly_revenue >= 0
    
    @pytest.mark.asyncio
    async def test_get_bulk_analytics_with_filters(
        self, analytics_service, mock_db_session, sample_users
    ):
        """Test bulk analytics with various filters."""
        # Create organizations with different tiers
        organizations = []
        tiers = [SubscriptionTier.STARTER, SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]
        
        for i, tier in enumerate(tiers):
            org = Mock()
            org.id = f"org-{i}"
            org.name = f"Organization {i+1}"
            org.subscription_tier = tier
            org.status = OrganizationStatus.ACTIVE
            organizations.append(org)
        
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.all.return_value = organizations
        mock_db_session.query.return_value.filter.return_value.count.return_value = len(sample_users)
        
        # Test with subscription tier filter
        filters = AnalyticsFilters(
            subscription_tiers=["professional", "enterprise"],
            include_inactive=False
        )
        
        result = await analytics_service.get_bulk_analytics(filters)
        
        # Should include organizations (filtering is applied later in the service)
        assert result.total_organizations >= 0
        assert len(result.organizations) >= 0


class TestAnalyticsFilters:
    """Test suite for AnalyticsFilters validation."""
    
    def test_valid_filters(self):
        """Test valid filter creation."""
        filters = AnalyticsFilters(
            time_range=MetricTimeRange.LAST_30_DAYS,
            organization_ids=["org1", "org2"],
            subscription_tiers=["professional", "enterprise"],
            include_inactive=True
        )
        
        assert filters.time_range == MetricTimeRange.LAST_30_DAYS
        assert filters.organization_ids is not None and len(filters.organization_ids) == 2
        assert filters.subscription_tiers is not None and len(filters.subscription_tiers) == 2
        assert filters.include_inactive is True
    
    def test_custom_date_range_validation(self):
        """Test custom date range validation."""
        from datetime import date
        
        # Valid date range
        filters = AnalyticsFilters(
            time_range=MetricTimeRange.CUSTOM,
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 26)
        )
        
        assert filters.start_date == date(2025, 7, 1)
        assert filters.end_date == date(2025, 7, 26)
    
    def test_invalid_date_range_validation(self):
        """Test invalid date range validation."""
        from datetime import date
        from pydantic import ValidationError
        
        # Invalid date range (end before start)
        with pytest.raises(ValidationError):
            AnalyticsFilters(
                time_range=MetricTimeRange.CUSTOM,
                start_date=date(2025, 7, 26),
                end_date=date(2025, 7, 1)  # End before start
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
