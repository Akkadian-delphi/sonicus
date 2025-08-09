"""
Multi-tenant middleware for B2B2C subdomain detection and routing
Phase 1 implementation from NEXT.md

This middleware detects the organization tenant based on:
1. Subdomain (organization.sonicus.com)  
2. Custom domain (organization.com -> organization tenant)
3. Direct API access with tenant header
"""
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.organization import Organization
from app.db.session import SessionLocal
import re

logger = logging.getLogger(__name__)

class TenantDetectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and inject tenant context into requests
    """
    
    def __init__(self, app, platform_domain: str = "sonicus.eu"):
        super().__init__(app)
        self.platform_domain = platform_domain
        # Regex pattern to extract subdomain from host
        self.subdomain_pattern = re.compile(r'^([a-zA-Z0-9-]+)\.sonicus\.eu$', re.IGNORECASE)
        # Excluded subdomains that are not tenant identifiers
        self.excluded_subdomains = {'www', 'api', 'admin', 'app', 'dashboard', 'static', 'cdn'}
    
    async def dispatch(self, request: Request, call_next):
        """
        Main middleware logic to detect tenant and inject context
        """
        # Skip tenant detection for certain paths
        if self._should_skip_tenant_detection(request):
            response = await call_next(request)
            return response
        
        # Detect tenant from request
        tenant_info = await self._detect_tenant(request)
        
        # Inject tenant information into request state
        request.state.tenant = tenant_info
        
        # For B2B2C mode, validate tenant exists and is active
        if tenant_info and tenant_info.get('mode') == 'b2b2c':
            if not tenant_info.get('organization'):
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "error": "Organization not found",
                        "message": f"No active organization found for identifier: {tenant_info.get('identifier')}",
                        "tenant_mode": "b2b2c"
                    }
                )
        
        # Continue to the actual endpoint
        response = await call_next(request)
        
        # Add tenant information to response headers for debugging
        if tenant_info:
            response.headers["X-Tenant-Mode"] = tenant_info.get('mode', 'unknown')
            if tenant_info.get('identifier'):
                response.headers["X-Tenant-Identifier"] = tenant_info['identifier']
        
        return response
    
    def _should_skip_tenant_detection(self, request: Request) -> bool:
        """
        Determine if tenant detection should be skipped for this request
        """
        path = request.url.path
        
        # Skip for health checks and public endpoints
        skip_paths = [
            '/health',
            '/docs',
            '/redoc',
            '/openapi.json',
            '/public/',
            '/static/',
            '/_internal/',
            '/api/v1/organizations/'  # Skip tenant detection for organization registration
        ]
        
        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return True
        
        return False
    
    async def _detect_tenant(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Detect tenant from various sources in priority order:
        1. Custom domain mapping
        2. Subdomain extraction
        3. X-Tenant-ID header (for API clients)
        4. Default to B2C mode
        """
        host = request.headers.get('host', '').lower()
        
        # Priority 1: Check for X-Tenant-ID header (API access)
        tenant_header = request.headers.get('x-tenant-id')
        if tenant_header:
            logger.info(f"Tenant detection via header: {tenant_header}")
            organization = await self._get_organization_by_identifier(tenant_header)
            if organization:
                return {
                    'mode': 'b2b2c',
                    'identifier': tenant_header,
                    'organization': organization,
                    'detection_method': 'header'
                }
        
        # Priority 2: Check for custom domain
        if not host.endswith('.sonicus.eu') and host != 'localhost' and not host.startswith('127.0.0.1'):
            logger.info(f"Tenant detection via custom domain: {host}")
            organization = await self._get_organization_by_custom_domain(host)
            if organization:
                return {
                    'mode': 'b2b2c',
                    'identifier': organization['domain'] or organization['id'],
                    'organization': organization,
                    'detection_method': 'custom_domain'
                }
        
        # Priority 3: Check for subdomain
        if host.endswith('.sonicus.eu'):
            match = self.subdomain_pattern.match(host)
            if match:
                subdomain = match.group(1).lower()
                
                # Skip excluded subdomains
                if subdomain in self.excluded_subdomains:
                    logger.info(f"Skipping excluded subdomain: {subdomain}")
                    return self._get_b2c_mode()
                
                logger.info(f"Tenant detection via subdomain: {subdomain}")
                organization = await self._get_organization_by_identifier(subdomain)
                if organization:
                    return {
                        'mode': 'b2b2c',
                        'identifier': subdomain,
                        'organization': organization,
                        'detection_method': 'subdomain'
                    }
                else:
                    # Subdomain doesn't match any organization - could be invalid
                    logger.warning(f"Subdomain '{subdomain}' does not match any organization")
                    return {
                        'mode': 'b2b2c',
                        'identifier': subdomain,
                        'organization': None,
                        'detection_method': 'subdomain',
                        'error': 'organization_not_found'
                    }
        
        # Default: B2C mode (main domain or localhost)
        logger.info(f"Default B2C mode for host: {host}")
        return self._get_b2c_mode()
    
    def _get_b2c_mode(self) -> Dict[str, Any]:
        """
        Return B2C mode tenant info
        """
        return {
            'mode': 'b2c',
            'identifier': None,
            'organization': None,
            'detection_method': 'default'
        }
    
    async def _get_organization_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get organization by domain, subdomain, or ID
        """
        try:
            with SessionLocal() as db:
                # First try to find by domain or custom_domain
                stmt = select(Organization).where(
                    (Organization.domain == identifier) |
                    (Organization.custom_domain == identifier)
                ).where(
                    Organization.subscription_status.in_(['trial', 'active'])
                )
                
                result = db.execute(stmt)
                organization = result.scalar_one_or_none()
                
                # If not found and identifier looks like a UUID, try by ID
                if not organization:
                    try:
                        import uuid
                        uuid.UUID(identifier)  # This will raise an exception if not a valid UUID
                        stmt = select(Organization).where(
                            Organization.id == identifier
                        ).where(
                            Organization.subscription_status.in_(['trial', 'active'])
                        )
                        result = db.execute(stmt)
                        organization = result.scalar_one_or_none()
                    except ValueError:
                        # Not a valid UUID, skip ID lookup
                        pass
                
                if organization:
                    return {
                        'id': str(organization.id),
                        'name': organization.name,
                        'display_name': organization.display_name,
                        'domain': organization.domain,
                        'custom_domain': organization.custom_domain,
                        'subscription_tier': organization.subscription_tier,
                        'subscription_status': organization.subscription_status,
                        'features_enabled': organization.features_enabled or {},
                        'max_users': organization.max_users,
                        'branding_config': organization.branding_config or {}
                    }
                
        except Exception as e:
            logger.error(f"Error querying organization by identifier '{identifier}': {e}")
        
        return None
    
    async def _get_organization_by_custom_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get organization by custom domain mapping
        """
        try:
            with SessionLocal() as db:
                stmt = select(Organization).where(
                    Organization.custom_domain == domain
                ).where(
                    Organization.subscription_status.in_(['trial', 'active'])
                )
                
                result = db.execute(stmt)
                organization = result.scalar_one_or_none()
                
                if organization:
                    return {
                        'id': str(organization.id),
                        'name': organization.name,
                        'display_name': organization.display_name,
                        'domain': organization.domain,
                        'custom_domain': organization.custom_domain,
                        'subscription_tier': organization.subscription_tier,
                        'subscription_status': organization.subscription_status,
                        'features_enabled': organization.features_enabled or {},
                        'max_users': organization.max_users,
                        'branding_config': organization.branding_config or {}
                    }
                
        except Exception as e:
            logger.error(f"Error querying organization by custom domain '{domain}': {e}")
        
        return None


