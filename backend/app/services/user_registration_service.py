"""
Enhanced User Registration Service
Integrates local database registration with Authentik user creation
"""

import logging
import uuid
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext

from app.models.user import User, UserRole
from app.models.organization import Organization, SubscriptionTier, OrganizationStatus
from app.services.authentik_service import authentik_service, create_organization_admin

logger = logging.getLogger(__name__)

# Configure password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRegistrationService:
    """Service for handling user registration with dual database support"""
    
    @staticmethod
    async def register_organization_user(
        user_data: Dict[str, Any], 
        db: Session,
        create_in_authentik: bool = True
    ) -> Tuple[User, Organization, Optional[Dict]]:
        """
        Register a new organization and business admin user
        Creates user in both local database and Authentik (if configured)
        
        Args:
            user_data: User registration data
            db: Database session
            create_in_authentik: Whether to create user in Authentik
        
        Returns:
            Tuple of (User, Organization, Authentik user data or None)
        """
        
        # Validate required fields
        email = user_data.get('email')
        password = user_data.get('password')
        company_name = user_data.get('company_name')
        
        if not all([email, password, company_name]):
            raise HTTPException(
                status_code=400,
                detail="Email, password, and company name are required"
            )
        
        # Check if user already exists locally
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Create organization first
        logger.info(f"Creating organization: {company_name}")
        organization = UserRegistrationService._create_organization(user_data, db)
        
        # Create local user
        logger.info(f"Creating local user: {email}")
        local_user = UserRegistrationService._create_local_user(
            user_data, str(organization.id), db
        )
        
        # Create user in Authentik if enabled and configured
        authentik_user = None
        if create_in_authentik and authentik_service.is_configured():
            try:
                logger.info(f"Creating Authentik user: {email}")
                authentik_user = await create_organization_admin(
                    email=str(email),
                    name=user_data.get('name', str(email).split('@')[0]),
                    company_name=str(company_name),
                    password=password
                )
                
                if authentik_user:
                    # Store Authentik user ID in local user record
                    setattr(local_user, 'authentik_user_id', authentik_user.get('pk'))
                    db.commit()
                    logger.info(f"Successfully linked local user with Authentik user PK: {authentik_user.get('pk')}")
                
            except Exception as e:
                logger.error(f"Failed to create user in Authentik: {e}")
                # Don't fail the entire registration if Authentik creation fails
                # User can still use JWT authentication
                logger.warning(f"Registration completed with local database only. User can use JWT authentication.")
        
        else:
            logger.info("Authentik user creation skipped (disabled or not configured)")
        
        # Log successful registration
        logger.info(f"User registration completed - Local: ✓, Authentik: {'✓' if authentik_user else '✗'}")
        
        return local_user, organization, authentik_user
    
    @staticmethod
    def _create_organization(user_data: Dict[str, Any], db: Session) -> Organization:
        """Create organization in local database"""
        
        organization_id = uuid.uuid4()
        company_domain = user_data['company_name'].lower().replace(' ', '').replace('-', '') + ".sonicus.local"
        
        new_organization = Organization(
            id=organization_id,
            name=user_data['company_name'],
            display_name=user_data['company_name'],
            domain=company_domain,
            primary_contact_email=user_data['email'],
            country=user_data.get('country'),
            industry=user_data.get('business_type'),
            subscription_tier=SubscriptionTier.STARTER,
            subscription_status=OrganizationStatus.TRIAL,
            max_users=10,  # Default starter limits
            max_sound_libraries=3,
            onboarding_completed=False
        )
        
        db.add(new_organization)
        db.flush()  # Ensure organization is created before user
        
        return new_organization
    
    @staticmethod
    def _create_local_user(
        user_data: Dict[str, Any], 
        organization_id: str,  # Change to string for now
        db: Session
    ) -> User:
        """Create user in local database"""
        
        # Hash password
        hashed_password = pwd_context.hash(user_data['password'])
        
        new_user = User(
            email=user_data['email'],
            hashed_password=hashed_password,
            telephone=user_data.get('telephone'),
            preferred_payment_method=user_data.get('preferred_payment_method'),
            company_name=user_data['company_name'],
            business_type=user_data.get('business_type'),
            country=user_data.get('country'),
            organization_id=uuid.UUID(organization_id),  # Convert string back to UUID
            role=UserRole.BUSINESS_ADMIN,  # Make registering user the business admin
            authentik_user_id=None  # Will be set if Authentik user is created
        )
        
        # Start 14-day trial for new user
        new_user.start_trial()
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    async def sync_user_with_authentik(
        user: User, 
        db: Session,
        password: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sync an existing local user with Authentik
        Creates user in Authentik if they don't exist there
        """
        
        if not authentik_service.is_configured():
            logger.warning("Authentik service not configured - skipping sync")
            return None
        
        user_authentik_id = getattr(user, 'authentik_user_id', None)
        if user_authentik_id:
            logger.info(f"User {user.email} already has Authentik user ID: {user_authentik_id}")
            return None
        
        try:
            # Check if user exists in Authentik
            existing_authentik_user = await authentik_service.get_user_by_email(str(user.email))
            
            if existing_authentik_user:
                # Link existing Authentik user
                setattr(user, 'authentik_user_id', existing_authentik_user.get('pk'))
                db.commit()
                logger.info(f"Linked existing Authentik user {user.email} with PK: {existing_authentik_user.get('pk')}")
                return existing_authentik_user
            
            else:
                # Create new user in Authentik
                user_company_name = getattr(user, 'company_name', None)
                authentik_user = await create_organization_admin(
                    email=str(user.email),
                    name=str(user.email).split('@')[0],  # Use email prefix as name
                    company_name=str(user_company_name) if user_company_name else "Unknown Company",
                    password=password  # Only if provided
                )
                
                if authentik_user:
                    setattr(user, 'authentik_user_id', authentik_user.get('pk'))
                    db.commit()
                    logger.info(f"Created and linked new Authentik user {user.email} with PK: {authentik_user.get('pk')}")
                    return authentik_user
            
        except Exception as e:
            logger.error(f"Failed to sync user with Authentik: {e}")
            return None
    
    @staticmethod
    async def update_authentik_user(
        user: User,
        updates: Dict[str, Any]
    ) -> bool:
        """Update user information in Authentik"""
        
        user_authentik_id = getattr(user, 'authentik_user_id', None)
        if not authentik_service.is_configured() or not user_authentik_id:
            return False
        
        try:
            await authentik_service.update_user(user_authentik_id, updates)
            logger.info(f"Updated Authentik user {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Authentik user: {e}")
            return False
    
    @staticmethod
    async def delete_authentik_user(user: User) -> bool:
        """Delete user from Authentik when local user is deleted"""
        
        user_authentik_id = getattr(user, 'authentik_user_id', None)
        if not authentik_service.is_configured() or not user_authentik_id:
            return False
        
        try:
            success = await authentik_service.delete_user(user_authentik_id)
            if success:
                logger.info(f"Deleted Authentik user {user.email}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete Authentik user: {e}")
            return False


# Global service instance
user_registration_service = UserRegistrationService()
