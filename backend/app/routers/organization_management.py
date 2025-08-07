"""
Organization Management Router

Complete CRUD operations for organization management including:
- Organization onboarding workflow API
- Subscription plan assignment and management  
- Organization feature toggle management
- Billing integration with Stripe/payment processor
- Organization suspension and reactivation workflows
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi import status as http_status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import uuid
import logging
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.organization import Organization, OrganizationStatus, SubscriptionTier
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationList, OrganizationSummary, OnboardingStatus, OnboardingStepUpdate,
    OnboardingStepResponse, BillingSetup, BillingSetupResponse, BillingInfo,
    InvoiceCreate, InvoiceResponse, BulkFeatureUpdate, BulkFeatureUpdateResponse
)
from app.schemas.organization_analytics import (
    MetricTimeRange, AnalyticsFilters, RealTimeUsageMetrics, 
    UserEngagementAnalyticsResponse, RevenueAttributionResponse, 
    ContentUsageAnalyticsResponse, OrganizationHealthScoreResponse,
    ComprehensiveAnalyticsResponse, BulkAnalyticsResponse
)
from app.services.organization_analytics import OrganizationAnalyticsService
from app.core.auth_dependencies import get_admin_user_compatible

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== HELPER FUNCTIONS ====================

def format_datetime(dt_value):
    """Helper function to safely format datetime values from SQLAlchemy columns."""
    if dt_value is None:
        return None
    if hasattr(dt_value, 'isoformat'):
        return dt_value.isoformat()
    return str(dt_value)


# ==================== ORGANIZATION CRUD OPERATIONS ====================

@router.post("/organizations", response_model=OrganizationResponse, status_code=http_status.HTTP_201_CREATED)
async def create_organization(
    organization_data: OrganizationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """
    Create a new organization with onboarding workflow setup.
    """
    try:
        # Check if organization with domain already exists
        existing_org = db.query(Organization).filter(
            Organization.domain == organization_data.domain
        ).first()
        
        if existing_org:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Organization with this domain already exists"
            )
        
        # Calculate trial end date
        trial_end_date = None
        if organization_data.trial_days and organization_data.trial_days > 0:
            trial_end_date = datetime.utcnow() + timedelta(days=organization_data.trial_days)
        
        # Create organization
        new_org = Organization(
            id=uuid.uuid4(),
            name=organization_data.name,
            display_name=organization_data.display_name or organization_data.name,
            domain=organization_data.domain,
            primary_contact_email=organization_data.primary_contact_email,
            phone=organization_data.phone,
            
            # Address
            address_line1=organization_data.address_line1,
            address_line2=organization_data.address_line2,
            city=organization_data.city,
            state=organization_data.state,
            country=organization_data.country,
            postal_code=organization_data.postal_code,
            
            # Business details
            industry=organization_data.industry,
            company_size=organization_data.company_size,
            
            # Subscription setup
            subscription_tier=organization_data.subscription_tier or SubscriptionTier.STARTER.value,
            subscription_status=OrganizationStatus.TRIAL.value if trial_end_date else OrganizationStatus.ACTIVE.value,
            max_users=organization_data.max_users or 10,
            max_sound_libraries=organization_data.max_sound_libraries or 3,
            trial_end_date=trial_end_date,
            
            # Configuration
            features_enabled=get_default_features(organization_data.subscription_tier or SubscriptionTier.STARTER),
            branding_config=organization_data.branding_config or {},
            
            # Status
            onboarding_completed=False,
            database_created=False
        )
        
        db.add(new_org)
        db.commit()
        db.refresh(new_org)
        
        logger.info(f"Created organization {new_org.id} ({new_org.name}) by admin {current_admin.id}")
        
        # Send webhook for organization creation
        try:
            from app.services.webhook_service import webhook_service
            
            webhook_data = {
                "id": new_org.id,
                "name": new_org.name,
                "display_name": new_org.display_name,
                "domain": new_org.domain,
                "primary_contact_email": new_org.primary_contact_email,
                "subscription_tier": new_org.subscription_tier,
                "subscription_status": new_org.subscription_status,
                "max_users": new_org.max_users,
                "industry": new_org.industry,
                "company_size": new_org.company_size,
                "created_at": new_org.created_at,
                "trial_end_date": new_org.trial_end_date
            }
            
            # Send webhook in background (fire and forget)
            background_tasks.add_task(
                webhook_service.send_organization_created_webhook,
                webhook_data, db
            )
            
        except Exception as webhook_error:
            # Don't fail the organization creation if webhook fails
            logger.error(f"Failed to send organization creation webhook: {webhook_error}")
        
        # Convert to response model
        return create_org_response(new_org)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create organization: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )


@router.get("/organizations", response_model=OrganizationList)
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    status: Optional[List[OrganizationStatus]] = Query(None, description="Filter by status"),
    tier: Optional[List[SubscriptionTier]] = Query(None, description="Filter by subscription tier"),
    search: Optional[str] = Query(None, min_length=1, max_length=255, description="Search in name, email, domain"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """
    Get paginated list of organizations with filtering and search capabilities.
    """
    try:
        from sqlalchemy import and_, or_, desc, asc
        
        query = db.query(Organization)
        
        # Apply filters
        if status:
            status_values = [s.value if hasattr(s, 'value') else s for s in status]
            query = query.filter(Organization.subscription_status.in_(status_values))
        
        if tier:
            tier_values = [t.value if hasattr(t, 'value') else t for t in tier]
            query = query.filter(Organization.subscription_tier.in_(tier_values))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Organization.name.ilike(search_term),
                    Organization.primary_contact_email.ilike(search_term),
                    Organization.domain.ilike(search_term)
                )
            )
        
        # Apply sorting
        sort_field = getattr(Organization, sort_by, Organization.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        organizations = query.offset(offset).limit(per_page).all()
        
        # Convert to response format
        org_responses = [create_org_response(org) for org in organizations]
        
        return OrganizationList(
            organizations=org_responses,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total_count
        )
        
    except Exception as e:
        logger.error(f"Failed to list organizations: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organizations"
        )


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """Get detailed information about a specific organization."""
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not organization:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return create_org_response(organization)


@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    update_data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """
    Update organization information with comprehensive audit logging.
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Validate domain uniqueness if being updated
        if update_data.domain and update_data.domain != organization.domain:
            existing_domain = db.query(Organization).filter(
                Organization.domain == update_data.domain,
                Organization.id != org_id
            ).first()
            
            if existing_domain:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Domain already exists for another organization"
                )
        
        # Apply updates
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(organization, field) and value is not None:
                setattr(organization, field, value)
        
        db.commit()
        db.refresh(organization)
        
        logger.info(f"Updated organization {org_id} by admin {current_admin.id}")
        
        return create_org_response(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update organization {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization"
        )


@router.delete("/organizations/{org_id}")
async def archive_organization(
    org_id: uuid.UUID,
    soft_delete: bool = Query(True, description="Soft delete (archive) vs permanent delete"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """
    Archive or permanently delete an organization.
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if soft_delete:
            # Soft delete - change status to cancelled
            old_status = organization.subscription_status
            db.query(Organization).filter(Organization.id == org_id).update({
                "subscription_status": OrganizationStatus.CANCELLED.value
            })
            
            db.commit()
            
            logger.info(f"Archived organization {org_id} by admin {current_admin.id}")
            return {"message": "Organization archived successfully"}
        else:
            # Hard delete - permanent removal
            org_name = organization.name
            
            db.delete(organization)
            db.commit()
            
            logger.info(f"Permanently deleted organization {org_id} ({org_name}) by admin {current_admin.id}")
            return {"message": "Organization permanently deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete organization {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete organization"
        )


# ==================== SUBSCRIPTION MANAGEMENT ====================

@router.get("/organizations/{org_id}/subscription")
async def get_subscription_summary(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """
    Get comprehensive subscription summary including usage, limits, and billing.
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Calculate usage metrics
        current_users = get_organization_user_count(db, org_id)
        current_sound_libraries = get_sound_library_count(db, org_id)
        
        # Get tier configuration
        tier_config = get_tier_configuration(str(organization.subscription_tier))
        
        # Calculate trial status
        is_trial = str(organization.subscription_status) == OrganizationStatus.TRIAL.value
        days_until_trial_end = None
        if is_trial:
            trial_end = getattr(organization, 'trial_end_date', None)
            if trial_end:
                delta = trial_end - datetime.utcnow()
                days_until_trial_end = max(0, delta.days)
        
        max_users = getattr(organization, 'max_users', 0) or 0
        max_libraries = getattr(organization, 'max_sound_libraries', 0) or 0
        
        return {
            "organization_id": str(org_id),
            "organization_name": organization.name,
            "subscription_tier": organization.subscription_tier,
            "subscription_status": organization.subscription_status,
            
            # Usage and limits
            "usage": {
                "current_users": current_users,
                "max_users": max_users,
                "users_percentage": (current_users / max_users) * 100 if max_users > 0 else 0,
                "current_sound_libraries": current_sound_libraries,
                "max_sound_libraries": max_libraries,
                "libraries_percentage": (current_sound_libraries / max_libraries) * 100 if max_libraries > 0 else 0
            },
            
            # Features
            "features": {
                "enabled_features": organization.features_enabled or {},
                "available_features": tier_config.get("features", {}),
                "feature_count": len([f for f, enabled in (organization.features_enabled or {}).items() if enabled])
            },
            
            # Trial information
            "trial": {
                "is_trial": is_trial,
                "trial_end_date": format_datetime(getattr(organization, 'trial_end_date', None)),
                "days_until_trial_end": days_until_trial_end,
                "trial_expired": is_trial and days_until_trial_end == 0
            },
            
            # Billing
            "billing": {
                "monthly_cost": tier_config.get("monthly_cost", 0),
                "yearly_cost": tier_config.get("yearly_cost", 0),
                "currency": "USD",
                "billing_email": organization.billing_email,
                "payment_method_configured": bool(organization.payment_method_id)
            },
            
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subscription summary for {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription summary"
        )


@router.put("/organizations/{org_id}/subscription")
async def update_subscription_plan(
    org_id: uuid.UUID,
    new_tier: SubscriptionTier,
    billing_cycle: str = "monthly",
    effective_date: Optional[datetime] = None,
    prorate: bool = True,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """
    Update organization subscription plan with comprehensive validation.
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        old_tier = str(organization.subscription_tier)
        
        # Validate downgrade constraints
        if new_tier.value != old_tier:
            await validate_subscription_change(db, org_id, old_tier, new_tier.value)
        
        # Get new tier configuration
        tier_config = get_tier_configuration(new_tier.value)
        
        # Update subscription
        setattr(organization, 'subscription_tier', new_tier.value)
        setattr(organization, 'max_users', tier_config["max_users"])
        setattr(organization, 'max_sound_libraries', tier_config["max_sound_libraries"])
        setattr(organization, 'features_enabled', tier_config["features"])
        
        # If upgrading from trial to paid, change status
        if (new_tier != SubscriptionTier.STARTER and 
            str(organization.subscription_status) == OrganizationStatus.TRIAL.value):
            setattr(organization, 'subscription_status', OrganizationStatus.ACTIVE.value)
        
        db.commit()
        
        logger.info(f"Updated subscription for organization {org_id} from {old_tier} to {new_tier.value}")
        
        return {
            "organization_id": str(org_id),
            "old_tier": old_tier,
            "new_tier": new_tier.value,
            "billing_cycle": billing_cycle,
            "effective_date": effective_date.isoformat() if effective_date else datetime.utcnow().isoformat(),
            "updated_limits": {
                "max_users": organization.max_users,
                "max_sound_libraries": organization.max_sound_libraries
            },
            "enabled_features": organization.features_enabled,
            "message": "Subscription updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update subscription for {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription"
        )


# ==================== FEATURE TOGGLE MANAGEMENT ====================

@router.get("/organizations/{org_id}/features")
async def get_organization_features(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """Get all features and their status for an organization."""
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not organization:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    tier_config = get_tier_configuration(str(organization.subscription_tier))
    
    return {
        "organization_id": str(org_id),
        "organization_name": str(organization.name),
        "subscription_tier": str(organization.subscription_tier),
        "enabled_features": getattr(organization, 'features_enabled', {}) or {},
        "available_features": tier_config["features"],
        "feature_limits": get_feature_limits(str(organization.subscription_tier)),
        "last_updated": datetime.utcnow().isoformat()
    }


@router.put("/organizations/{org_id}/features/{feature_name}")
async def update_feature_toggle(
    org_id: uuid.UUID,
    feature_name: str,
    enabled: bool,
    metadata: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """
    Toggle a specific feature for an organization.
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Validate feature name and tier permissions
        tier_config = get_tier_configuration(str(organization.subscription_tier))
        available_features = tier_config["features"]
        
        if feature_name not in available_features:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Feature '{feature_name}' not available for {str(organization.subscription_tier)} tier"
            )
        
        if enabled and not available_features[feature_name]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Feature '{feature_name}' not allowed for {str(organization.subscription_tier)} tier"
            )
        
        # Update feature toggle
        current_features = getattr(organization, 'features_enabled', {}) or {}
        
        if not current_features:
            current_features = {}
        
        old_value = current_features.get(feature_name, False)
        
        # Create a new dict to avoid SQLAlchemy issues
        updated_features = dict(current_features)
        updated_features[feature_name] = enabled
        
        # Add metadata if provided
        if metadata and enabled:
            feature_metadata_key = f"{feature_name}_metadata"
            updated_features[feature_metadata_key] = metadata
        
        # Update the organization
        setattr(organization, 'features_enabled', updated_features)
        
        db.commit()
        
        logger.info(f"Updated feature '{feature_name}' to {enabled} for organization {org_id}")
        
        return {
            "organization_id": str(org_id),
            "feature_name": feature_name,
            "enabled": enabled,
            "metadata": metadata,
            "previous_value": old_value,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update feature toggle for {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feature toggle"
        )


# ==================== ORGANIZATION STATUS MANAGEMENT ====================

@router.post("/organizations/{org_id}/suspend")
async def suspend_organization(
    org_id: uuid.UUID,
    reason: str,
    notify_users: bool = True,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """
    Suspend an organization with comprehensive audit trail.
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if str(organization.subscription_status) == OrganizationStatus.SUSPENDED.value:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Organization is already suspended"
            )
        
        old_status = str(organization.subscription_status)
        setattr(organization, 'subscription_status', OrganizationStatus.SUSPENDED.value)
        
        db.commit()
        
        logger.info(f"Suspended organization {org_id} by admin {current_admin.id}. Reason: {reason}")
        
        return {
            "organization_id": str(org_id),
            "organization_name": organization.name,
            "status": "suspended",
            "reason": reason,
            "suspended_at": datetime.utcnow().isoformat(),
            "suspended_by": current_admin.id,
            "notify_users": notify_users,
            "message": "Organization suspended successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to suspend organization {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend organization"
        )


@router.post("/organizations/{org_id}/reactivate")
async def reactivate_organization(
    org_id: uuid.UUID,
    notify_users: bool = True,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """
    Reactivate a suspended organization.
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if str(organization.subscription_status) != OrganizationStatus.SUSPENDED.value:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Organization is not suspended"
            )
        
        # Restore to active status (can be enhanced to restore previous status)
        previous_status = OrganizationStatus.ACTIVE.value
        
        # Check if trial has expired while suspended
        trial_end = getattr(organization, 'trial_end_date', None)
        if trial_end and datetime.utcnow() > trial_end:
            previous_status = OrganizationStatus.CANCELLED.value
        
        setattr(organization, 'subscription_status', previous_status)
        db.commit()
        
        logger.info(f"Reactivated organization {org_id} by admin {current_admin.id}")
        
        return {
            "organization_id": str(org_id),
            "organization_name": organization.name,
            "status": previous_status,
            "reactivated_at": datetime.utcnow().isoformat(),
            "reactivated_by": current_admin.id,
            "notify_users": notify_users,
            "message": "Organization reactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reactivate organization {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate organization"
        )


# ==================== HELPER FUNCTIONS ====================

def create_org_response(org) -> OrganizationResponse:
    """Create OrganizationResponse from org model."""
    try:
        # Handle domain with fallback
        domain = getattr(org, 'domain', '') or ''
        
        # Handle subscription tier - get raw value first
        sub_tier = getattr(org, 'subscription_tier', None)
        if sub_tier and hasattr(sub_tier, 'value'):
            tier_value = sub_tier.value
        else:
            tier_value = str(sub_tier) if sub_tier else 'starter'
        
        # Convert string back to enum for schema
        try:
            subscription_tier = SubscriptionTier(tier_value)
        except ValueError:
            subscription_tier = SubscriptionTier.STARTER
            
        # Handle subscription status - get raw value first  
        sub_status = getattr(org, 'subscription_status', None)
        if sub_status and hasattr(sub_status, 'value'):
            status_value = sub_status.value
        else:
            status_value = str(sub_status) if sub_status else 'active'
            
        # Convert string back to enum for schema
        try:
            subscription_status = OrganizationStatus(status_value)
        except ValueError:
            subscription_status = OrganizationStatus.ACTIVE
        
        # Handle created_at with fallback
        created_at = getattr(org, 'created_at', None)
        if created_at is None:
            from datetime import datetime
            created_at = datetime.utcnow()
            
        # Handle UUID conversion for id field
        org_id = getattr(org, 'id', None)
        if org_id:
            try:
                from uuid import UUID
                if isinstance(org_id, str):
                    id_value = UUID(org_id)
                else:
                    id_value = org_id
            except ValueError:
                from uuid import uuid4
                id_value = uuid4()
        else:
            from uuid import uuid4
            id_value = uuid4()
            
        return OrganizationResponse(
            id=id_value,
            name=str(getattr(org, 'name', '')),
            display_name=getattr(org, 'display_name', None),
            domain=domain,
            primary_contact_email=str(getattr(org, 'primary_contact_email', '')),
            phone=getattr(org, 'phone', None),
            address_line1=getattr(org, 'address_line1', None),
            address_line2=getattr(org, 'address_line2', None),
            city=getattr(org, 'city', None),
            state=getattr(org, 'state', None),
            country=getattr(org, 'country', None),
            postal_code=getattr(org, 'postal_code', None),
            industry=getattr(org, 'industry', None),
            company_size=getattr(org, 'company_size', None),
            billing_email=getattr(org, 'billing_email', None),
            subscription_tier=subscription_tier,
            subscription_status=subscription_status,
            max_users=int(getattr(org, 'max_users', 0)),
            max_sound_libraries=int(getattr(org, 'max_sound_libraries', 0)),
            current_user_count=int(getattr(org, 'current_user_count', 0)),
            trial_end_date=getattr(org, 'trial_end_date', None),
            features_enabled=getattr(org, 'features_enabled', {}),
            branding_config=getattr(org, 'branding_config', {}),
            created_at=created_at,
            updated_at=getattr(org, 'updated_at', created_at)
        )
    except Exception as e:
        # Return default response on error
        from datetime import datetime
        from uuid import uuid4
        return OrganizationResponse(
            id=uuid4(),
            name='',
            display_name=None,
            domain='',
            primary_contact_email='',
            phone=None,
            address_line1=None,
            address_line2=None,
            city=None,
            state=None,
            country=None,
            postal_code=None,
            industry=None,
            company_size=None,
            billing_email=None,
            subscription_tier=SubscriptionTier.STARTER,
            subscription_status=OrganizationStatus.ACTIVE,
            max_users=0,
            max_sound_libraries=0,
            current_user_count=0,
            trial_end_date=None,
            features_enabled={},
            branding_config={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )


def get_default_features(tier) -> Dict[str, bool]:
    """Get default features for a subscription tier."""
    # Handle both string and enum inputs  
    tier_key = tier.value if hasattr(tier, 'value') else tier
    
    feature_sets = {
        SubscriptionTier.STARTER.value: {
            "analytics": False,
            "custom_branding": False,
            "api_access": False,
            "advanced_reporting": False,
            "white_labeling": False,
            "sso_integration": False,
            "bulk_user_management": False,
            "custom_sounds": False,
            "priority_support": False,
            "webhook_notifications": False
        },
        SubscriptionTier.PROFESSIONAL.value: {
            "analytics": True,
            "custom_branding": True,
            "api_access": True,
            "advanced_reporting": False,
            "white_labeling": False,
            "sso_integration": False,
            "bulk_user_management": True,
            "custom_sounds": True,
            "priority_support": False,
            "webhook_notifications": True
        },
        SubscriptionTier.ENTERPRISE.value: {
            "analytics": True,
            "custom_branding": True,
            "api_access": True,
            "advanced_reporting": True,
            "white_labeling": True,
            "sso_integration": True,
            "bulk_user_management": True,
            "custom_sounds": True,
            "priority_support": True,
            "webhook_notifications": True
        },
        SubscriptionTier.CUSTOM.value: {
            "analytics": True,
            "custom_branding": True,
            "api_access": True,
            "advanced_reporting": True,
            "white_labeling": True,
            "sso_integration": True,
            "bulk_user_management": True,
            "custom_sounds": True,
            "priority_support": True,
            "webhook_notifications": True
        }
    }
    
    return feature_sets.get(tier_key, feature_sets[SubscriptionTier.STARTER.value])


def get_tier_configuration(tier: str) -> Dict[str, Any]:
    """Get configuration for a subscription tier."""
    configurations = {
        SubscriptionTier.STARTER.value: {
            "max_users": 10,
            "max_sound_libraries": 3,
            "monthly_cost": 0,
            "yearly_cost": 0,
            "features": get_default_features(SubscriptionTier.STARTER.value)
        },
        SubscriptionTier.PROFESSIONAL.value: {
            "max_users": 100,
            "max_sound_libraries": 10,
            "monthly_cost": 49,
            "yearly_cost": 490,
            "features": get_default_features(SubscriptionTier.PROFESSIONAL.value)
        },
        SubscriptionTier.ENTERPRISE.value: {
            "max_users": 1000,
            "max_sound_libraries": 50,
            "monthly_cost": 199,
            "yearly_cost": 1990,
            "features": get_default_features(SubscriptionTier.ENTERPRISE.value)
        },
        SubscriptionTier.CUSTOM.value: {
            "max_users": 10000,
            "max_sound_libraries": 100,
            "monthly_cost": 0,  # Custom pricing
            "yearly_cost": 0,   # Custom pricing
            "features": get_default_features(SubscriptionTier.CUSTOM.value)
        }
    }
    
    return configurations.get(tier, configurations[SubscriptionTier.STARTER.value])


def get_feature_limits(tier: str) -> Dict[str, Any]:
    """Get feature usage limits for a tier."""
    limits = {
        SubscriptionTier.STARTER.value: {
            "api_calls_per_month": 1000,
            "custom_sounds": 0,
            "webhook_endpoints": 1,
            "sso_providers": 0
        },
        SubscriptionTier.PROFESSIONAL.value: {
            "api_calls_per_month": 10000,
            "custom_sounds": 10,
            "webhook_endpoints": 5,
            "sso_providers": 2
        },
        SubscriptionTier.ENTERPRISE.value: {
            "api_calls_per_month": 100000,
            "custom_sounds": 50,
            "webhook_endpoints": 20,
            "sso_providers": 10
        },
        SubscriptionTier.CUSTOM.value: {
            "api_calls_per_month": -1,  # Unlimited
            "custom_sounds": -1,        # Unlimited
            "webhook_endpoints": -1,    # Unlimited
            "sso_providers": -1         # Unlimited
        }
    }
    
    return limits.get(tier, limits[SubscriptionTier.STARTER.value])


async def validate_subscription_change(
    db: Session, 
    org_id: uuid.UUID, 
    old_tier: str, 
    new_tier: str
):
    """Validate that subscription change is allowed based on current usage."""
    if old_tier == new_tier:
        return
    
    # Get current usage
    current_users = get_organization_user_count(db, org_id)
    current_libraries = get_sound_library_count(db, org_id)
    
    # Get new tier limits
    new_config = get_tier_configuration(new_tier)
    
    # Check if downgrade is possible
    if current_users > new_config["max_users"]:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot downgrade: Current users ({current_users}) exceeds limit for {new_tier} tier ({new_config['max_users']})"
        )
    
    if current_libraries > new_config["max_sound_libraries"]:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot downgrade: Current sound libraries ({current_libraries}) exceeds limit for {new_tier} tier ({new_config['max_sound_libraries']})"
        )


def get_organization_user_count(db: Session, org_id: uuid.UUID) -> int:
    """Get current user count for organization."""
    try:
        from app.models.user import User
        return db.query(User).filter(User.organization_id == org_id).count()
    except Exception:
        return 0


def get_sound_library_count(db: Session, org_id: uuid.UUID) -> int:
    """Get current sound library count for organization."""
    try:
        from app.models.organization import OrganizationSoundPackage
        return db.query(OrganizationSoundPackage).filter(
            OrganizationSoundPackage.organization_id == org_id,
            OrganizationSoundPackage.is_active == True
        ).count()
    except Exception:
        return 0


# ==================== ORGANIZATION ONBOARDING WORKFLOW API ====================

@router.get("/organizations/{org_id}/onboarding")
async def get_onboarding_status(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """Get detailed onboarding status for an organization."""
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Define onboarding steps and check completion
        onboarding_steps = {
            "registration": True,  # Always completed if org exists
            "email_verification": check_email_verified(organization),
            "organization_setup": check_organization_setup_complete(organization),
            "subscription_selection": str(getattr(organization, 'subscription_tier', '')) != 'starter',
            "payment_setup": check_payment_setup_complete(organization),
            "team_invitation": get_organization_user_count(db, org_id) > 1,
            "initial_configuration": bool(getattr(organization, 'features_enabled', None) or getattr(organization, 'branding_config', None)),
        }
        
        completed_steps = [step for step, completed in onboarding_steps.items() if completed]
        total_steps = len(onboarding_steps)
        completion_percentage = (len(completed_steps) / total_steps) * 100
        
        current_step = get_next_onboarding_step(onboarding_steps)
        
        return {
            "organization_id": str(org_id),
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "completion_percentage": round(completion_percentage, 1),
            "is_completed": getattr(organization, 'onboarding_completed', False),
            "current_step": current_step,
            "step_details": get_onboarding_step_details(onboarding_steps),
            "estimated_completion_time": estimate_onboarding_completion_time(onboarding_steps)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get onboarding status for {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get onboarding status: {str(e)}"
        )


@router.put("/organizations/{org_id}/onboarding/{step_name}")
async def update_onboarding_step(
    org_id: uuid.UUID,
    step_name: str,
    step_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """Update a specific onboarding step."""
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        completed = step_data.get("completed", False)
        metadata = step_data.get("metadata", {})
        
        # Update step completion in organization metadata
        current_metadata = getattr(organization, 'metadata', None) or {}
        if "onboarding_steps" not in current_metadata:
            current_metadata["onboarding_steps"] = {}
        
        current_metadata["onboarding_steps"][step_name] = {
            "completed": completed,
            "completed_at": datetime.utcnow().isoformat() if completed else None,
            "metadata": metadata,
            "updated_by": getattr(current_admin, 'id', None)
        }
        
        setattr(organization, 'metadata', current_metadata)
        
        # Check if all onboarding is complete
        onboarding_status = await get_onboarding_status(org_id, db, current_admin)
        if onboarding_status["completion_percentage"] >= 100:
            setattr(organization, 'onboarding_completed', True)
        
        setattr(organization, 'updated_at', datetime.utcnow())
        db.commit()
        
        logger.info(f"Updated onboarding step {step_name} for organization {org_id}")
        
        return {
            "message": f"Onboarding step '{step_name}' updated successfully",
            "step_name": step_name,
            "completed": completed,
            "organization_id": str(org_id),
            "overall_completion": onboarding_status["completion_percentage"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update onboarding step for {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update onboarding step: {str(e)}"
        )


# ==================== BILLING INTEGRATION API ====================

@router.post("/organizations/{org_id}/billing/setup")
async def setup_billing(
    org_id: uuid.UUID,
    billing_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """Set up billing integration for an organization."""
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Simulate Stripe customer creation
        stripe_customer_id = f"cus_{uuid.uuid4().hex[:24]}"
        payment_method_id = billing_data.get("payment_method_id")
        billing_email = billing_data.get("billing_email", getattr(organization, 'primary_contact_email', ''))
        
        # Update organization with billing information
        billing_info = {
            "stripe_customer_id": stripe_customer_id,
            "payment_method_id": payment_method_id,
            "billing_email": billing_email,
            "billing_address": billing_data.get("billing_address", {}),
            "setup_date": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        current_metadata = getattr(organization, 'metadata', None) or {}
        current_metadata["billing"] = billing_info
        setattr(organization, 'metadata', current_metadata)
        setattr(organization, 'updated_at', datetime.utcnow())
        
        db.commit()
        
        # Schedule background task for billing setup verification
        background_tasks.add_task(verify_billing_setup, org_id, stripe_customer_id)
        
        logger.info(f"Set up billing for organization {org_id} with Stripe customer {stripe_customer_id}")
        
        return {
            "message": "Billing setup completed successfully",
            "organization_id": str(org_id),
            "stripe_customer_id": stripe_customer_id,
            "billing_email": billing_email,
            "status": "active"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to setup billing for {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup billing: {str(e)}"
        )


@router.get("/organizations/{org_id}/billing")
async def get_billing_info(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """Get billing information for an organization."""
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        metadata = getattr(organization, 'metadata', None) or {}
        billing_info = metadata.get("billing", {})
        
        if not billing_info:
            return {
                "organization_id": str(org_id),
                "billing_setup": False,
                "message": "Billing not set up for this organization"
            }
        
        # Get subscription tier pricing
        tier_config = get_default_features(getattr(organization, 'subscription_tier', SubscriptionTier.STARTER))
        
        return {
            "organization_id": str(org_id),
            "billing_setup": True,
            "stripe_customer_id": billing_info.get("stripe_customer_id"),
            "billing_email": billing_info.get("billing_email"),
            "payment_method_id": billing_info.get("payment_method_id"),
            "billing_address": billing_info.get("billing_address", {}),
            "setup_date": billing_info.get("setup_date"),
            "status": billing_info.get("status", "inactive"),
            "current_subscription": {
                "tier": str(getattr(organization, 'subscription_tier', '')),
                "status": str(getattr(organization, 'subscription_status', '')),
                "trial_end_date": format_datetime(getattr(organization, 'trial_end_date', None))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get billing info for {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get billing information: {str(e)}"
        )


@router.post("/organizations/{org_id}/billing/invoice")
async def create_invoice(
    org_id: uuid.UUID,
    invoice_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """Create an invoice for an organization."""
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Simulate invoice creation
        invoice_id = f"inv_{uuid.uuid4().hex[:16]}"
        amount = invoice_data.get("amount", 0)
        description = invoice_data.get("description", f"Subscription for {getattr(organization, 'name', 'Organization')}")
        
        invoice_info = {
            "invoice_id": invoice_id,
            "amount": amount,
            "currency": "usd",
            "description": description,
            "status": "pending",
            "created_date": datetime.utcnow().isoformat(),
            "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "organization_id": str(org_id)
        }
        
        # Store invoice in organization metadata
        current_metadata = getattr(organization, 'metadata', None) or {}
        if "invoices" not in current_metadata:
            current_metadata["invoices"] = []
        current_metadata["invoices"].append(invoice_info)
        setattr(organization, 'metadata', current_metadata)
        
        db.commit()
        
        # Schedule background task for invoice processing
        background_tasks.add_task(process_invoice, org_id, invoice_id)
        
        logger.info(f"Created invoice {invoice_id} for organization {org_id}")
        
        return {
            "message": "Invoice created successfully",
            "invoice_id": invoice_id,
            "organization_id": str(org_id),
            "amount": amount,
            "status": "pending",
            "due_date": invoice_info["due_date"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create invoice for {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}"
        )


# ==================== BULK OPERATIONS API ====================

@router.post("/organizations/bulk/features")
async def bulk_update_features(
    feature_updates: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin = Depends(get_admin_user_compatible)
):
    """Bulk update features for multiple organizations."""
    try:
        org_ids = feature_updates.get("organization_ids", [])
        features = feature_updates.get("features", {})
        
        if not org_ids or not features:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Organization IDs and features are required"
            )
        
        results = {
            "successful_updates": [],
            "failed_updates": [],
            "total_organizations": len(org_ids),
            "updated_features": features
        }
        
        for org_id_str in org_ids:
            try:
                org_id = uuid.UUID(org_id_str)
                organization = db.query(Organization).filter(Organization.id == org_id).first()
                
                if not organization:
                    results["failed_updates"].append({
                        "organization_id": org_id_str,
                        "error": "Organization not found"
                    })
                    continue
                
                # Update features for this organization
                current_features = getattr(organization, 'features_enabled', None) or {}
                
                for feature_name, enabled in features.items():
                    # Check if feature is allowed for this tier
                    allowed_features = get_allowed_features_for_tier(getattr(organization, 'subscription_tier', SubscriptionTier.STARTER))
                    if feature_name in allowed_features:
                        current_features[feature_name] = enabled
                
                setattr(organization, 'features_enabled', current_features)
                setattr(organization, 'updated_at', datetime.utcnow())
                
                results["successful_updates"].append({
                    "organization_id": org_id_str,
                    "organization_name": str(getattr(organization, 'name', '')),
                    "updated_features": current_features
                })
                
            except Exception as org_error:
                results["failed_updates"].append({
                    "organization_id": org_id_str,
                    "error": str(org_error)
                })
                logger.error(f"Failed to update features for organization {org_id_str}: {org_error}")
        
        db.commit()
        
        # Schedule background task for feature propagation
        background_tasks.add_task(propagate_feature_changes, results["successful_updates"])
        
        logger.info(f"Bulk feature update completed: {len(results['successful_updates'])} successful, {len(results['failed_updates'])} failed")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed bulk feature update: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed bulk feature update: {str(e)}"
        )


# ==================== HELPER FUNCTIONS FOR NEW ENDPOINTS ====================

def check_email_verified(organization) -> bool:
    """Check if organization email is verified."""
    # TODO: Implement actual email verification check
    return True  # Placeholder


def check_organization_setup_complete(organization) -> bool:
    """Check if basic organization setup is complete."""
    required_fields = ['name', 'primary_contact_email', 'industry']
    return all(getattr(organization, field, None) for field in required_fields)


def check_payment_setup_complete(organization) -> bool:
    """Check if payment setup is complete."""
    metadata = getattr(organization, 'metadata', None) or {}
    billing_info = metadata.get("billing", {})
    return bool(billing_info.get("payment_method_id"))


def get_next_onboarding_step(steps: Dict[str, bool]) -> str:
    """Get the next incomplete onboarding step."""
    step_order = [
        "registration", "email_verification", "organization_setup",
        "subscription_selection", "payment_setup", "team_invitation",
        "initial_configuration"
    ]
    
    for step in step_order:
        if not steps.get(step, False):
            return step
    
    return "completed"


def get_onboarding_step_details(steps: Dict[str, bool]) -> Dict[str, Any]:
    """Get detailed information for each onboarding step."""
    return {
        "registration": {
            "title": "Registration",
            "description": "Organization account created",
            "completed": steps.get("registration", False)
        },
        "email_verification": {
            "title": "Email Verification",
            "description": "Verify your email address",
            "completed": steps.get("email_verification", False)
        },
        "organization_setup": {
            "title": "Organization Setup",
            "description": "Complete your organization profile",
            "completed": steps.get("organization_setup", False)
        },
        "subscription_selection": {
            "title": "Subscription Selection",
            "description": "Choose your subscription plan",
            "completed": steps.get("subscription_selection", False)
        },
        "payment_setup": {
            "title": "Payment Setup",
            "description": "Add your payment method",
            "completed": steps.get("payment_setup", False)
        },
        "team_invitation": {
            "title": "Team Invitation",
            "description": "Invite your team members",
            "completed": steps.get("team_invitation", False)
        },
        "initial_configuration": {
            "title": "Initial Configuration",
            "description": "Configure features and branding",
            "completed": steps.get("initial_configuration", False)
        }
    }


def estimate_onboarding_completion_time(steps: Dict[str, bool]) -> int:
    """Estimate remaining onboarding time in minutes."""
    step_times = {
        "registration": 0,      # Already completed
        "email_verification": 2,
        "organization_setup": 5,
        "subscription_selection": 3,
        "payment_setup": 4,
        "team_invitation": 3,
        "initial_configuration": 8
    }
    
    remaining_time = sum(
        time for step, time in step_times.items()
        if not steps.get(step, False)
    )
    
    return remaining_time


def get_allowed_features_for_tier(tier: SubscriptionTier) -> List[str]:
    """Get list of allowed features for a tier."""
    tier_config = get_default_features(tier)
    return [feature for feature, enabled in tier_config.items() if enabled]


# ==================== BACKGROUND TASKS ====================

async def verify_billing_setup(org_id: uuid.UUID, stripe_customer_id: str):
    """Background task to verify billing setup."""
    logger.info(f"Verifying billing setup for organization {org_id} with Stripe customer {stripe_customer_id}")
    # TODO: Implement actual Stripe verification


async def process_invoice(org_id: uuid.UUID, invoice_id: str):
    """Background task to process invoice."""
    logger.info(f"Processing invoice {invoice_id} for organization {org_id}")
    # TODO: Implement actual invoice processing


# ==================== ORGANIZATION ANALYTICS ENDPOINTS ====================

@router.get("/organizations/{org_id}/analytics/usage", response_model=RealTimeUsageMetrics)
async def get_organization_usage_metrics(
    org_id: str,
    time_range: MetricTimeRange = Query(MetricTimeRange.LAST_30_DAYS, description="Time range for metrics"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for custom range"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for custom range"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user_compatible)
):
    """
    Get real-time usage metrics for an organization.
    
    Provides comprehensive usage analytics including:
    - Total sessions and listening time
    - Unique active users
    - Average session duration
    - Most popular content
    - Daily usage trends
    """
    try:
        analytics_service = OrganizationAnalyticsService(db)
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        if start_date:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        usage_metrics = await analytics_service.get_real_time_usage_metrics(
            organization_id=org_id,
            time_range=time_range,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return usage_metrics
        
    except ValueError as e:
        logger.error(f"Invalid parameters for usage metrics: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting usage metrics for organization {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage metrics"
        )


@router.get("/organizations/{org_id}/analytics/engagement", response_model=UserEngagementAnalyticsResponse)
async def get_organization_engagement_analytics(
    org_id: str,
    time_range: MetricTimeRange = Query(MetricTimeRange.LAST_30_DAYS, description="Time range for analytics"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for custom range"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for custom range"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user_compatible)
):
    """
    Get user engagement analytics for an organization.
    
    Provides detailed engagement analysis including:
    - User engagement distribution across levels
    - Top engaged users with detailed metrics  
    - Engagement trends over time
    - Actionable recommendations for improvement
    """
    try:
        analytics_service = OrganizationAnalyticsService(db)
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        if start_date:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        engagement_analytics = await analytics_service.get_user_engagement_analytics(
            organization_id=org_id,
            time_range=time_range,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return engagement_analytics
        
    except ValueError as e:
        logger.error(f"Invalid parameters for engagement analytics: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting engagement analytics for organization {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engagement analytics"
        )


@router.get("/organizations/{org_id}/analytics/revenue", response_model=RevenueAttributionResponse)
async def get_organization_revenue_analytics(
    org_id: str,
    time_range: MetricTimeRange = Query(MetricTimeRange.LAST_30_DAYS, description="Time range for revenue analysis"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for custom range"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for custom range"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user_compatible)
):
    """
    Get revenue attribution analytics for an organization.
    
    Provides comprehensive revenue analysis including:
    - Revenue breakdown by category (subscription, usage, one-time)
    - Growth rates and trend analysis
    - Key business metrics (MRR, ARR, ARPU, CLV)
    - Revenue projections and forecasting
    """
    try:
        analytics_service = OrganizationAnalyticsService(db)
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        if start_date:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        revenue_analytics = await analytics_service.get_revenue_attribution(
            organization_id=org_id,
            time_range=time_range,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return revenue_analytics
        
    except ValueError as e:
        logger.error(f"Invalid parameters for revenue analytics: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting revenue analytics for organization {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve revenue analytics"
        )


@router.get("/organizations/{org_id}/analytics/content", response_model=ContentUsageAnalyticsResponse)
async def get_organization_content_analytics(
    org_id: str,
    time_range: MetricTimeRange = Query(MetricTimeRange.LAST_30_DAYS, description="Time range for content analysis"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for custom range"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for custom range"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user_compatible)
):
    """
    Get content usage patterns and recommendations for an organization.
    
    Provides detailed content analysis including:
    - Top performing content with detailed metrics
    - Content category performance breakdown
    - Underutilized content identification
    - Personalized content recommendations
    - Content diversity scoring and usage patterns
    """
    try:
        analytics_service = OrganizationAnalyticsService(db)
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        if start_date:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        content_analytics = await analytics_service.get_content_usage_analytics(
            organization_id=org_id,
            time_range=time_range,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return content_analytics
        
    except ValueError as e:
        logger.error(f"Invalid parameters for content analytics: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting content analytics for organization {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content analytics"
        )


@router.get("/organizations/{org_id}/analytics/health", response_model=OrganizationHealthScoreResponse)
async def get_organization_health_score(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user_compatible)
):
    """
    Get comprehensive health score for an organization.
    
    Provides detailed health analysis including:
    - Overall health score and status classification 
    - Individual health factors with weights and targets
    - Risk factors and success indicators
    - Actionable recommendations for improvement
    - Historical health trends and peer comparisons
    """
    try:
        analytics_service = OrganizationAnalyticsService(db)
        
        health_score = await analytics_service.get_organization_health_score(
            organization_id=org_id
        )
        
        return health_score
        
    except ValueError as e:
        logger.error(f"Invalid parameters for health score: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting health score for organization {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health score"
        )


@router.get("/organizations/{org_id}/analytics/comprehensive", response_model=ComprehensiveAnalyticsResponse)
async def get_comprehensive_organization_analytics(
    org_id: str,
    time_range: MetricTimeRange = Query(MetricTimeRange.LAST_30_DAYS, description="Time range for comprehensive analytics"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for custom range"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for custom range"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user_compatible)
):
    """
    Get comprehensive analytics combining all metrics for an organization.
    
    Provides complete analytics overview including:
    - Real-time usage metrics and trends
    - User engagement analytics and distribution
    - Revenue attribution and business metrics
    - Content usage patterns and recommendations
    - Organization health scoring and insights
    - Key insights and actionable recommendations
    """
    try:
        analytics_service = OrganizationAnalyticsService(db)
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        if start_date:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        comprehensive_analytics = await analytics_service.get_comprehensive_analytics(
            organization_id=org_id,
            time_range=time_range,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return comprehensive_analytics
        
    except ValueError as e:
        logger.error(f"Invalid parameters for comprehensive analytics: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting comprehensive analytics for organization {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comprehensive analytics"
        )


@router.post("/organizations/analytics/bulk", response_model=BulkAnalyticsResponse)
async def get_bulk_organization_analytics(
    filters: AnalyticsFilters,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user_compatible)
):
    """
    Get analytics summary for multiple organizations based on filters.
    
    Provides bulk analytics including:
    - Organization summaries with key metrics
    - Health scores and engagement levels
    - Revenue and user statistics
    - Platform-wide averages and benchmarks
    - Filtered results based on criteria
    """
    try:
        analytics_service = OrganizationAnalyticsService(db)
        
        bulk_analytics = await analytics_service.get_bulk_analytics(filters)
        
        return bulk_analytics
        
    except ValueError as e:
        logger.error(f"Invalid filters for bulk analytics: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting bulk analytics: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bulk analytics"
        )


async def propagate_feature_changes(successful_updates: List[Dict[str, Any]]):
    """Background task to propagate feature changes."""
    logger.info(f"Propagating feature changes to {len(successful_updates)} organizations")
    # TODO: Implement feature change propagation
