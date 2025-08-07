"""
Organization model for B2B2C architecture
Each organization represents a business customer of Sonicus
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import uuid
from enum import Enum


class SubscriptionTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class OrganizationStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    domain = Column(String(255), unique=True, nullable=True)  # For email domain-based access
    
    # Subscription details
    subscription_tier = Column(String(50), nullable=False, default=SubscriptionTier.STARTER)
    subscription_status = Column(String(50), nullable=False, default=OrganizationStatus.TRIAL)
    
    # Contact information
    primary_contact_email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Business details
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)  # "1-10", "11-50", "51-200", "201-1000", "1000+"
    
    # Subscription limits
    max_users = Column(Integer, nullable=False, default=10)
    max_sound_libraries = Column(Integer, nullable=False, default=3)
    
    # Features enabled
    features_enabled = Column(JSON, nullable=True)  # {"analytics": true, "custom_branding": false}
    
    # Billing information
    billing_email = Column(String(255), nullable=True)
    payment_method_id = Column(String(255), nullable=True)  # Stripe payment method ID
    
    # Customization
    branding_config = Column(JSON, nullable=True)  # Logo, colors, etc.
    custom_domain = Column(String(255), nullable=True)  # custom.sonicus.com
    
    # Metadata
    onboarding_completed = Column(Boolean, default=False)
    trial_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Database management for B2B2C multi-tenancy
    database_created = Column(Boolean, default=False)  # Track if org's database was created
    database_created_at = Column(DateTime, nullable=True)  # When database was created
    
    # Relationships
    # Temporarily commented out to avoid circular import issues
    # users = relationship("User", back_populates="organization")
    # sound_packages = relationship("OrganizationSoundPackage", back_populates="organization")
    # analytics = relationship("OrganizationAnalytics", back_populates="organization")
    
    # Note: Wellness metrics relationships will be added when those models are properly configured
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', status='{self.subscription_status}')>"


class OrganizationSoundPackage(Base):
    __tablename__ = "organization_sound_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Package details
    package_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # "sleep", "focus", "stress", "wellness"
    
    # Sound configuration
    sound_ids = Column(JSON, nullable=False)  # Array of sound IDs from therapy_sounds table
    
    # Delivery settings
    is_active = Column(Boolean, default=True)
    auto_assign_new_users = Column(Boolean, default=False)
    delivery_schedule = Column(JSON, nullable=True)  # {"daily": true, "time": "09:00", "days": ["mon", "tue"]}
    
    # Usage tracking
    total_listens = Column(Integer, default=0)
    unique_users_accessed = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # Temporarily commented out to avoid circular import issues
    # organization = relationship("Organization", back_populates="sound_packages")
    
    def __repr__(self):
        return f"<OrganizationSoundPackage(id={self.id}, name='{self.package_name}')>"


class OrganizationAnalytics(Base):
    __tablename__ = "organization_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Date for this analytics record
    date = Column(DateTime(timezone=True), nullable=False)
    
    # User metrics
    total_users = Column(Integer, default=0)
    active_users_today = Column(Integer, default=0)
    active_users_week = Column(Integer, default=0)
    active_users_month = Column(Integer, default=0)
    new_users_today = Column(Integer, default=0)
    
    # Usage metrics
    total_sessions = Column(Integer, default=0)
    total_listen_time = Column(Integer, default=0)  # in minutes
    average_session_length = Column(Integer, default=0)  # in minutes
    
    # Content metrics
    most_popular_sounds = Column(JSON, nullable=True)  # [{"sound_id": "123", "listens": 45}]
    most_popular_categories = Column(JSON, nullable=True)
    
    # Wellness metrics (if available)
    wellness_survey_responses = Column(Integer, default=0)
    average_wellness_score = Column(Integer, nullable=True)  # 1-10 scale
    stress_reduction_reported = Column(Integer, default=0)  # percentage
    sleep_improvement_reported = Column(Integer, default=0)  # percentage
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # Temporarily commented out to avoid circular import issues
    # organization = relationship("Organization", back_populates="analytics")
    
    def __repr__(self):
        return f"<OrganizationAnalytics(org_id={self.organization_id}, date={self.date})>"
