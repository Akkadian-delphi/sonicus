"""
Business Admin Organization-Specific API endpoints.
Handles organization-specific requests for business administrators.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import uuid

from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationStatus, SubscriptionTier
from app.models.sound_package import SoundPackage
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organization", tags=["business-admin-organization"])


def check_business_admin(current_user: User):
    """Check if user is Business Admin or Super Admin."""
    allowed_roles = [UserRole.BUSINESS_ADMIN, UserRole.SUPER_ADMIN]
    if getattr(current_user, 'role') not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business Admin access required"
        )


def safe_enum_value(value):
    """Safely get enum value - handles both enum objects and string values."""
    return value.value if hasattr(value, 'value') else value


@router.get("/{org_id}/details")
async def get_organization_details(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed organization information by organization ID."""
    try:
        check_business_admin(current_user)
        
        # For business admin, only allow accessing their own organization
        if getattr(current_user, 'role') == UserRole.BUSINESS_ADMIN:
            user_org_id = getattr(current_user, 'organization_id')
            if not user_org_id or str(user_org_id) != org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this organization"
                )
        
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get user count for this organization
        user_count = db.query(User).filter(User.organization_id == org_id).count()
        active_user_count = db.query(User).filter(
            User.organization_id == org_id,
            User.is_active == True
        ).count()
        
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
            "current_users": user_count,
            "active_users": active_user_count,
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
        logger.error(f"Failed to get organization details for {org_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving organization details"
        )


@router.get("/{org_id}/stats")
async def get_organization_stats(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get organization statistics and metrics."""
    try:
        check_business_admin(current_user)
        
        # For business admin, only allow accessing their own organization
        if getattr(current_user, 'role') == UserRole.BUSINESS_ADMIN:
            user_org_id = getattr(current_user, 'organization_id')
            if not user_org_id or str(user_org_id) != org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this organization"
                )
        
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get user statistics
        total_users = db.query(User).filter(User.organization_id == org_id).count()
        active_users = db.query(User).filter(
            User.organization_id == org_id,
            User.is_active == True
        ).count()
        
        # Get recent users (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_week = db.query(User).filter(
            User.organization_id == org_id,
            User.created_at >= week_ago
        ).count()
        
        # Get users by role
        user_role_stats = db.query(
            User.role,
            func.count(User.id).label('count')
        ).filter(
            User.organization_id == org_id
        ).group_by(User.role).all()
        
        role_stats = {}
        for stat in user_role_stats:
            role_stats[str(stat.role)] = stat.count
        
        # Calculate subscription health
        trial_end = getattr(organization, 'trial_end_date')
        days_until_trial_end = None
        if trial_end:
            days_until_trial_end = (trial_end - datetime.utcnow()).days
        
        max_users = getattr(organization, 'max_users')
        usage_percentage = round((total_users / max_users) * 100, 2) if max_users and max_users > 0 else 0
        
        return {
            "organization_id": str(organization.id),
            "organization_name": organization.name,
            "subscription_tier": safe_enum_value(organization.subscription_tier),
            "subscription_status": safe_enum_value(organization.subscription_status),
            "total_users": total_users,
            "active_users": active_users,
            "max_users": max_users,
            "usage_percentage": usage_percentage,
            "new_users_this_week": new_users_week,
            "user_role_distribution": role_stats,
            "days_until_trial_end": max(0, days_until_trial_end) if days_until_trial_end is not None else None,
            "trial_end_date": trial_end.isoformat() if trial_end else None,
            "organization_health": "healthy" if usage_percentage < 90 else "near_limit",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization stats for {org_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving organization statistics"
        )


@router.get("/{org_id}/wellness-analytics")
async def get_organization_wellness_analytics(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics")
):
    """Get wellness analytics for the organization."""
    try:
        check_business_admin(current_user)
        
        # For business admin, only allow accessing their own organization
        if getattr(current_user, 'role') == UserRole.BUSINESS_ADMIN:
            user_org_id = getattr(current_user, 'organization_id')
            if not user_org_id or str(user_org_id) != org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this organization"
                )
        
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get basic user engagement metrics
        total_users = db.query(User).filter(User.organization_id == org_id).count()
        active_users = db.query(User).filter(
            User.organization_id == org_id,
            User.is_active == True
        ).count()
        
        # Mock wellness analytics data (in a real implementation, this would come from actual wellness tracking)
        engagement_score = round((active_users / total_users) * 100, 2) if total_users > 0 else 0
        
        # Generate mock wellness metrics
        wellness_metrics = {
            "overall_wellness_score": min(85, max(45, engagement_score + 15)),
            "stress_reduction_percentage": min(25, max(5, engagement_score * 0.3)),
            "productivity_improvement": min(20, max(0, (engagement_score - 50) * 0.4)),
            "employee_satisfaction": min(90, max(40, engagement_score + 10))
        }
        
        return {
            "organization_id": str(organization.id),
            "organization_name": organization.name,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_users": total_users,
            "active_users": active_users,
            "engagement_score": engagement_score,
            "wellness_metrics": wellness_metrics,
            "trends": {
                "wellness_trend": "improving" if engagement_score > 60 else "stable",
                "engagement_trend": "stable",
                "productivity_trend": "improving" if engagement_score > 65 else "stable"
            },
            "recommendations": [
                "Continue current wellness programs" if engagement_score > 70 else "Consider enhancing employee engagement initiatives",
                "Regular check-ins with team members",
                "Promote work-life balance practices"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get wellness analytics for {org_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving wellness analytics"
        )


@router.get("/{org_id}/packages")
async def get_organization_packages(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """Get sound packages available to the organization."""
    try:
        check_business_admin(current_user)
        
        # For business admin, only allow accessing their own organization
        if getattr(current_user, 'role') == UserRole.BUSINESS_ADMIN:
            user_org_id = getattr(current_user, 'organization_id')
            if not user_org_id or str(user_org_id) != org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this organization"
                )
        
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get sound packages (for now, return mock data since sound package model might need adjustment)
        # In a real implementation, you'd query actual sound packages associated with this organization
        
        # Mock data for demonstration
        mock_packages = [
            {
                "id": str(uuid.uuid4()),
                "name": "Nature Sounds Collection",
                "description": "Relaxing nature sounds including rain, ocean waves, and forest ambience",
                "category": "nature",
                "duration_minutes": 45,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Focus & Concentration",
                "description": "Sounds designed to enhance focus and productivity",
                "category": "productivity",
                "duration_minutes": 60,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Stress Relief Suite",
                "description": "Calming sounds for stress reduction and relaxation",
                "category": "wellness",
                "duration_minutes": 30,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        # Apply pagination
        paginated_packages = mock_packages[skip:skip + limit]
        
        return {
            "organization_id": str(organization.id),
            "packages": paginated_packages,
            "total_count": len(mock_packages),
            "page": skip // limit + 1,
            "per_page": limit,
            "has_next": skip + limit < len(mock_packages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization packages for {org_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving organization packages"
        )
