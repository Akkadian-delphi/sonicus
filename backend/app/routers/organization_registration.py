"""
Organization Registration and Management Router
Phase 1 implementation from NEXT.md

Handles:
1. Organization registration (business signup)
2. Organization profile management
3. Subdomain availability checks
4. Organization authentication
5. DNS subdomain creation and management
6. Payment integration via Revolut
7. CRM lead creation in Odoo
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, text
from pydantic import BaseModel, EmailStr, Field, validator
from app.db.session import get_db
from app.models.organization import Organization, SubscriptionTier, OrganizationStatus
from app.core.tenant_middleware import get_current_tenant, get_organization_context

# DNS and Multi-tenant Services Integration
from app.services.dns_service import dns_service
from app.services.dns_verification import dns_verification_service
from app.services.stripe_service import stripe_service
from app.services.odoo_service import odoo_service
from app.services.deployment_service import deployment_service
from app.services.email import send_organization_registration_email

import uuid
import re
from datetime import datetime, timedelta
import secrets
import string

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Request/Response Models ---

class OrganizationRegistrationRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Organization name")
    display_name: Optional[str] = Field(None, max_length=255, description="Public display name")
    domain: str = Field(..., min_length=3, max_length=50, description="Subdomain identifier (e.g., 'acme' for acme.sonicus.com)")
    primary_contact_email: EmailStr = Field(..., description="Primary contact email")
    
    # Contact information
    phone: Optional[str] = Field(None, max_length=50)
    
    # Business details
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, description="1-10, 11-50, 51-200, 201-1000, 1000+")
    
    # Address (optional during registration)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    @validator('domain')
    def validate_domain(cls, v):
        # Must be alphanumeric with hyphens, no special characters
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$', v) and len(v) > 1:
            if len(v) == 1 and not re.match(r'^[a-zA-Z0-9]$', v):
                raise ValueError('Domain must contain only letters, numbers, and hyphens')
        elif len(v) > 1 and not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$', v):
            raise ValueError('Domain must contain only letters, numbers, and hyphens')
        
        # Reserved domains
        reserved = ['www', 'api', 'admin', 'app', 'dashboard', 'static', 'cdn', 'mail', 'ftp', 'blog']
        if v.lower() in reserved:
            raise ValueError(f'Domain "{v}" is reserved')
        
        return v.lower()
    
    @validator('company_size')
    def validate_company_size(cls, v):
        if v and v not in ['1-10', '11-50', '51-200', '201-1000', '1000+']:
            raise ValueError('Invalid company size option')
        return v


class OrganizationResponse(BaseModel):
    id: str
    name: str
    display_name: Optional[str]
    domain: str
    custom_domain: Optional[str]
    subscription_tier: str
    subscription_status: str
    primary_contact_email: str
    max_users: int
    features_enabled: Dict[str, Any]
    created_at: datetime
    onboarding_completed: bool
    
    @validator('id', pre=True)
    def convert_uuid_to_string(cls, v):
        if hasattr(v, '__str__'):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class DomainAvailabilityResponse(BaseModel):
    domain: str
    available: bool
    suggested_alternatives: Optional[List[str]] = None
    message: str


class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    @validator('company_size')
    def validate_company_size(cls, v):
        if v and v not in ['1-10', '11-50', '51-200', '201-1000', '1000+']:
            raise ValueError('Invalid company size option')
        return v


# --- Helper Functions ---

def generate_domain_alternatives(base_domain: str, limit: int = 5) -> List[str]:
    """Generate alternative domain suggestions"""
    alternatives = []
    
    # Add numbers
    for i in range(1, limit + 1):
        alternatives.append(f"{base_domain}{i}")
    
    # Add common suffixes
    suffixes = ['inc', 'corp', 'ltd', 'co', 'team']
    for suffix in suffixes[:limit-len(alternatives)]:
        alternatives.append(f"{base_domain}{suffix}")
    
    return alternatives[:limit]


async def setup_organization_infrastructure(
    organization_id: str,
    domain: str,
    contact_email: str,
    organization_name: str,
    phone: str,
    address_info: Dict[str, Any]
):
    """
    Background task to setup complete multi-tenant infrastructure for new organization
    
    This function orchestrates the creation of:
    1. DNS subdomain record (IONOS)
    2. Payment customer (Revolut) 
    3. CRM lead (Odoo)
    4. Container deployment trigger
    5. DNS verification monitoring
    """
    logger.info(f"Starting infrastructure setup for organization {organization_id} ({domain})")
    
    try:
        # Step 1: Create DNS subdomain record
        logger.info(f"Creating DNS record for {domain}.sonicus.eu")
        dns_success = await dns_service.create_subdomain_record(
            subdomain=domain,
            target_ip="127.0.0.1"  # Development IP, will be updated with container IP
        )
        
        if dns_success:
            logger.info(f"DNS record created successfully for {domain}.sonicus.eu")
        else:
            logger.error(f"DNS record creation failed for {domain}.sonicus.eu")
        
        # Step 2: Create payment customer in Stripe
        logger.info(f"Creating Stripe customer for {contact_email}")
        customer_data = {
            "email": contact_email,
            "name": organization_name,
            "phone": phone,
            "address": {
                "line1": address_info.get("address_line1", ""),
                "city": address_info.get("city", ""),
                "postal_code": "",
                "country": address_info.get("country", "")
            },
            "organization_id": str(organization_id),
            "business_type": business_type
        }
        
        stripe_customer = await stripe_service.create_customer(customer_data)
        
        if stripe_customer:
            logger.info(f"Stripe customer created: {stripe_customer.get('id')}")
        else:
            logger.error(f"Stripe customer creation failed")
        
        # Step 3: Create lead in Odoo CRM
        logger.info(f"Creating Odoo CRM lead for {organization_name}")
        lead_data = {
            "name": organization_name,
            "contact_name": organization_name,
            "email": contact_email,
            "phone": phone,
            "website": f"https://{domain}.sonicus.eu",
            "company_name": organization_name,
            "description": f"New organization registration for domain: {domain}",
            "source": "sonicus_registration"
        }
        
        odoo_lead = await odoo_service.create_lead(lead_data)
        
        if odoo_lead:
            logger.info(f"Odoo lead created: {odoo_lead.get('id')}")
        else:
            logger.error(f"Odoo lead creation failed")
        
        # Step 4: Wait for DNS propagation
        logger.info(f"Waiting for DNS propagation for {domain}.sonicus.eu")
        propagation_success = await dns_verification_service.wait_for_dns_propagation(
            subdomain=domain,
            expected_ip="127.0.0.1"
        )
        
        if propagation_success:
            logger.info(f"DNS propagation verified for {domain}.sonicus.eu")
        else:
            logger.error(f"DNS propagation timeout for {domain}.sonicus.eu")
        
        # Step 5: Trigger container deployment
        logger.info(f"Triggering container deployment for {domain}")
        deployment_data = {
            "organization_id": organization_id,
            "organization_name": organization_name,
            "admin_email": contact_email,
            "subdomain": domain,
            "resources": {
                "cpu": "0.5",
                "memory": "512Mi",
                "storage": "1Gi"
            },
            "database_config": {
                "name": f"sonicus_{domain}",
                "host": "localhost"
            }
        }
        
        deployment_success = await deployment_service.trigger_container_deployment(deployment_data)
        
        if deployment_success:
            logger.info(f"Container deployment triggered successfully")
        else:
            logger.error(f"Container deployment trigger failed")
        
        # Step 6: Send organization registration confirmation email
        logger.info(f"Sending registration confirmation email to {contact_email}")
        try:
            # Generate a temporary admin password
            admin_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            
            # Create a mock background tasks object for the email function
            from fastapi import BackgroundTasks
            email_tasks = BackgroundTasks()
            
            # Send the registration email with login credentials
            send_organization_registration_email(
                background_tasks=email_tasks,
                admin_email=contact_email,
                organization_name=organization_name,
                subdomain=domain,
                admin_password=admin_password
            )
            
            # Execute the email task immediately since we're already in a background task
            for task in email_tasks.tasks:
                await task.func(*task.args, **task.kwargs)
            
            logger.info(f"Registration confirmation email sent to {contact_email}")
        except Exception as email_error:
            logger.error(f"Failed to send registration email: {str(email_error)}")
        
        logger.info(f"Infrastructure setup completed for organization {organization_id}")
        
    except Exception as e:
        logger.error(f"Infrastructure setup failed for organization {organization_id}: {str(e)}")
        # Note: We don't raise here as this is a background task
        # The organization is still created, infrastructure setup can be retried


# --- Route Handlers ---

@router.get("/organizations/domain-availability/{domain}", response_model=DomainAvailabilityResponse)
async def check_domain_availability(
    domain: str,
    db: Session = Depends(get_db)
):
    """
    Check if a subdomain is available for organization registration
    Public endpoint - no authentication required
    """
    try:
        # Validate domain format
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$', domain) and len(domain) > 1:
            if len(domain) == 1 and not re.match(r'^[a-zA-Z0-9]$', domain):
                return DomainAvailabilityResponse(
                    domain=domain,
                    available=False,
                    message="Domain must contain only letters, numbers, and hyphens"
                )
        elif len(domain) > 1 and not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$', domain):
            return DomainAvailabilityResponse(
                domain=domain,
                available=False,
                message="Domain must contain only letters, numbers, and hyphens"
            )
        
        # Check reserved domains
        reserved = ['www', 'api', 'admin', 'app', 'dashboard', 'static', 'cdn', 'mail', 'ftp', 'blog']
        if domain.lower() in reserved:
            return DomainAvailabilityResponse(
                domain=domain,
                available=False,
                message=f"Domain '{domain}' is reserved",
                suggested_alternatives=generate_domain_alternatives(domain)
            )
        
        # Check database for existing domain
        stmt = select(Organization).where(
            (Organization.domain == domain.lower()) |
            (Organization.custom_domain == f"{domain.lower()}.sonicus.com")
        )
        result = db.execute(stmt)
        existing_org = result.scalar_one_or_none()
        
        if existing_org:
            return DomainAvailabilityResponse(
                domain=domain,
                available=False,
                message="Domain is already taken",
                suggested_alternatives=generate_domain_alternatives(domain)
            )
        
        return DomainAvailabilityResponse(
            domain=domain,
            available=True,
            message="Domain is available"
        )
    
    except Exception as e:
        logger.error(f"Error checking domain availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking domain availability"
        )


@router.post("/organizations/register", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def register_organization(
    registration_data: OrganizationRegistrationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Enhanced Organization Registration with Multi-tenant Infrastructure
    Public endpoint - no authentication required (business self-service)
    
    Multi-step process:
    1. Validate domain availability
    2. Create organization record
    3. Create DNS subdomain record (IONOS)
    4. Setup payment customer (Revolut)
    5. Create CRM lead (Odoo)
    6. Queue container deployment
    7. Send welcome emails
    """
    try:
        # HOTFIX: Ensure correct schema is set for this session
        db.execute(text("SET search_path TO sonicus, public"))
        
        # Step 1: Check domain availability again
        stmt = select(Organization).where(
            (Organization.domain == registration_data.domain) |
            (Organization.custom_domain == f"{registration_data.domain}.sonicus.com")
        )
        result = db.execute(stmt)
        existing_org = result.scalar_one_or_none()
        
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Domain '{registration_data.domain}' is already taken"
            )
        
        # Check for duplicate primary contact email
        stmt = select(Organization).where(Organization.primary_contact_email == registration_data.primary_contact_email)
        result = db.execute(stmt)
        existing_email = result.scalar_one_or_none()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An organization with this email already exists"
            )
        
        # Step 2: Create new organization in database
        new_org = Organization(
            name=registration_data.name,
            display_name=registration_data.display_name or registration_data.name,
            domain=registration_data.domain,
            primary_contact_email=registration_data.primary_contact_email,
            phone=registration_data.phone,
            industry=registration_data.industry,
            company_size=registration_data.company_size,
            
            # Address information
            address_line1=registration_data.address_line1,
            address_line2=registration_data.address_line2,
            city=registration_data.city,
            state=registration_data.state,
            country=registration_data.country,
            postal_code=registration_data.postal_code,
            
            # Default subscription settings
            subscription_tier=SubscriptionTier.STARTER,
            subscription_status=OrganizationStatus.TRIAL,
            max_users=10,  # Starter tier default
            
            # Default features for trial
            features_enabled={
                "analytics": True,
                "custom_branding": False,
                "api_access": True,
                "webhook_integration": False,
                "advanced_reporting": False
            },
            
            # Trial period (14 days)
            trial_end_date=datetime.utcnow() + timedelta(days=14),
            
            onboarding_completed=False
        )
        
        db.add(new_org)
        db.commit()
        db.refresh(new_org)
        
        logger.info(f"Organization created in database: {new_org.name} ({new_org.domain})")
        
        # Step 3: Multi-tenant Infrastructure Setup (Background Tasks)
        background_tasks.add_task(
            setup_organization_infrastructure,
            str(new_org.id),
            registration_data.domain,
            registration_data.primary_contact_email,
            registration_data.name,
            registration_data.phone or "",
            {
                "address_line1": registration_data.address_line1,
                "city": registration_data.city,
                "country": registration_data.country
            }
        )
        
        logger.info(f"Infrastructure setup queued for organization: {new_org.name}")
        
        return OrganizationResponse.from_orm(new_org)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating organization"
        )


