"""
Business Admin API endpoints for organization-level management.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import uuid

from app.core.security import get_current_user
from app.core.auth_transition import get_business_admin_user_transition, check_business_admin_transition
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationStatus, SubscriptionTier
from app.db.session import get_db
from typing import List, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/business-admin", tags=["business-admin"])


def check_business_admin(current_user: Union[User, Dict[str, Any]]):
    """Check if user is Business Admin or Super Admin (supports both auth types)."""
    if isinstance(current_user, dict):
        # OIDC user
        role = current_user.get("role", "user")
        if role not in ["super_admin", "business_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Business Admin access required"
            )
    else:
        # JWT user (SQLAlchemy User object)
        allowed_roles = [UserRole.BUSINESS_ADMIN, UserRole.SUPER_ADMIN]
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Business Admin access required"
            )


def safe_enum_value(value):
    """Safely get enum value - handles both enum objects and string values."""
    if value is None:
        return None
    if hasattr(value, 'value'):
        return value.value
    # If it's already a string, return as-is
    return str(value)

def get_user_organization_id(current_user: Union[User, Dict[str, Any]]) -> Optional[str]:
    """Get organization ID from user (supports both auth types)."""
    if isinstance(current_user, dict):
        # OIDC user - try to get org ID from local_user or token
        local_user = current_user.get("local_user")
        if local_user and hasattr(local_user, 'organization_id') and local_user.organization_id:
            return str(local_user.organization_id)
        # Could also extract from groups or custom claims
        return None
    else:
        # JWT user (SQLAlchemy User object)
        return str(current_user.organization_id) if getattr(current_user, 'organization_id', None) else None


@router.get("/organization")
async def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's organization details."""
    try:
        check_business_admin(current_user)
        
        user_org_id = getattr(current_user, 'organization_id')
        if not user_org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not associated with any organization"
            )
        
        organization = db.query(Organization).filter(
            Organization.id == user_org_id
        ).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Convert to response format
        result = {
            "id": str(organization.id),
            "name": organization.name,
            "display_name": organization.display_name,
            "domain": organization.domain,
            "primary_contact_email": organization.primary_contact_email,
            "phone": organization.phone,
            "address_line1": organization.address_line1,
            "address_line2": organization.address_line2,
            "city": organization.city,
            "state": organization.state,
            "country": organization.country,
            "postal_code": organization.postal_code,
            "industry": organization.industry,
            "company_size": organization.company_size,
            "billing_email": organization.billing_email,
            "subscription_tier": safe_enum_value(organization.subscription_tier),
            "subscription_status": safe_enum_value(organization.subscription_status),
            "max_users": organization.max_users,
            "max_sound_libraries": organization.max_sound_libraries,
            "features_enabled": organization.features_enabled or {},
            "branding_config": organization.branding_config or {},
            "created_at": organization.created_at.isoformat(),
            "updated_at": getattr(organization, 'updated_at').isoformat() if getattr(organization, 'updated_at') else None,
            "trial_end_date": getattr(organization, 'trial_end_date').isoformat() if getattr(organization, 'trial_end_date') else None
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving organization"
        )


@router.put("/organization")
async def update_my_organization(
    organization_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's organization (limited fields)."""
    try:
        check_business_admin(current_user)
        
        user_org_id = getattr(current_user, 'organization_id')
        if not user_org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not associated with any organization"
            )
        
        organization = db.query(Organization).filter(
            Organization.id == user_org_id
        ).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Define allowed fields for business admin updates
        allowed_fields = [
            'display_name', 'phone', 'address_line1', 'address_line2',
            'city', 'state', 'country', 'postal_code', 'industry',
            'company_size', 'billing_email', 'branding_config'
        ]
        
        # Update only allowed fields
        updated = False
        for field, value in organization_data.items():
            if field in allowed_fields and hasattr(organization, field):
                setattr(organization, field, value)
                updated = True
        
        if updated:
            setattr(organization, 'updated_at', datetime.utcnow())
            db.commit()
            db.refresh(organization)
        
        logger.info(f"Business admin {current_user.email} updated organization {organization.id}")
        
        # Convert to response format
        result = {
            "id": str(organization.id),
            "name": organization.name,
            "display_name": organization.display_name,
            "domain": organization.domain,
            "primary_contact_email": organization.primary_contact_email,
            "subscription_tier": safe_enum_value(organization.subscription_tier),
            "subscription_status": safe_enum_value(organization.subscription_status),
            "updated_at": getattr(organization, 'updated_at').isoformat() if getattr(organization, 'updated_at') else None
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update organization: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating organization"
        )


