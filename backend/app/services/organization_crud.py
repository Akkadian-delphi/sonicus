"""
Fixed Organization Management Service

This service provides complete CRUD operations for organizations.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from fastapi import HTTPException, status

from app.models.organization import (
    Organization, OrganizationStatus, SubscriptionTier,
    OrganizationSoundPackage, OrganizationAnalytics
)
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationList, OrganizationSummary
)
from app.core.config import settings
from app.core.cache import redis_client

logger = logging.getLogger(__name__)


class OrganizationCRUDService:
    """Organization CRUD operations service"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_organization(
        self, 
        org_data: OrganizationCreate,
        created_by_user_id: Optional[int] = None
    ) -> Organization:
        """Create a new organization."""
        try:
            # Generate unique slug from name
            slug = self._generate_unique_slug(org_data.name)
            
            # Calculate trial end date
            trial_end_date = None
            if org_data.trial_days and org_data.trial_days > 0:
                trial_end_date = datetime.utcnow() + timedelta(days=org_data.trial_days)
            
            # Create organization record
            org = Organization(
                id=uuid.uuid4(),
                name=org_data.name,
                display_name=org_data.display_name or org_data.name,
                domain=org_data.domain,
                primary_contact_email=org_data.primary_contact_email,
                phone=org_data.phone,
                address_line1=org_data.address_line1,
                address_line2=org_data.address_line2,
                city=org_data.city,
                state=org_data.state,
                country=org_data.country,
                postal_code=org_data.postal_code,
                industry=org_data.industry,
                company_size=org_data.company_size,
                subscription_tier=org_data.subscription_tier or SubscriptionTier.STARTER,
                subscription_status=OrganizationStatus.TRIAL if trial_end_date else OrganizationStatus.ACTIVE,
                max_users=org_data.max_users or 10,
                max_sound_libraries=org_data.max_sound_libraries or 3,
                trial_end_date=trial_end_date,
                features_enabled=self._get_default_features(org_data.subscription_tier or SubscriptionTier.STARTER),
                branding_config=org_data.branding_config or {},
                created_by_user_id=created_by_user_id,
                onboarding_completed=False,
                database_created=False
            )
            
            self.db.add(org)
            self.db.commit()
            self.db.refresh(org)
            
            # Initialize workflows
            self._initialize_onboarding_workflow(str(org.id))
            self._create_default_sound_packages(str(org.id))
            
            # Log organization creation
            self._log_organization_event(
                str(org.id), 
                "organization_created",
                old_values={},
                new_values={"id": str(org.id), "name": org.name},
                user_id=created_by_user_id
            )
            
            logger.info(f"Created organization {org.id} ({org.name}) by user {created_by_user_id}")
            return org
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create organization: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create organization: {str(e)}"
            )
    
    def get_organization(self, org_id: uuid.UUID) -> Optional[Organization]:
        """Get organization by ID"""
        return self.db.query(Organization).filter(Organization.id == org_id).first()
    
    def get_organization_by_domain(self, domain: str) -> Optional[Organization]:
        """Get organization by domain"""
        return self.db.query(Organization).filter(Organization.domain == domain).first()
    
    def update_organization(
        self,
        org_id: uuid.UUID,
        update_data: OrganizationUpdate,
        updated_by_user_id: Optional[int] = None
    ) -> Organization:
        """Update organization with audit logging."""
        try:
            org = self.get_organization(org_id)
            if not org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
            
            # Store old values for audit log
            old_values = {"id": str(org.id), "name": getattr(org, 'name', '')}
            
            # Apply updates
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(org, field):
                    setattr(org, field, value)
            
            setattr(org, 'updated_at', datetime.utcnow())
            
            self.db.commit()
            self.db.refresh(org)
            
            # Log the update
            self._log_organization_event(
                str(org_id),
                "organization_updated",
                old_values=old_values,
                new_values={"id": str(org.id), "name": getattr(org, 'name', '')},
                user_id=updated_by_user_id
            )
            
            logger.info(f"Updated organization {org_id} by user {updated_by_user_id}")
            return org
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update organization {org_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update organization: {str(e)}"
            )
    
    def delete_organization(
        self,
        org_id: uuid.UUID,
        deleted_by_user_id: Optional[int] = None,
        soft_delete: bool = True
    ) -> bool:
        """Delete organization (soft delete by default)."""
        try:
            org = self.get_organization(org_id)
            if not org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
            
            if soft_delete:
                # Soft delete - change status to archived
                old_values = {"id": str(org.id), "status": str(getattr(org, 'subscription_status', ''))}
                
                setattr(org, 'subscription_status', OrganizationStatus.CANCELLED)
                setattr(org, 'updated_at', datetime.utcnow())
                
                self.db.commit()
                
                # Log the archival
                self._log_organization_event(
                    str(org_id),
                    "organization_archived",
                    old_values=old_values,
                    new_values={"status": "archived"},
                    user_id=deleted_by_user_id
                )
                
                logger.info(f"Archived organization {org_id} by user {deleted_by_user_id}")
            else:
                # Hard delete - remove from database
                self._log_organization_event(
                    str(org_id),
                    "organization_deleted",
                    old_values={"id": str(org.id)},
                    new_values={},
                    user_id=deleted_by_user_id
                )
                
                self.db.delete(org)
                self.db.commit()
                
                logger.info(f"Permanently deleted organization {org_id} by user {deleted_by_user_id}")
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete organization {org_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete organization: {str(e)}"
            )

    # ==================== HELPER METHODS ====================
    
    def _generate_unique_slug(self, name: str) -> str:
        """Generate unique slug from organization name"""
        import re
        base_slug = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower()).strip('-')
        base_slug = re.sub(r'-+', '-', base_slug)  # Remove multiple consecutive hyphens
        
        # Check if slug exists
        counter = 1
        slug = base_slug
        while self.db.query(Organization).filter(Organization.domain == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def _get_default_features(self, tier: SubscriptionTier) -> Dict[str, bool]:
        """Get default features for a subscription tier"""
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
    
    def _initialize_onboarding_workflow(self, org_id: str) -> None:
        """Initialize onboarding workflow for new organization"""
        # TODO: Set up onboarding workflow tasks
        pass
    
    def _create_default_sound_packages(self, org_id: str) -> None:
        """Create default sound packages for new organization"""
        try:
            default_packages = [
                {
                    "package_name": "Welcome Package",
                    "description": "A curated selection of calming sounds to get started",
                    "category": "wellness",
                    "sound_ids": [],  # TODO: Add default sound IDs
                    "auto_assign_new_users": True
                }
            ]
            
            for package_data in default_packages:
                package = OrganizationSoundPackage(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    **package_data
                )
                self.db.add(package)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create default sound packages for {org_id}: {e}")
    
    def _log_organization_event(
        self,
        org_id: str,
        event_type: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log organization events for audit trail"""
        try:
            event_data = {
                "organization_id": str(org_id),
                "event_type": event_type,
                "old_values": old_values,
                "new_values": new_values,
                "user_id": user_id,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in cache for now (could be moved to database table)
            cache_key = f"org_audit:{org_id}:{datetime.utcnow().timestamp()}"
            redis_client.set_json(cache_key, event_data, expire=86400 * 30)  # 30 days
            
        except Exception as e:
            logger.error(f"Failed to log organization event: {e}")
    
    def _get_user_count(self, org_id: uuid.UUID) -> int:
        """Get current user count for organization"""
        try:
            from app.models.user import User
            return self.db.query(User).filter(User.organization_id == org_id).count()
        except Exception:
            return 0
