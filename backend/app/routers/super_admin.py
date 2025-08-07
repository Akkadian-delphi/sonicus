"""
Super Admin API endpoints for platform-level organization management.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import uuid

from app.core.security import get_current_user
from app.core.auth_middleware import require_super_admin
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationStatus, SubscriptionTier
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationSummary, OrganizationHealthCheck
)
from app.db.session import get_db, SessionLocal
from app.services.organization_db_service import OrganizationDatabaseService
from app.db.b2b2c_session import B2B2CSessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/super-admin", tags=["super-admin"])

# Initialize services
organization_db_service = OrganizationDatabaseService()
b2b2c_session_manager = B2B2CSessionManager()


def get_master_db():
    """Get master database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_super_admin(current_user: User):
    """Check if user is Super Admin."""
    if getattr(current_user, 'role') != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required"
        )


@router.post("/organizations", response_model=OrganizationResponse)
@require_super_admin
async def create_organization(
    organization_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_master_db)
):
    """
    Create a new organization (Super Admin only).
    """
    try:
        logger.info(f"Super admin {getattr(current_user, 'email')} creating organization: {organization_data.name}")
        
        # Check if organization domain already exists
        existing_org = db.query(Organization).filter(
            Organization.domain == organization_data.domain
        ).first()
        
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization with domain {organization_data.domain} already exists"
            )
        
        # Create organization
        organization = Organization(
            id=uuid.uuid4(),
            name=organization_data.name,
            domain=organization_data.domain,
            subscription_tier=organization_data.subscription_tier,
            subscription_status=OrganizationStatus.TRIAL,
            max_users=organization_data.max_users,
            primary_contact_email=organization_data.primary_contact_email,
            trial_end_date=datetime.utcnow() + timedelta(days=14),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(organization)
        db.commit()
        db.refresh(organization)
        
        # Create organization database
        await organization_db_service.create_organization_database(organization)
        
        logger.info(f"Organization {organization.name} created successfully with ID: {organization.id}")
        
        # Send webhook for organization creation
        try:
            from app.services.webhook_service import webhook_service
            
            webhook_data = {
                "id": organization.id,
                "name": organization.name,
                "display_name": getattr(organization, 'display_name', organization.name),
                "domain": organization.domain,
                "primary_contact_email": organization.primary_contact_email,
                "subscription_tier": organization.subscription_tier,
                "subscription_status": organization.subscription_status,
                "max_users": organization.max_users,
                "industry": getattr(organization, 'industry', None),
                "company_size": getattr(organization, 'company_size', None),
                "created_at": organization.created_at,
                "trial_end_date": organization.trial_end_date
            }
            
            # Send webhook asynchronously (fire and forget)
            asyncio.create_task(
                webhook_service.send_organization_created_webhook(webhook_data, db)
            )
            
        except Exception as webhook_error:
            # Don't fail the organization creation if webhook fails
            logger.error(f"Failed to send organization creation webhook: {webhook_error}")
        
        return OrganizationResponse.from_orm(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating organization"
        )


@router.get("/organizations")
@require_super_admin
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_master_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_filter: Optional[OrganizationStatus] = Query(None, description="Filter by subscription status"),
    tier: Optional[SubscriptionTier] = Query(None, description="Filter by subscription tier"),
    search: Optional[str] = Query(None, description="Search by organization name or domain")
):
    """List all organizations with filtering and pagination (Super Admin only)."""
    try:
        logger.info(f"Super admin {getattr(current_user, 'email')} listing organizations")
        
        query = db.query(Organization)
        
        # Apply filters
        if status_filter:
            query = query.filter(Organization.subscription_status == status_filter)
        if tier:
            query = query.filter(Organization.subscription_tier == tier)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Organization.name.ilike(search_pattern)) |
                (Organization.domain.ilike(search_pattern)) |
                (Organization.primary_contact_email.ilike(search_pattern))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        organizations = query.order_by(Organization.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "organizations": [OrganizationResponse.from_orm(org) for org in organizations],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while listing organizations"
        )


@router.get("/organizations/{organization_id}", response_model=OrganizationResponse)
@require_super_admin
async def get_organization(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_master_db)
):
    """Get a specific organization by ID (Super Admin only)."""
    try:
        logger.info(f"Super admin {getattr(current_user, 'email')} getting organization: {organization_id}")
        
        # Validate UUID format
        try:
            uuid.UUID(organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization ID format"
            )
        
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return OrganizationResponse.from_orm(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting organization"
        )


