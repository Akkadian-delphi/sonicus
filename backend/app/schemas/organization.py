"""
Pydantic schemas for Organization model and related data structures.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum

from app.models.organization import OrganizationStatus, SubscriptionTier


class OrganizationBase(BaseModel):
    """Base organization schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    display_name: Optional[str] = Field(None, max_length=255, description="Display name for the organization")
    domain: str = Field(..., min_length=3, max_length=100, description="Organization domain (e.g., company.com)")
    primary_contact_email: EmailStr = Field(..., description="Primary contact email")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    
    # Address fields
    address_line1: Optional[str] = Field(None, max_length=255, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=255, description="Address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    
    # Business details
    industry: Optional[str] = Field(None, max_length=100, description="Industry type")
    company_size: Optional[str] = Field(None, max_length=50, description="Company size (e.g., '1-10', '11-50', etc.)")
    billing_email: Optional[EmailStr] = Field(None, description="Billing contact email")

    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain format."""
        if not v:
            return v
        # Basic domain validation - should contain at least one dot
        if '.' not in v:
            raise ValueError('Domain must contain at least one dot')
        # Remove protocol if present
        v = v.replace('http://', '').replace('https://', '')
        # Remove trailing slash
        v = v.rstrip('/')
        return v.lower()

    @validator('phone')
    def validate_phone(cls, v):
        """Basic phone validation."""
        if not v:
            return v
        # Remove common separators and whitespace
        cleaned = ''.join(c for c in v if c.isdigit() or c in '+()-. ')
        if len(cleaned.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return cleaned


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""
    subscription_tier: Optional[SubscriptionTier] = Field(SubscriptionTier.STARTER, description="Subscription tier")
    max_users: Optional[int] = Field(10, ge=1, le=10000, description="Maximum number of users allowed")
    max_sound_libraries: Optional[int] = Field(3, ge=1, le=1000, description="Maximum sound libraries allowed")
    trial_days: Optional[int] = Field(14, ge=0, le=90, description="Trial period in days")
    
    # Configuration
    features_enabled: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Feature flags and settings")
    branding_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom branding configuration")


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    domain: Optional[str] = Field(None, min_length=3, max_length=100)
    primary_contact_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    
    # Address fields
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Business details
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    billing_email: Optional[EmailStr] = None
    
    # Subscription details
    subscription_tier: Optional[SubscriptionTier] = None
    subscription_status: Optional[OrganizationStatus] = None
    max_users: Optional[int] = Field(None, ge=1, le=10000)
    max_sound_libraries: Optional[int] = Field(None, ge=1, le=1000)
    trial_end_date: Optional[datetime] = None
    
    # Configuration
    features_enabled: Optional[Dict[str, Any]] = None
    branding_config: Optional[Dict[str, Any]] = None

    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain format."""
        if not v:
            return v
        if '.' not in v:
            raise ValueError('Domain must contain at least one dot')
        v = v.replace('http://', '').replace('https://', '')
        v = v.rstrip('/')
        return v.lower()


class OrganizationResponse(BaseModel):
    """Schema for organization responses."""
    id: uuid.UUID
    name: str
    display_name: Optional[str]
    domain: str
    primary_contact_email: str
    phone: Optional[str]
    
    # Address fields
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    
    # Business details
    industry: Optional[str]
    company_size: Optional[str]
    billing_email: Optional[str]
    
    # Subscription details
    subscription_tier: SubscriptionTier
    subscription_status: OrganizationStatus
    max_users: int
    max_sound_libraries: int
    current_user_count: Optional[int] = 0
    trial_end_date: Optional[datetime]
    
    # Configuration
    features_enabled: Dict[str, Any] = Field(default_factory=dict)
    branding_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: lambda v: str(v)
        }


class OrganizationList(BaseModel):
    """Schema for paginated organization list."""
    organizations: List[OrganizationResponse]
    total_count: int
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=1000)
    has_next: bool

    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total_count + self.per_page - 1) // self.per_page


class OrganizationAnalytics(BaseModel):
    """Schema for organization analytics data."""
    organization_id: uuid.UUID
    organization_name: str
    period_days: int
    start_date: datetime
    end_date: datetime
    
    # Database metrics
    database_status: str
    database_size: str
    
    # User metrics
    total_users: int = 0
    active_users_today: int = 0
    active_users_week: int = 0
    active_users_month: int = 0
    
    # Usage metrics
    total_sessions: int = 0
    total_listen_time: int = 0  # in minutes
    average_session_length: float = 0  # in minutes
    
    # Subscription info
    subscription_status: OrganizationStatus
    subscription_tier: SubscriptionTier
    trial_end_date: Optional[datetime]
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: lambda v: str(v)
        }


