"""
Business Admin Customer Management Router

This module provides comprehensive customer management capabilities for business administrators
within their organizations. Includes user management, invitations, analytics, and profile operations.

Created: August 7, 2025
Author: Sonicus Platform Team
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import secrets

# Database and models
from app.db.session import get_db
from app.models.user import User, UserRole, SubscriptionStatus
from app.models.organization import Organization

# Schemas
from pydantic import BaseModel, EmailStr, Field

# Authentication and security
from app.core.security import get_current_user
from app.models.user import UserRole as UserRoleEnum
from typing import Union, Dict, Any

# Initialize router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to check business admin access
def check_business_admin(current_user: User):
    """Check if user is Business Admin or Super Admin."""
    allowed_roles = [UserRole.BUSINESS_ADMIN, UserRole.SUPER_ADMIN]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business Admin access required"
        )

# Helper function to get and validate business admin user
def get_business_admin_user(current_user: User = Depends(get_current_user)):
    """Get current user and validate business admin access."""
    check_business_admin(current_user)
    return current_user

# =================== PYDANTIC SCHEMAS ===================

class CustomerBase(BaseModel):
    email: EmailStr
    telephone: Optional[str] = None
    role: UserRole = UserRole.STAFF

class CustomerCreate(CustomerBase):
    password: Optional[str] = Field(None, min_length=8, description="Password for new customer")

class CustomerUpdate(BaseModel):
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class CustomerResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    is_active: bool
    telephone: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    subscription_status: SubscriptionStatus
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    is_trial_active: bool = False
    days_left_in_trial: int = 0

    class Config:
        from_attributes = True

class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class CustomerInvite(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.STAFF
    
    class Config:
        from_attributes = True

class CustomerAnalytics(BaseModel):
    activity_metrics: Dict[str, Any]
    usage_stats: Dict[str, Any]
    performance_indicators: Dict[str, Any]

class BulkOperationResult(BaseModel):
    successful: int
    failed: int
    errors: List[str]

# =================== API ENDPOINTS ===================

@router.get("/customers", response_model=CustomerListResponse)
async def list_organization_customers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of customers per page"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    role_filter: Optional[UserRole] = Query(None, description="Filter by role"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, inactive, trial"),
    sort_by: str = Query("created_at", description="Sort field: created_at, email, last_login, role"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    List all customers in the current user's organization with filtering and pagination
    """
    try:
        # Ensure user has an organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Build base query
        query = db.query(User).filter(User.organization_id == user_org_id)
        
        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_pattern),
                    User.telephone.ilike(search_pattern)
                )
            )
        
        # Apply role filter
        if role_filter:
            query = query.filter(User.role == role_filter.value)
        
        # Apply status filter
        if status_filter:
            if status_filter == "active":
                query = query.filter(User.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(User.is_active == False)
            elif status_filter == "trial":
                from sqlalchemy import text
                query = query.filter(text("users.subscription_status = 'trial'"))
        
        # Apply sorting
        sort_field = getattr(User, sort_by, User.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        customers = query.offset(offset).limit(page_size).all()
        
        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size
        
        # Convert to response format
        customer_responses = []
        for customer in customers:
            customer_response = CustomerResponse(
                id=getattr(customer, 'id', 0),
                email=getattr(customer, 'email', ''),
                role=UserRole(getattr(customer, 'role', 'staff')),
                is_active=getattr(customer, 'is_active', True),
                telephone=getattr(customer, 'telephone', None),
                created_at=getattr(customer, 'created_at', datetime.utcnow()),
                last_login=getattr(customer, 'last_login', None),
                subscription_status=SubscriptionStatus(getattr(customer, 'subscription_status', 'trial')),
                trial_start_date=getattr(customer, 'trial_start_date', None),
                trial_end_date=getattr(customer, 'trial_end_date', None),
                is_trial_active=getattr(customer, 'is_trial_active', False),
                days_left_in_trial=getattr(customer, 'days_left_in_trial', 0)
            )
            customer_responses.append(customer_response)
        
        return CustomerListResponse(
            customers=customer_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch customers: {str(e)}")

@router.post("/customers/invite", response_model=CustomerInvite)
async def invite_customer(
    customer_invite: CustomerInvite,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Invite a new customer to join the organization
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == customer_invite.email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
        
        # Get user's organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Generate temporary password
        temp_password = secrets.token_urlsafe(12)
        
        # Create new user
        new_customer = User(
            email=customer_invite.email,
            hashed_password=temp_password,  # This should be hashed properly
            role=customer_invite.role,
            organization_id=user_org_id,
            is_active=True,
            subscription_status=SubscriptionStatus.TRIAL,
            trial_start_date=datetime.utcnow(),
            trial_end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        
        # TODO: Send invitation email with temporary password
        logger.info(f"Customer invitation sent to {customer_invite.email}")
        
        return CustomerInvite(
            email=customer_invite.email,
            role=customer_invite.role
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error inviting customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to invite customer: {str(e)}")

@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Update customer information
    """
    try:
        # Get user's organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Find customer in the same organization
        customer = db.query(User).filter(
            User.id == customer_id,
            User.organization_id == user_org_id
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Update fields using setattr for SQLAlchemy compatibility
        if customer_update.email is not None:
            setattr(customer, 'email', customer_update.email)
        if customer_update.telephone is not None:
            setattr(customer, 'telephone', customer_update.telephone)
        if customer_update.role is not None:
            setattr(customer, 'role', customer_update.role.value)
        if customer_update.is_active is not None:
            setattr(customer, 'is_active', customer_update.is_active)
        
        db.commit()
        db.refresh(customer)
        
        return CustomerResponse(
            id=getattr(customer, 'id'),
            email=getattr(customer, 'email'),
            role=UserRole(getattr(customer, 'role')),
            is_active=getattr(customer, 'is_active'),
            telephone=getattr(customer, 'telephone'),
            created_at=getattr(customer, 'created_at'),
            last_login=getattr(customer, 'last_login'),
            subscription_status=SubscriptionStatus(getattr(customer, 'subscription_status')),
            trial_start_date=getattr(customer, 'trial_start_date'),
            trial_end_date=getattr(customer, 'trial_end_date'),
            is_trial_active=getattr(customer, 'is_trial_active', False),
            days_left_in_trial=getattr(customer, 'days_left_in_trial', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update customer: {str(e)}")

@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Delete a customer from the organization
    """
    try:
        # Get user's organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Find customer in the same organization
        customer = db.query(User).filter(
            User.id == customer_id,
            User.organization_id == user_org_id
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Don't allow deleting business admins or super admins
        if customer.role in [UserRole.BUSINESS_ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete admin users"
            )
        
        db.delete(customer)
        db.commit()
        
        return {"message": "Customer deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete customer: {str(e)}")

@router.get("/customers/{customer_id}/analytics", response_model=CustomerAnalytics)
async def get_customer_analytics(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get analytics data for a specific customer
    """
    try:
        # Get user's organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Find customer in the same organization
        customer = db.query(User).filter(
            User.id == customer_id,
            User.organization_id == user_org_id
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Mock analytics data - replace with real data
        activity_metrics = {
            "total_sessions": 45,
            "avg_session_duration": 25.5,
            "last_active": "2025-08-07T10:30:00Z",
            "weekly_usage_hours": 8.5
        }
        
        usage_stats = {
            "sounds_accessed": 12,
            "favorite_categories": ["Nature", "Meditation", "Focus"],
            "peak_usage_time": "14:00-16:00",
            "completion_rate": 78.5
        }
        
        performance_indicators = {
            "engagement_score": 8.2,
            "wellness_improvement": 15.3,
            "goal_achievement_rate": 67.8,
            "platform_adoption_score": 88.9
        }
        
        return CustomerAnalytics(
            activity_metrics=activity_metrics,
            usage_stats=usage_stats,
            performance_indicators=performance_indicators
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get customer analytics: {str(e)}")
