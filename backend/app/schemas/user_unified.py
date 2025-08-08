"""
Unified User Schemas - Best of all user management systems

Combines features from user.py, user_b2c.py, and users_simple.py
Supports both B2B2C (organization-based) and B2C (direct customer) modes
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole, PaymentMethod, SubscriptionStatus

# === Base Schemas ===

class UserBaseSchema(BaseModel):
    """Base schema with common user fields."""
    email: EmailStr
    is_active: bool = True

class UserIdentitySchema(UserBaseSchema):
    """User identity with role and organization context."""
    id: int
    role: UserRole
    organization_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True

# === Profile Update Schemas ===

class UserProfileUpdateSchema(BaseModel):
    """Schema for updating user profile information."""
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    company_name: Optional[str] = None
    business_type: Optional[str] = None
    country: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None
    language: Optional[str] = None  # For internationalization
    notifications_enabled: Optional[bool] = None
    
    class Config:
        # Allow extra fields for future extensibility
        extra = "ignore"

# === Registration Schemas ===

class CustomerRegistrationSchema(BaseModel):
    """Schema for B2C customer registration."""
    email: EmailStr
    password: str
    name: str  # Full name for B2C customers
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class OrganizationRegistrationSchema(BaseModel):
    """Schema for B2B2C organization registration."""
    email: EmailStr
    password: str
    company_name: str
    business_type: Optional[str] = None
    country: Optional[str] = None
    telephone: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserRegistrationCompletionSchema(BaseModel):
    """Schema for completing user registration with additional details."""
    telephone: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None
    preferences: Optional[Dict[str, Any]] = None

# === Response Schemas ===

class UserReadSchema(UserIdentitySchema):
    """Standard user response schema."""
    pass

class UserProfileSchema(UserIdentitySchema):
    """Extended user profile with additional details."""
    telephone: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None
    company_name: Optional[str] = None
    business_type: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_status: SubscriptionStatus = SubscriptionStatus.TRIAL

class UserB2CProfileSchema(BaseModel):
    """B2C-specific user profile with enhanced features."""
    id: int
    email: EmailStr
    name: Optional[str] = None
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    is_premium: bool = False
    trial_end_date: Optional[datetime] = None
    total_sessions: int = 0
    total_listening_hours: float = 0.0
    wellness_streak_days: int = 0
    created_at: datetime
    has_subscription_details: bool = False
    has_preferences: bool = False
    
    class Config:
        from_attributes = True

# === Subscription Schemas ===

class SubscriptionUpdateSchema(BaseModel):
    """Schema for updating subscription details."""
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    billing_cycle: Optional[str] = None
    auto_renew: Optional[bool] = None

class SubscriptionResponseSchema(BaseModel):
    """Subscription details response."""
    id: UUID
    subscription_tier: str
    subscription_status: str
    billing_cycle: Optional[str] = None
    price_per_cycle: Optional[float] = None
    currency: str = "USD"
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    auto_renew: bool = True
    next_payment_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# === Preferences Schemas ===

class UserPreferencesSchema(BaseModel):
    """User preferences and settings."""
    preferred_session_length: Optional[int] = 20
    preferred_time_of_day: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = {}
    theme_preferences: Optional[Dict[str, Any]] = {}
    audio_preferences: Optional[Dict[str, Any]] = {}
    privacy_settings: Optional[Dict[str, Any]] = {}

class UserPreferencesResponseSchema(UserPreferencesSchema):
    """User preferences response with metadata."""
    id: UUID
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# === Analytics Schemas ===

class DailyAnalyticsSchema(BaseModel):
    """Daily analytics data."""
    date: str
    sessions_count: int
    listening_time_minutes: int
    completion_rate: float
    mood_improvement: Optional[float] = None

class UserAnalyticsSchema(BaseModel):
    """User analytics response."""
    period_days: int
    total_sessions: int
    total_listening_hours: float
    average_session_length: float
    completion_rate: float
    wellness_streak_days: int
    average_wellness_improvement: Optional[float] = None
    daily_analytics: List[DailyAnalyticsSchema]

# === Sound Package Schemas ===

class UserSoundPackageSchema(BaseModel):
    """User sound package assignment."""
    id: UUID
    sound_package_id: Union[UUID, int]  # Support both UUID and int package IDs
    package_name: str
    description: Optional[str] = None
    access_granted_at: datetime
    access_expires_at: Optional[datetime] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True

# === Authentication Schemas ===

class UserLoginSchema(BaseModel):
    """User login credentials."""
    email: EmailStr
    password: str

class TokenSchema(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: Optional[UserReadSchema] = None

class PasswordResetRequestSchema(BaseModel):
    """Password reset request."""
    email: EmailStr

class PasswordResetSchema(BaseModel):
    """Password reset with token."""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# === Platform Detection Schemas ===

class PlatformModeSchema(BaseModel):
    """Platform mode detection response."""
    mode: str  # "B2B2C" or "B2C"
    organization_count: int
    registration_path: str
    registration_text: str
    features_enabled: List[str]

# === Error Response Schemas ===

class ErrorResponseSchema(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

class ValidationErrorSchema(BaseModel):
    """Validation error response."""
    detail: str
    field_errors: Optional[Dict[str, List[str]]] = None
    timestamp: datetime = datetime.utcnow()

# === Success Response Schemas ===

class SuccessResponseSchema(BaseModel):
    """Standard success response."""
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()

class TrialStartResponseSchema(BaseModel):
    """Trial start response."""
    message: str
    trial_end_date: datetime
    days_remaining: int
    tier: str = "starter"

# === Admin Schemas ===

class UserAdminResponseSchema(UserProfileSchema):
    """Admin view of user with additional fields."""
    is_superuser: bool = False
    authentik_user_id: Optional[int] = None
    last_login: Optional[datetime] = None
    database_created: bool = False
    database_created_at: Optional[datetime] = None

class UserUpdateAdminSchema(BaseModel):
    """Admin schema for updating users."""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role: Optional[UserRole] = None
    subscription_status: Optional[SubscriptionStatus] = None
    telephone: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None

# === Utility Functions ===

def create_user_response(user, include_sensitive: bool = False) -> Dict[str, Any]:
    """Create a safe user response dictionary from SQLAlchemy model."""
    response = {
        "id": getattr(user, 'id'),
        "email": getattr(user, 'email'),
        "role": getattr(user, 'role'),
        "is_active": getattr(user, 'is_active', True),
        "organization_id": getattr(user, 'organization_id', None),
        "created_at": getattr(user, 'created_at')
    }
    
    if include_sensitive:
        response.update({
            "telephone": getattr(user, 'telephone', None),
            "preferred_payment_method": getattr(user, 'preferred_payment_method', None),
            "company_name": getattr(user, 'company_name', None),
            "business_type": getattr(user, 'business_type', None),
            "country": getattr(user, 'country', None),
            "trial_start_date": getattr(user, 'trial_start_date', None),
            "trial_end_date": getattr(user, 'trial_end_date', None),
            "subscription_status": getattr(user, 'subscription_status', SubscriptionStatus.TRIAL)
        })
    
    return response