def get_current_tenant(request: Request) -> Optional[Dict[str, Any]]:
    """
    Helper function to get current tenant from request state
    Usage in route handlers: tenant = get_current_tenant(request)
    """
    return getattr(request.state, 'tenant', None)


def require_b2b2c_tenant(request: Request) -> Dict[str, Any]:
    """
    Dependency function to require B2B2C tenant context
    Raises HTTPException if not in B2B2C mode or organization not found
    """
    tenant = get_current_tenant(request)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant detection failed"
        )
    
    if tenant.get('mode') != 'b2b2c':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint requires B2B2C tenant context"
        )
    
    if not tenant.get('organization'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {tenant.get('identifier')}"
        )
    
    return tenant


def require_b2c_mode(request: Request) -> Dict[str, Any]:
    """
    Dependency function to require B2C mode
    Raises HTTPException if not in B2C mode
    """
    tenant = get_current_tenant(request)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant detection failed"
        )
    
    if tenant.get('mode') != 'b2c':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only available in B2C mode"
        )
    
    return tenant


def get_organization_context(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get organization context if available, None otherwise
    Safe to use in both B2B2C and B2C modes
    """
    tenant = get_current_tenant(request)
    if tenant and tenant.get('mode') == 'b2b2c':
        return tenant.get('organization')
    return None
