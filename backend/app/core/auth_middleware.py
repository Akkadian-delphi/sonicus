"""
Authentication middleware for role-based access control in B2B2C architecture.
"""

import logging
from functools import wraps
from typing import Optional, Callable, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.organization import OrganizationStatus

logger = logging.getLogger(__name__)

# Security scheme for bearer token
security_scheme = HTTPBearer()


class AuthenticationError(HTTPException):
    """Custom authentication error."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Custom authorization error."""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> User:
    """
    Get authenticated user from JWT token.
    This replaces the get_current_user function for B2B2C architecture.
    """
    try:
        # Use existing get_current_user function with token string
        user = await get_current_user(credentials.credentials)
        
        # Validate user is active and organization is active
        if user.organization_id:
            if user.organization.subscription_status == OrganizationStatus.CANCELLED.value:
                raise AuthorizationError("Organization subscription is cancelled")
            
            if user.organization.subscription_status == OrganizationStatus.SUSPENDED.value:
                raise AuthorizationError("Organization subscription is suspended")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise AuthenticationError("Authentication failed")


def require_role(*allowed_roles: UserRole):
    """
    Decorator that requires user to have one of the specified roles.
    
    Usage:
        @require_role(UserRole.BUSINESS_ADMIN, UserRole.SUPER_ADMIN)
        async def admin_endpoint():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from function dependencies
            current_user = None
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
            
            # If not found in args, check kwargs
            if not current_user:
                current_user = kwargs.get('current_user')
            
            if not current_user:
                raise AuthenticationError("User not authenticated")
            
            # Check if user has required role - compare string values
            user_role_value = current_user.role
            allowed_role_values = [role.value for role in allowed_roles]
            
            if user_role_value not in allowed_role_values:
                logger.warning(
                    f"User {current_user.email} with role {user_role_value} "
                    f"attempted to access endpoint requiring {allowed_role_values}"
                )
                raise AuthorizationError(
                    f"Required role: {' or '.join(allowed_role_values)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_super_admin(func: Callable) -> Callable:
    """Decorator that requires Super Admin role."""
    return require_role(UserRole.SUPER_ADMIN)(func)


def require_business_admin(func: Callable) -> Callable:
    """Decorator that requires Business Admin role (or Super Admin)."""
    return require_role(UserRole.BUSINESS_ADMIN, UserRole.SUPER_ADMIN)(func)


def require_staff_or_admin(func: Callable) -> Callable:
    """Decorator that requires staff privileges or higher."""
    return require_role(UserRole.STAFF, UserRole.BUSINESS_ADMIN, UserRole.SUPER_ADMIN)(func)


def require_organization_access(organization_id: Optional[str] = None):
    """
    Decorator that ensures user has access to specific organization.
    If organization_id is None, uses the user's own organization.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user
            current_user = None
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
            
            if not current_user:
                current_user = kwargs.get('current_user')
            
            if not current_user:
                raise AuthenticationError("User not authenticated")
            
            # Determine target organization ID
            target_org_id = organization_id
            if not target_org_id:
                # Try to get from function parameters
                target_org_id = kwargs.get('organization_id')
            
            # Super admins can access any organization
            user_role = getattr(current_user, 'role')
            if user_role == UserRole.SUPER_ADMIN.value:
                return await func(*args, **kwargs)
            
            # Check organization access
            user_org_id = getattr(current_user, 'organization_id')
            if not user_org_id:
                raise AuthorizationError("User not associated with any organization")
            
            if target_org_id and str(user_org_id) != str(target_org_id):
                user_email = getattr(current_user, 'email')
                logger.warning(
                    f"User {user_email} from organization {user_org_id} "
                    f"attempted to access organization {target_org_id}"
                )
                raise AuthorizationError("Access denied to this organization")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_active_subscription(func: Callable) -> Callable:
    """Decorator that requires user's organization to have active subscription."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get current user
        current_user = None
        for arg in args:
            if isinstance(arg, User):
                current_user = arg
                break
        
        if not current_user:
            current_user = kwargs.get('current_user')
        
        if not current_user:
            raise AuthenticationError("User not authenticated")
        
        # Super admins bypass subscription check
        user_role = getattr(current_user, 'role')
        if user_role == UserRole.SUPER_ADMIN.value:
            return await func(*args, **kwargs)
        
        # Check subscription status
        user_org_id = getattr(current_user, 'organization_id')
        if not user_org_id:
            raise AuthorizationError("User not associated with any organization")
        
        user_organization = getattr(current_user, 'organization')
        if not user_organization:
            raise AuthorizationError("Organization not found")
        
        subscription_status = current_user.organization.subscription_status
        
        if subscription_status == OrganizationStatus.CANCELLED.value:
            raise AuthorizationError("Organization subscription is cancelled")
        
        if subscription_status == OrganizationStatus.SUSPENDED.value:
            raise AuthorizationError("Organization subscription is suspended")
        
        # Allow trial and active subscriptions
        active_statuses = [OrganizationStatus.TRIAL.value, OrganizationStatus.ACTIVE.value]
        if subscription_status not in active_statuses:
            raise AuthorizationError("Organization subscription is not active")
        
        return await func(*args, **kwargs)
    return wrapper


class RoleBasedAccessControl:
    """
    Class-based approach for role-based access control.
    Useful for more complex permission logic.
    """
    
    @staticmethod
    def can_manage_organization(user: User, target_org_id: Optional[str] = None) -> bool:
        """Check if user can manage organization."""
        # Super admins can manage any organization
        user_role = getattr(user, 'role')
        if user_role == UserRole.SUPER_ADMIN.value:
            return True
        
        # Business admins can only manage their own organization
        if user_role == UserRole.BUSINESS_ADMIN.value:
            if not target_org_id:
                return True  # Managing their own org
            user_org_id = getattr(user, 'organization_id')
            return str(user_org_id) == str(target_org_id)
        
        return False
    
    @staticmethod
    def can_view_analytics(user: User, target_org_id: Optional[str] = None) -> bool:
        """Check if user can view analytics."""
        # Super admins can view any analytics
        user_role = getattr(user, 'role')
        if user_role == UserRole.SUPER_ADMIN.value:
            return True
        
        # Business admins and staff can view their org's analytics
        allowed_roles = [UserRole.BUSINESS_ADMIN.value, UserRole.STAFF.value]
        if user_role in allowed_roles:
            if not target_org_id:
                return True
            user_org_id = getattr(user, 'organization_id')
            return str(user_org_id) == str(target_org_id)
        
        return False
    
    @staticmethod
    def can_manage_users(user: User, target_org_id: Optional[str] = None) -> bool:
        """Check if user can manage users."""
        # Super admins can manage users in any organization
        user_role = getattr(user, 'role')
        if user_role == UserRole.SUPER_ADMIN.value:
            return True
        
        # Business admins can manage users in their organization
        if user_role == UserRole.BUSINESS_ADMIN.value:
            if not target_org_id:
                return True
            user_org_id = getattr(user, 'organization_id')
            return str(user_org_id) == str(target_org_id)
        
        return False


# Dependency functions for FastAPI
async def get_super_admin_user(
    current_user: User = Depends(get_authenticated_user)
) -> User:
    """FastAPI dependency that ensures user is Super Admin."""
    user_role = getattr(current_user, 'role')
    if user_role != UserRole.SUPER_ADMIN.value:
        raise AuthorizationError("Super Admin access required")
    return current_user


async def get_business_admin_user(
    current_user: User = Depends(get_authenticated_user)
) -> User:
    """FastAPI dependency that ensures user is Business Admin or Super Admin."""
    allowed_roles = [UserRole.BUSINESS_ADMIN.value, UserRole.SUPER_ADMIN.value]
    user_role = getattr(current_user, 'role')
    if user_role not in allowed_roles:
        raise AuthorizationError("Business Admin access required")
    return current_user


async def get_staff_user(
    current_user: User = Depends(get_authenticated_user)
) -> User:
    """FastAPI dependency that ensures user has staff privileges or higher."""
    allowed_roles = [UserRole.STAFF.value, UserRole.BUSINESS_ADMIN.value, UserRole.SUPER_ADMIN.value]
    user_role = getattr(current_user, 'role')
    if user_role not in allowed_roles:
        raise AuthorizationError("Staff access required")
    return current_user