@router.get("/users")
async def list_organization_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    role_filter: Optional[str] = Query(None, description="Filter by user role"),
    search: Optional[str] = Query(None, description="Search by email")
):
    """List users in the current organization."""
    try:
        check_business_admin(current_user)
        
        if not getattr(current_user, 'organization_id'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not associated with any organization"
            )
        
        query = db.query(User).filter(User.organization_id == getattr(current_user, 'organization_id'))
        
        # Apply filters
        if role_filter:
            query = query.filter(User.role == role_filter)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(User.email.ilike(search_pattern))
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convert to response format
        user_list = []
        for user in users:
            user_dict = {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "telephone": user.telephone,
                "created_at": user.created_at.isoformat(),
                "trial_end_date": getattr(user, 'trial_end_date').isoformat() if getattr(user, 'trial_end_date') else None
            }
            user_list.append(user_dict)
        
        return {
            "users": user_list,
            "total_count": total_count,
            "page": skip // limit + 1,
            "per_page": limit,
            "has_next": skip + limit < total_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while listing users"
        )


@router.get("/analytics/summary")
async def get_organization_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics")
):
    """Get analytics summary for the current organization."""
    try:
        check_business_admin(current_user)
        
        if not getattr(current_user, 'organization_id'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not associated with any organization"
            )
        
        # Get organization info
        organization = db.query(Organization).filter(
            Organization.id == getattr(current_user, 'organization_id')
        ).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user counts
        total_users = db.query(User).filter(
            User.organization_id == getattr(current_user, 'organization_id')
        ).count()
        
        active_users = db.query(User).filter(
            User.organization_id == getattr(current_user, 'organization_id'),
            User.is_active == True
        ).count()
        
        # Get users by role
        user_role_stats = db.query(
            User.role,
            func.count(User.id).label('count')
        ).filter(
            User.organization_id == getattr(current_user, 'organization_id')
        ).group_by(User.role).all()
        
        role_stats = {}
        for stat in user_role_stats:
            role_stats[stat.role] = stat.count
        
        return {
            "organization_id": str(organization.id),
            "organization_name": organization.name,
            "subscription_tier": safe_enum_value(organization.subscription_tier),
            "subscription_status": safe_enum_value(organization.subscription_status),
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_users": total_users,
            "active_users": active_users,
            "max_users": organization.max_users,
            "usage_percentage": round((total_users / getattr(organization, 'max_users')) * 100, 2) if getattr(organization, 'max_users') > 0 else 0,
            "user_role_distribution": role_stats,
            "trial_end_date": getattr(organization, 'trial_end_date').isoformat() if getattr(organization, 'trial_end_date') else None,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving analytics"
        )


@router.get("/dashboard/stats")
async def get_business_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for Business Admin."""
    try:
        check_business_admin(current_user)
        
        if not getattr(current_user, 'organization_id'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not associated with any organization"
            )
        
        # Get organization
        organization = db.query(Organization).filter(
            Organization.id == getattr(current_user, 'organization_id')
        ).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get user stats
        total_users = db.query(User).filter(
            User.organization_id == getattr(current_user, 'organization_id')
        ).count()
        
        active_users = db.query(User).filter(
            User.organization_id == getattr(current_user, 'organization_id'),
            User.is_active == True
        ).count()
        
        # Get recent users (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_week = db.query(User).filter(
            User.organization_id == getattr(current_user, 'organization_id'),
            User.created_at >= week_ago
        ).count()
        
        # Calculate subscription health
        days_until_trial_end = None
        if getattr(organization, 'trial_end_date'):
            days_until_trial_end = (getattr(organization, 'trial_end_date') - datetime.utcnow()).days
        
        usage_percentage = round((total_users / getattr(organization, 'max_users')) * 100, 2) if getattr(organization, 'max_users') > 0 else 0
        
        return {
            "organization_name": organization.name,
            "subscription_tier": safe_enum_value(organization.subscription_tier),
            "subscription_status": safe_enum_value(organization.subscription_status),
            "total_users": total_users,
            "active_users": active_users,
            "max_users": organization.max_users,
            "usage_percentage": usage_percentage,
            "new_users_this_week": new_users_week,
            "days_until_trial_end": max(0, days_until_trial_end) if days_until_trial_end is not None else None,
            "trial_end_date": getattr(organization, 'trial_end_date').isoformat() if getattr(organization, 'trial_end_date') else None,
            "organization_health": "healthy" if usage_percentage < 90 else "near_limit",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving dashboard statistics"
        )