@router.get("/organizations/me", response_model=OrganizationResponse)
async def get_current_organization(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get current organization information based on tenant context
    Requires B2B2C tenant context
    """
    tenant = get_current_tenant(request)
    
    if not tenant or tenant.get('mode') != 'b2b2c':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint requires B2B2C tenant context (organization subdomain)"
        )
    
    organization_data = tenant.get('organization')
    if not organization_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get fresh organization data from database
    org_id = organization_data.get('id')
    stmt = select(Organization).where(Organization.id == org_id)
    result = db.execute(stmt)
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found in database"
        )
    
    return OrganizationResponse.from_orm(organization)


@router.put("/organizations/me", response_model=OrganizationResponse)
async def update_current_organization(
    update_data: OrganizationUpdateRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Update current organization information
    Requires B2B2C tenant context and organization admin role
    """
    tenant = get_current_tenant(request)
    
    if not tenant or tenant.get('mode') != 'b2b2c':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint requires B2B2C tenant context"
        )
    
    organization_data = tenant.get('organization')
    if not organization_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    try:
        # Get organization from database
        org_id = organization_data.get('id')
        stmt = select(Organization).where(Organization.id == org_id)
        result = db.execute(stmt)
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Update fields that are provided
        update_fields = update_data.dict(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(organization, field, value)
        
        db.commit()
        db.refresh(organization)
        
        logger.info(f"Organization updated: {organization.name} ({organization.domain})")
        
        return OrganizationResponse.from_orm(organization)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating organization"
        )


@router.get("/organizations/status")
async def get_organization_status(request: Request):
    """
    Get current tenant/organization status for debugging
    Public endpoint to help with tenant detection debugging
    """
    tenant = get_current_tenant(request)
    
    if not tenant:
        return {
            "error": "No tenant information available",
            "host": request.headers.get('host'),
            "headers": dict(request.headers)
        }
    
    return {
        "tenant_mode": tenant.get('mode'),
        "tenant_identifier": tenant.get('identifier'),
        "detection_method": tenant.get('detection_method'),
        "organization": tenant.get('organization'),
        "host": request.headers.get('host'),
        "error": tenant.get('error')
    }
