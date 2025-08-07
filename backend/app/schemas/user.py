from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import SubscriptionStatus, PaymentMethod, UserRole

class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str
    telephone: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None
    # B2B2C Company information - required for organization registration
    company_name: str  # Required for B2B2C organization setup
    business_type: Optional[str] = None
    country: Optional[str] = None

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class UserReadSchema(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: UserRole  # Include role for dashboard routing
    organization_id: Optional[str] = None  # Include organization_id for business admin access

    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes

# New schemas for admin functionality
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_superuser: bool
    created_at: datetime
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_status: SubscriptionStatus
    last_login: Optional[datetime] = None
    telephone: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    subscription_status: Optional[SubscriptionStatus] = None
    telephone: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None

class TokenSchema(BaseModel):
    access_token: str
    token_type: str
