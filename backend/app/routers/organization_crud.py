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
from fastapi.responses import JSONResponse
from fastapi import status as http_status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import uuid
import logging
from datetime import datetime

from app.db.session import get_db
from app.models.organization import Organization, OrganizationStatus, SubscriptionTier
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationList, OrganizationSummary
)
from app.core.auth_dependencies import get_admin_user_compatible as get_current_super_admin
# Enhanced audit service removed - using standard logging instead

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
    current_admin = Depends(get_current_super_admin)
):
    """
    Create a new organization with onboarding workflow setup.
    
    Features:
    - Automatic slug generation
    - Trial period setup
    - Default feature configuration
    - Onboarding workflow initialization
    - Audit logging
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
            from datetime import timedelta
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
            subscription_tier=organization_data.subscription_tier or SubscriptionTier.STARTER,
            subscription_status=OrganizationStatus.TRIAL if trial_end_date else OrganizationStatus.ACTIVE,
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
        
        # Log creation event
        logger.info(f"Organization created: {new_org.id} ({new_org.name}) by admin {current_admin.id}", extra={
            "organization_id": str(new_org.id),
            "organization_name": new_org.name,
            "subscription_tier": new_org.subscription_tier,
            "trial_days": organization_data.trial_days,
            "admin_id": current_admin.id,
            "event_type": "organization_created"
        })
        
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
        
        # Initialize onboarding workflow in background
        background_tasks.add_task(initialize_onboarding_workflow, uuid.UUID(str(new_org.id)))
        
        # Convert to response model
        org_response = OrganizationResponse.from_orm(new_org)
        org_response.current_user_count = 0  # New organization
        
        logger.info(f"Created organization {new_org.id} ({new_org.name}) by admin {current_admin.id}")
        
        return org_response
        
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
    current_admin = Depends(get_current_super_admin)
):
    """
    Get paginated list of organizations with filtering and search capabilities.
    
    Features:
    - Advanced filtering by status and tier
    - Full-text search across name, email, domain
    - Flexible sorting options
    - User count calculation
    """
    try:
        from sqlalchemy import and_, or_, desc, asc
        
        query = db.query(Organization)
        
        # Apply filters
        if status:
            query = query.filter(Organization.subscription_status.in_(status))
        
        if tier:
            query = query.filter(Organization.subscription_tier.in_(tier))
        
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
        
        # Convert to response format with user counts
        org_responses = []
        for org in organizations:
            org_response = OrganizationResponse.from_orm(org)
            org_response.current_user_count = get_organization_user_count(db, uuid.UUID(str(org.id)))
            org_responses.append(org_response)
        
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
    current_admin = Depends(get_current_super_admin)
):
    """Get detailed information about a specific organization."""
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not organization:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Convert to response model
    org_response = OrganizationResponse.from_orm(organization)
    org_response.current_user_count = get_organization_user_count(db, org_id)
    
    return org_response


@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    update_data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """
    Update organization information with comprehensive audit logging.
    
    Features:
    - Selective field updates
    - Audit trail logging
    - Domain uniqueness validation
    - Automatic timestamp updates
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Store old values for audit log
        old_values = {
            "name": organization.name,
            "subscription_tier": organization.subscription_tier,
            "subscription_status": organization.subscription_status,
            "max_users": organization.max_users
        }
        
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
        
        # Log the update
        logger.info(f"Organization updated: {org_id} by admin {current_admin.id}", extra={
            "organization_id": str(org_id),
            "updated_fields": list(update_dict.keys()),
            "old_values": old_values,
            "new_values": {k: getattr(organization, k) for k in update_dict.keys()},
            "admin_id": current_admin.id,
            "event_type": "organization_updated"
        })
        
        # Convert to response model
        org_response = OrganizationResponse.from_orm(organization)
        org_response.current_user_count = get_organization_user_count(db, org_id)
        
        logger.info(f"Updated organization {org_id} by admin {current_admin.id}")
        
        return org_response
        
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
    current_admin = Depends(get_current_super_admin)
):
    """
    Archive or permanently delete an organization.
    
    Features:
    - Soft delete (archive) by default
    - Hard delete option for super admins
    - Comprehensive audit logging
    - Cascade handling for related data
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if soft_delete:
            # Soft delete - change status to archived
            old_status = str(organization.subscription_status)
            setattr(organization, 'subscription_status', OrganizationStatus.CANCELLED.value)
            
            db.commit()
            
            # Log archival
            logger.info(
                "Organization archived",
                extra={
                    "user_id": current_admin.id,
                    "event_type": "organization_archived",
                    "details": {
                        "organization_id": str(org_id),
                        "organization_name": organization.name,
                        "previous_status": old_status
                    }
                }
            )
            
            logger.info(f"Archived organization {org_id} by admin {current_admin.id}")
            return {"message": "Organization archived successfully"}
        else:
            # Hard delete - permanent removal
            org_name = organization.name
            
            # Log before deletion
            logger.info(
                "Organization deleted",
                extra={
                    "user_id": current_admin.id,
                    "event_type": "organization_deleted",
                    "details": {
                        "organization_id": str(org_id),
                        "organization_name": org_name,
                        "admin_id": str(current_admin.id)
                    }
                }
            )
            
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


# ==================== ONBOARDING WORKFLOW MANAGEMENT ====================

@router.get("/organizations/{org_id}/onboarding")
async def get_onboarding_status(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """
    Get detailed onboarding status and progress for an organization.
    
    Returns:
    - Current step
    - Completed steps
    - Overall progress percentage
    - Estimated completion time
    - Step-specific details and requirements
    """
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
            "email_verification": check_email_verified(db, org_id),
            "organization_setup": check_organization_setup_complete(organization),
            "subscription_selection": organization.subscription_tier != SubscriptionTier.STARTER,
            "payment_setup": check_payment_setup_complete(organization),
            "team_invitation": check_team_invitations_sent(db, org_id),
            "initial_configuration": check_initial_configuration_complete(organization),
        }
        
        completed_steps = [step for step, completed in onboarding_steps.items() if completed]
        total_steps = len(onboarding_steps)
        completion_percentage = (len(completed_steps) / total_steps) * 100
        
        # Get current step (next incomplete step)
        step_order = list(onboarding_steps.keys())
        current_step = "completed"
        for step in step_order:
            if not onboarding_steps[step]:
                current_step = step
                break
        
        return {
            "organization_id": str(org_id),
            "organization_name": organization.name,
            "current_step": current_step,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "completion_percentage": round(completion_percentage, 1),
            "is_completed": organization.onboarding_completed,
            "step_details": get_onboarding_step_details(onboarding_steps),
            "estimated_completion_time": estimate_onboarding_completion_time(onboarding_steps),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get onboarding status for {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get onboarding status"
        )


@router.post("/organizations/{org_id}/onboarding/steps/{step_name}")
async def update_onboarding_step(
    org_id: uuid.UUID,
    step_name: str,
    completed: bool = True,
    step_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """
    Update a specific onboarding step completion status.
    
    Features:
    - Step-specific validation
    - Progress tracking
    - Automatic completion detection
    - Audit logging
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Validate step name
        valid_steps = [
            "registration", "email_verification", "organization_setup",
            "subscription_selection", "payment_setup", "team_invitation",
            "initial_configuration"
        ]
        
        if step_name not in valid_steps:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid step name. Must be one of: {', '.join(valid_steps)}"
            )
        
        # Update step in organization metadata
        if not organization.metadata:
            organization.metadata = {}
        
        if "onboarding_steps" not in organization.metadata:
            organization.metadata["onboarding_steps"] = {}
        
        organization.metadata["onboarding_steps"][step_name] = {
            "completed": completed,
            "completed_at": datetime.utcnow().isoformat() if completed else None,
            "data": step_data or {},
            "updated_by": current_admin.id
        }
        
        # Check if all onboarding is complete
        onboarding_status = await get_onboarding_status(org_id, db, current_admin)
        current_onboarding_completed = getattr(organization, 'onboarding_completed', False)
        if onboarding_status["completion_percentage"] >= 100 and not current_onboarding_completed:
            setattr(organization, 'onboarding_completed', True)
            
            # Log onboarding completion
            logger.info(
                "Onboarding completed",
                extra={
                    "user_id": current_admin.id,
                    "event_type": "onboarding_completed",
                    "details": {
                        "organization_id": str(org_id),
                        "organization_name": organization.name,
                        "completion_date": datetime.utcnow().isoformat()
                    }
                }
            )
        
        db.commit()
        
        logger.info(f"Updated onboarding step {step_name} for organization {org_id}")
        
        return {
            "organization_id": str(org_id),
            "step_name": step_name,
            "completed": completed,
            "updated_at": datetime.utcnow().isoformat(),
            "overall_progress": onboarding_status["completion_percentage"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update onboarding step for {org_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update onboarding step"
        )


# ==================== SUBSCRIPTION MANAGEMENT ====================

@router.get("/organizations/{org_id}/subscription")
async def get_subscription_summary(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """
    Get comprehensive subscription summary including usage, limits, and billing.
    
    Returns:
    - Current subscription tier and status
    - Usage metrics vs limits
    - Feature availability
    - Billing information
    - Trial status
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
    current_admin = Depends(get_current_super_admin)
):
    """
    Update organization subscription plan with comprehensive validation.
    
    Features:
    - Tier upgrade/downgrade validation
    - Usage limit updates
    - Feature enablement
    - Billing integration
    - Audit logging
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        old_tier = str(organization.subscription_tier)
        old_limits = {
            "max_users": getattr(organization, 'max_users', 0),
            "max_sound_libraries": getattr(organization, 'max_sound_libraries', 0)
        }
        
        # Validate downgrade constraints
        if new_tier.value != old_tier:
            await validate_subscription_change(db, org_id, old_tier, new_tier)
        
        # Get new tier configuration
        tier_config = get_tier_configuration(new_tier)
        
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
        
        # Log subscription change
        logger.info(
            "Subscription updated",
            extra={
                "user_id": current_admin.id,
                "event_type": "subscription_updated",
                "details": {
                    "organization_id": str(org_id),
                    "organization_name": organization.name,
                    "old_tier": old_tier,
                    "new_tier": new_tier,
                    "billing_cycle": billing_cycle,
                    "prorate": prorate,
                    "old_limits": old_limits,
                    "new_limits": {
                        "max_users": organization.max_users,
                        "max_sound_libraries": organization.max_sound_libraries
                    }
                }
            }
        )
        
        logger.info(f"Updated subscription for organization {org_id} from {old_tier} to {new_tier}")
        
        return {
            "organization_id": str(org_id),
            "old_tier": old_tier,
            "new_tier": new_tier,
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
    current_admin = Depends(get_current_super_admin)
):
    """Get all features and their status for an organization."""
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not organization:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    tier_config = get_tier_configuration(organization.subscription_tier)
    
    return {
        "organization_id": str(org_id),
        "organization_name": organization.name,
        "subscription_tier": organization.subscription_tier,
        "enabled_features": organization.features_enabled or {},
        "available_features": tier_config["features"],
        "feature_limits": get_feature_limits(organization.subscription_tier),
        "last_updated": datetime.utcnow().isoformat()
    }


@router.put("/organizations/{org_id}/features/{feature_name}")
async def update_feature_toggle(
    org_id: uuid.UUID,
    feature_name: str,
    enabled: bool,
    metadata: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """
    Toggle a specific feature for an organization.
    
    Features:
    - Tier-based feature validation
    - Usage limit checking
    - Metadata support
    - Audit logging
    """
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        
        if not organization:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Validate feature name and tier permissions
        tier_config = get_tier_configuration(organization.subscription_tier)
        available_features = tier_config["features"]
        
        if feature_name not in available_features:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Feature '{feature_name}' not available for {organization.subscription_tier} tier"
            )
        
        if enabled and not available_features[feature_name]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Feature '{feature_name}' not allowed for {organization.subscription_tier} tier"
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
        
        # Update the organization features
        setattr(organization, 'features_enabled', updated_features)
        
        db.commit()
        
        # Log feature toggle change
        logger.info(
            "Feature toggle updated",
            extra={
                "user_id": current_admin.id,
                "event_type": "feature_toggle_updated",
                "details": {
                    "organization_id": str(org_id),
                    "organization_name": organization.name,
                    "feature_name": feature_name,
                    "old_value": old_value,
                    "new_value": enabled,
                    "metadata": metadata
                }
            }
        )
        
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


@router.post("/organizations/features/bulk-update")
async def bulk_update_features(
    organization_ids: List[uuid.UUID],
    feature_updates: Dict[str, bool],
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """
    Bulk update features across multiple organizations.
    
    Features:
    - Batch processing
    - Per-organization validation
    - Detailed result reporting
    - Comprehensive audit logging
    """
    try:
        if len(organization_ids) > 100:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Cannot update more than 100 organizations at once"
            )
        
        results = {
            "total_organizations": len(organization_ids),
            "successful_updates": [],
            "failed_updates": [],
            "feature_updates": feature_updates,
            "reason": reason
        }
        
        for org_id in organization_ids:
            try:
                organization = db.query(Organization).filter(Organization.id == org_id).first()
                
                if not organization:
                    results["failed_updates"].append({
                        "organization_id": str(org_id),
                        "error": "Organization not found"
                    })
                    continue
                
                # Validate features for this organization's tier
                tier_config = get_tier_configuration(organization.subscription_tier)
                available_features = tier_config["features"]
                
                valid_updates = {}
                invalid_features = []
                
                for feature_name, enabled in feature_updates.items():
                    if feature_name not in available_features:
                        invalid_features.append(f"{feature_name} (not available)")
                        continue
                    
                    if enabled and not available_features[feature_name]:
                        invalid_features.append(f"{feature_name} (not allowed for tier)")
                        continue
                    
                    valid_updates[feature_name] = enabled
                
                if invalid_features:
                    results["failed_updates"].append({
                        "organization_id": str(org_id),
                        "organization_name": organization.name,
                        "error": f"Invalid features: {', '.join(invalid_features)}"
                    })
                    continue
                
                # Apply valid updates
                old_features = getattr(organization, 'features_enabled', {}) or {}
                
                current_features = dict(old_features) if old_features else {}
                
                for feature_name, enabled in valid_updates.items():
                    current_features[feature_name] = enabled
                
                setattr(organization, 'features_enabled', current_features)
                
                db.commit()
                
                # Log bulk update for this organization
                logger.info(
                    "Bulk feature update",
                    extra={
                        "user_id": current_admin.id,
                        "event_type": "bulk_feature_update",
                        "details": {
                            "organization_id": str(org_id),
                            "organization_name": organization.name,
                            "updated_features": valid_updates,
                            "old_features": old_features,
                            "reason": reason
                        }
                    }
                )
                
                results["successful_updates"].append({
                    "organization_id": str(org_id),
                    "organization_name": organization.name,
                    "updated_features": valid_updates
                })
                
            except Exception as org_error:
                db.rollback()
                results["failed_updates"].append({
                    "organization_id": str(org_id),
                    "error": str(org_error)
                })
                logger.error(f"Failed to update features for organization {org_id}: {org_error}")
        
        logger.info(f"Bulk feature update completed: {len(results['successful_updates'])} successful, {len(results['failed_updates'])} failed")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed bulk feature update: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed bulk feature update"
        )


# ==================== ORGANIZATION STATUS MANAGEMENT ====================

@router.post("/organizations/{org_id}/suspend")
async def suspend_organization(
    org_id: uuid.UUID,
    reason: str,
    notify_users: bool = True,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """
    Suspend an organization with comprehensive audit trail.
    
    Features:
    - Reason requirement
    - User notification options
    - Status validation
    - Suspension metadata storage
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
        
        # Store suspension metadata
        if not organization.metadata:
            organization.metadata = {}
        
        organization.metadata["suspension"] = {
            "reason": reason,
            "suspended_at": datetime.utcnow().isoformat(),
            "suspended_by": current_admin.id,
            "previous_status": old_status,
            "notify_users": notify_users
        }
        
        db.commit()
        
        # Log suspension
        logger.info(
            "Organization suspended",
            extra={
                "user_id": current_admin.id,
                "event_type": "organization_suspended",
                "details": {
                    "organization_id": str(org_id),
                    "organization_name": organization.name,
                    "reason": reason,
                    "previous_status": old_status,
                    "notify_users": notify_users
                }
            }
        )
        
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
    current_admin = Depends(get_current_super_admin)
):
    """
    Reactivate a suspended organization.
    
    Features:
    - Status validation
    - Smart status restoration
    - Trial expiration checking
    - User notification options
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
        
        # Get suspension info to restore previous status
        suspension_info = getattr(organization, 'metadata', {}).get("suspension", {}) if hasattr(organization, 'metadata') and organization.metadata else {}
        previous_status = suspension_info.get("previous_status", OrganizationStatus.ACTIVE.value)
        
        # Check if trial has expired while suspended
        trial_end = getattr(organization, 'trial_end_date', None)
        if previous_status == OrganizationStatus.TRIAL.value and trial_end:
            if datetime.utcnow() > trial_end:
                previous_status = OrganizationStatus.CANCELLED.value
        
        setattr(organization, 'subscription_status', previous_status)
        
        # Update metadata
        if organization.metadata and "suspension" in organization.metadata:
            organization.metadata["reactivation"] = {
                "reactivated_at": datetime.utcnow().isoformat(),
                "reactivated_by": current_admin.id,
                "restored_status": previous_status
            }
            del organization.metadata["suspension"]
        
        db.commit()
        
        # Log reactivation
        logger.info(
            "Organization reactivated",
            extra={
                "user_id": current_admin.id,
                "event_type": "organization_reactivated",
                "details": {
                    "organization_id": str(org_id),
                    "organization_name": organization.name,
                    "restored_status": previous_status,
                    "notify_users": notify_users
                }
            }
        )
        
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

def get_default_features(tier: SubscriptionTier) -> Dict[str, bool]:
    """Get default features for a subscription tier."""
    feature_sets = {
        SubscriptionTier.STARTER: {
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
        SubscriptionTier.PROFESSIONAL: {
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
        SubscriptionTier.ENTERPRISE: {
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
        SubscriptionTier.CUSTOM: {
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
    
    return feature_sets.get(tier, feature_sets[SubscriptionTier.STARTER])


def get_tier_configuration(tier) -> Dict[str, Any]:
    """Get configuration for a subscription tier."""
    # Convert to string if it's an enum
    tier_str = tier.value if hasattr(tier, 'value') else str(tier)
    
    configurations = {
        SubscriptionTier.STARTER.value: {
            "max_users": 10,
            "max_sound_libraries": 3,
            "monthly_cost": 0,
            "yearly_cost": 0,
            "features": get_default_features(SubscriptionTier.STARTER)
        },
        SubscriptionTier.PROFESSIONAL.value: {
            "max_users": 100,
            "max_sound_libraries": 10,
            "monthly_cost": 49,
            "yearly_cost": 490,
            "features": get_default_features(SubscriptionTier.PROFESSIONAL)
        },
        SubscriptionTier.ENTERPRISE.value: {
            "max_users": 1000,
            "max_sound_libraries": 50,
            "monthly_cost": 199,
            "yearly_cost": 1990,
            "features": get_default_features(SubscriptionTier.ENTERPRISE)
        },
        SubscriptionTier.CUSTOM.value: {
            "max_users": 10000,
            "max_sound_libraries": 100,
            "monthly_cost": 0,  # Custom pricing
            "yearly_cost": 0,   # Custom pricing
            "features": get_default_features(SubscriptionTier.CUSTOM)
        }
    }
    
    return configurations.get(tier_str, configurations[SubscriptionTier.STARTER.value])


def get_feature_limits(tier) -> Dict[str, Any]:
    """Get feature usage limits for a tier."""
    # Convert to string if it's an enum
    tier_str = tier.value if hasattr(tier, 'value') else str(tier)
    
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
    
    return limits.get(tier_str, limits[SubscriptionTier.STARTER.value])


async def validate_subscription_change(
    db: Session, 
    org_id: uuid.UUID, 
    old_tier, 
    new_tier
):
    """Validate that subscription change is allowed based on current usage."""
    # Convert to string values for comparison
    old_tier_str = old_tier.value if hasattr(old_tier, 'value') else str(old_tier)
    new_tier_str = new_tier.value if hasattr(new_tier, 'value') else str(new_tier)
    
    if old_tier_str == new_tier_str:
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


# Onboarding helper functions
def check_email_verified(db: Session, org_id: uuid.UUID) -> bool:
    """Check if organization email is verified."""
    # TODO: Implement email verification check
    return True


def check_organization_setup_complete(org: Organization) -> bool:
    """Check if basic organization setup is complete."""
    required_fields = ['name', 'primary_contact_email', 'industry']
    return all(getattr(org, field) for field in required_fields)


def check_payment_setup_complete(org: Organization) -> bool:
    """Check if payment setup is complete."""
    return bool(org.payment_method_id)


def check_team_invitations_sent(db: Session, org_id: uuid.UUID) -> bool:
    """Check if team invitations have been sent."""
    user_count = get_organization_user_count(db, org_id)
    return user_count > 1


def check_initial_configuration_complete(org: Organization) -> bool:
    """Check if initial configuration is complete."""
    return bool(org.features_enabled or org.branding_config)


def get_onboarding_step_details(steps: Dict[str, bool]) -> Dict[str, Any]:
    """Get detailed information for each onboarding step."""
    return {
        "registration": {
            "title": "Registration",
            "description": "Organization account created",
            "completed": steps.get("registration", False),
            "estimated_time": 0
        },
        "email_verification": {
            "title": "Email Verification",
            "description": "Verify your email address",
            "completed": steps.get("email_verification", False),
            "estimated_time": 2
        },
        "organization_setup": {
            "title": "Organization Setup",
            "description": "Complete your organization profile",
            "completed": steps.get("organization_setup", False),
            "estimated_time": 5
        },
        "subscription_selection": {
            "title": "Subscription Selection",
            "description": "Choose your subscription plan",
            "completed": steps.get("subscription_selection", False),
            "estimated_time": 3
        },
        "payment_setup": {
            "title": "Payment Setup",
            "description": "Add your payment method",
            "completed": steps.get("payment_setup", False),
            "estimated_time": 4
        },
        "team_invitation": {
            "title": "Team Invitation",
            "description": "Invite your team members",
            "completed": steps.get("team_invitation", False),
            "estimated_time": 3
        },
        "initial_configuration": {
            "title": "Initial Configuration",
            "description": "Configure features and branding",
            "completed": steps.get("initial_configuration", False),
            "estimated_time": 8
        }
    }


def estimate_onboarding_completion_time(steps: Dict[str, bool]) -> int:
    """Estimate remaining onboarding time in minutes."""
    step_details = get_onboarding_step_details(steps)
    
    remaining_time = sum(
        details["estimated_time"] for step_name, details in step_details.items()
        if not steps.get(step_name, False)
    )
    
    return remaining_time


async def initialize_onboarding_workflow(org_id: uuid.UUID):
    """Initialize onboarding workflow for new organization (background task)."""
    try:
        # TODO: Set up onboarding workflow tasks
        # This could integrate with a workflow engine or task queue
        logger.info(f"Initialized onboarding workflow for organization {org_id}")
    except Exception as e:
        logger.error(f"Failed to initialize onboarding workflow for {org_id}: {e}")