class OrganizationSummary(BaseModel):
    """Schema for organization summary (minimal data)."""
    id: uuid.UUID
    name: str
    display_name: Optional[str]
    domain: str
    subscription_status: OrganizationStatus
    subscription_tier: SubscriptionTier
    current_user_count: int = 0
    max_users: int
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: lambda v: str(v)
        }


class OrganizationHealthCheck(BaseModel):
    """Schema for organization health check results."""
    organization_id: uuid.UUID
    organization_name: str
    database_status: str  # 'healthy', 'degraded', 'offline'
    database_size: str
    connection_test: bool
    last_backup: Optional[datetime]
    issues: List[str] = Field(default_factory=list)
    checked_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: lambda v: str(v)
        }


# ==================== ONBOARDING SCHEMAS ====================

class OnboardingStepDetail(BaseModel):
    """Schema for individual onboarding step details."""
    title: str
    description: str
    completed: bool


class OnboardingStatus(BaseModel):
    """Schema for organization onboarding status."""
    organization_id: str
    completed_steps: List[str]
    total_steps: int
    completion_percentage: float
    is_completed: bool
    current_step: str
    step_details: Dict[str, OnboardingStepDetail]
    estimated_completion_time: int  # in minutes

    class Config:
        json_encoders = {
            uuid.UUID: lambda v: str(v)
        }


class OnboardingStepUpdate(BaseModel):
    """Schema for updating an onboarding step."""
    completed: bool = Field(..., description="Whether the step is completed")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional step metadata")


class OnboardingStepResponse(BaseModel):
    """Schema for onboarding step update response."""
    message: str
    step_name: str
    completed: bool
    organization_id: str
    overall_completion: float


# ==================== BILLING SCHEMAS ====================

class BillingAddress(BaseModel):
    """Schema for billing address."""
    line1: Optional[str] = Field(None, max_length=255, description="Address line 1")
    line2: Optional[str] = Field(None, max_length=255, description="Address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")


class BillingSetup(BaseModel):
    """Schema for billing setup request."""
    payment_method_id: str = Field(..., description="Payment method ID from Stripe")
    billing_email: Optional[EmailStr] = Field(None, description="Billing contact email")
    billing_address: Optional[BillingAddress] = Field(None, description="Billing address")


class BillingSetupResponse(BaseModel):
    """Schema for billing setup response."""
    message: str
    organization_id: str
    stripe_customer_id: str
    billing_email: str
    status: str


class SubscriptionInfo(BaseModel):
    """Schema for subscription information."""
    tier: str
    status: str
    trial_end_date: Optional[str]


class BillingInfo(BaseModel):
    """Schema for billing information response."""
    organization_id: str
    billing_setup: bool
    stripe_customer_id: Optional[str] = None
    billing_email: Optional[str] = None
    payment_method_id: Optional[str] = None
    billing_address: Optional[BillingAddress] = None
    setup_date: Optional[str] = None
    status: str
    current_subscription: Optional[SubscriptionInfo] = None
    message: Optional[str] = None


class InvoiceCreate(BaseModel):
    """Schema for invoice creation request."""
    amount: float = Field(..., gt=0, description="Invoice amount")
    description: Optional[str] = Field(None, max_length=255, description="Invoice description")


class InvoiceResponse(BaseModel):
    """Schema for invoice creation response."""
    message: str
    invoice_id: str
    organization_id: str
    amount: float
    status: str
    due_date: str


# ==================== BULK OPERATIONS SCHEMAS ====================

class BulkFeatureUpdate(BaseModel):
    """Schema for bulk feature update request."""
    organization_ids: List[str] = Field(..., description="List of organization IDs")
    features: Dict[str, bool] = Field(..., description="Features to update")
    
    @validator('organization_ids')
    def validate_organization_ids(cls, v):
        if not v:
            raise ValueError('At least one organization ID is required')
        return v
    
    @validator('features')
    def validate_features(cls, v):
        if not v:
            raise ValueError('At least one feature is required')
        return v


class BulkUpdateResult(BaseModel):
    """Schema for individual bulk update result."""
    organization_id: str
    organization_name: Optional[str] = None
    updated_features: Optional[Dict[str, bool]] = None
    error: Optional[str] = None


class BulkFeatureUpdateResponse(BaseModel):
    """Schema for bulk feature update response."""
    successful_updates: List[BulkUpdateResult]
    failed_updates: List[BulkUpdateResult]
    total_organizations: int
    updated_features: Dict[str, bool]