@router.put("/organizations/{organization_id}", response_model=OrganizationResponse)
@require_super_admin
async def update_organization(
    organization_id: str,
    organization_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_master_db)
):
    """Update an organization (Super Admin only)."""
    try:
        logger.info(f"Super admin {getattr(current_user, 'email')} updating organization: {organization_id}")
        
        # Validate UUID format
        try:
            uuid.UUID(organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization ID format"
            )
        
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Update fields
        update_data = organization_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(organization, field, value)
        
        # Always update the timestamp
        setattr(organization, 'updated_at', datetime.utcnow())
        
        db.commit()
        db.refresh(organization)
        
        logger.info(f"Organization {organization_id} updated successfully")
        
        return OrganizationResponse.from_orm(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization {organization_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating organization"
        )


@router.delete("/organizations/{organization_id}")
@require_super_admin
async def delete_organization(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_master_db)
):
    """Delete an organization and its database (Super Admin only)."""
    try:
        logger.info(f"Super admin {getattr(current_user, 'email')} deleting organization: {organization_id}")
        
        # Validate UUID format
        try:
            uuid.UUID(organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization ID format"
            )
        
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Check if organization can be deleted (no active users, etc.)
        active_users_count = db.query(func.count(User.id)).filter(
            User.organization_id == organization_id
        ).scalar()
        
        if active_users_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete organization with {active_users_count} active users"
            )
        
        # TODO: Drop organization database
        # await organization_db_service.drop_organization_database(organization_id)
        logger.warning(f"Database cleanup for organization {organization_id} needs to be implemented")
        
        # Update organization status to cancelled before deletion
        setattr(organization, 'subscription_status', OrganizationStatus.CANCELLED)
        setattr(organization, 'updated_at', datetime.utcnow())
        db.commit()
        
        # Actually delete the organization
        db.delete(organization)
        db.commit()
        
        logger.info(f"Organization {organization_id} deleted successfully")
        
        return {"message": "Organization deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization {organization_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting organization"
        )


@router.get("/organizations/{organization_id}/health", response_model=OrganizationHealthCheck)
@require_super_admin
async def get_organization_health(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_master_db)
):
    """Get health check for a specific organization (Super Admin only)."""
    try:
        logger.info(f"Super admin {getattr(current_user, 'email')} checking health for organization: {organization_id}")
        
        # Validate UUID format
        try:
            uuid.UUID(organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization ID format"
            )
        
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get organization-specific database session
        org_db = b2b2c_session_manager.get_organization_session(organization_id)
        
        try:
            # Test database connection
            org_db.execute(text("SELECT 1"))
            connection_test = True
            database_status = "healthy"
            issues = []
            
            # Get database size (simplified)
            database_size = "unknown"
            
        except Exception as db_error:
            connection_test = False
            database_status = "offline"
            issues = [f"Database connection failed: {str(db_error)}"]
            database_size = "unknown"
        finally:
            org_db.close()
        
        return OrganizationHealthCheck(
            organization_id=uuid.UUID(organization_id),
            organization_name=getattr(organization, 'name'),
            database_status=database_status,
            database_size=database_size,
            connection_test=connection_test,
            last_backup=None,  # Would need backup service integration
            issues=issues,
            checked_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics for organization {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting organization analytics"
        )


@router.get("/platform-stats")
@require_super_admin
async def get_platform_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_master_db)
):
    """Get platform-wide statistics (Super Admin only)."""
    try:
        logger.info(f"Super admin {getattr(current_user, 'email')} getting platform stats")
        
        # Get organization counts by status
        org_stats = db.query(
            Organization.subscription_status,
            func.count(Organization.id).label('count')
        ).group_by(Organization.subscription_status).all()
        
        # Get all organizations for detailed analytics
        organizations = db.query(Organization).all()
        
        # Calculate totals across all organizations
        total_users = 0
        total_active_users = 0
        
        for organization in organizations:
            try:
                org_db = organization_db_service.get_organization_database_session(str(organization.id))
                org_user_count = org_db.query(func.count(User.id)).scalar() or 0
                org_active_count = org_db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
                
                total_users += org_user_count
                total_active_users += org_active_count
                
                org_db.close()
            except Exception as e:
                logger.warning(f"Could not get stats for organization {organization.id}: {e}")
                continue
        
        return {
            "total_organizations": len(organizations),
            "organizations_by_status": {stat.subscription_status: stat.count for stat in org_stats},
            "total_users_across_platform": total_users,
            "total_active_users": total_active_users,
            "platform_health": {
                "database_connections": "healthy",
                "system_status": "operational"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting platform stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting platform statistics"
        )
