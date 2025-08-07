"""
Authentik API Service
Handles user creation, management, and synchronization with Authentik
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Configuration from environment
AUTHENTIK_BASE_URL = os.getenv("AUTHENTIK_BASE_URL", "https://authentik.elefefe.eu")
AUTHENTIK_API_TOKEN = os.getenv("AUTHENTIK_API_TOKEN")  # Service account token


class AuthentikUser(BaseModel):
    """Authentik user model"""
    pk: Optional[int] = None
    username: str
    email: str
    name: str
    is_active: bool = True
    groups: List[int] = []
    attributes: Dict[str, Any] = {}


class AuthentikGroup(BaseModel):
    """Authentik group model"""
    pk: Optional[int] = None
    name: str
    is_superuser: bool = False
    parent: Optional[int] = None
    users: List[int] = []
    attributes: Dict[str, Any] = {}


class AuthentikAPIError(Exception):
    """Authentik API related errors"""
    pass


class AuthentikService:
    """Service for interacting with Authentik API"""
    
    def __init__(self):
        self.base_url = AUTHENTIK_BASE_URL.rstrip('/')
        self.api_base = f"{self.base_url}/api/v3"
        self.timeout = 30.0
        
        # Get API token from environment
        self.api_token = AUTHENTIK_API_TOKEN
        
        if not self.api_token:
            logger.warning("No Authentik API token configured. User creation will be disabled.")
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Authentik API"""
        
        if not self.api_token:
            raise AuthentikAPIError("No Authentik API token configured")
        
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data if data else None,
                    params=params if params else None,
                    headers=headers
                )
                
                if response.status_code >= 400:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get('detail', error_detail)
                    except:
                        pass
                    
                    logger.error(f"Authentik API error {response.status_code}: {error_detail}")
                    raise AuthentikAPIError(f"API request failed: {error_detail}")
                
                return response.json() if response.content else {}
                
        except httpx.RequestError as e:
            logger.error(f"Request to Authentik API failed: {e}")
            raise AuthentikAPIError(f"Request failed: {str(e)}")
    
    async def validate_api_token(self) -> bool:
        """
        Validate the API token by making a simple API call
        Returns True if token is valid, False otherwise
        """
        try:
            # Try a simple API call to validate the token
            await self._make_request("GET", "/core/users/")
            return True
        except AuthentikAPIError as e:
            if "Token invalid/expired" in str(e):
                logger.warning("Authentik API token is expired or invalid")
                return False
            # Other API errors don't necessarily mean the token is invalid
            logger.error(f"API token validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            return False
    
    async def create_user(
        self,
        email: str,
        username: str,
        name: str,
        password: Optional[str] = None,
        groups: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new user in Authentik
        
        Args:
            email: User's email address
            username: Username (should be unique)
            name: Display name
            password: Initial password (optional, can be set later)
            groups: List of group names to add user to
            attributes: Additional user attributes
        
        Returns:
            Created user data from Authentik
        """
        try:
            # Prepare user data
            user_data = {
                "username": username,
                "email": email,
                "name": name,
                "is_active": True,
                "type": "internal"  # Internal Authentik user
            }
            
            # Add password if provided
            if password:
                user_data["password"] = password
            
            # Add attributes if provided
            if attributes:
                user_data["attributes"] = attributes
            
            # Create the user
            logger.info(f"Creating user in Authentik: {email}")
            user_response = await self._make_request("POST", "/core/users/", user_data)
            
            user_pk = user_response.get("pk")
            if not user_pk:
                raise AuthentikAPIError("No user PK returned from Authentik")
            
            # Add user to groups if specified
            if groups:
                await self._add_user_to_groups(user_pk, groups)
            
            logger.info(f"Successfully created user in Authentik: {email} (PK: {user_pk})")
            return user_response
            
        except Exception as e:
            logger.error(f"Failed to create user in Authentik: {e}")
            raise AuthentikAPIError(f"User creation failed: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email from Authentik"""
        try:
            params = {"email": email}
            response = await self._make_request("GET", "/core/users/", params=params)
            
            results = response.get("results", [])
            if results:
                return results[0]  # Return first match
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by email from Authentik: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username from Authentik"""
        try:
            params = {"username": username}
            response = await self._make_request("GET", "/core/users/", params=params)
            
            results = response.get("results", [])
            if results:
                return results[0]  # Return first match
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by username from Authentik: {e}")
            return None
    
    async def update_user(self, user_pk: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user in Authentik"""
        try:
            logger.info(f"Updating user in Authentik: PK {user_pk}")
            response = await self._make_request("PATCH", f"/core/users/{user_pk}/", updates)
            return response
            
        except Exception as e:
            logger.error(f"Failed to update user in Authentik: {e}")
            raise AuthentikAPIError(f"User update failed: {str(e)}")
    
    async def delete_user(self, user_pk: int) -> bool:
        """Delete user from Authentik"""
        try:
            logger.info(f"Deleting user in Authentik: PK {user_pk}")
            await self._make_request("DELETE", f"/core/users/{user_pk}/")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user in Authentik: {e}")
            return False
    
    async def get_groups(self) -> List[Dict[str, Any]]:
        """Get all groups from Authentik"""
        try:
            response = await self._make_request("GET", "/core/groups/")
            return response.get("results", [])
            
        except Exception as e:
            logger.error(f"Failed to get groups from Authentik: {e}")
            return []
    
    async def get_group_by_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Get group by name from Authentik"""
        try:
            params = {"name": group_name}
            response = await self._make_request("GET", "/core/groups/", params=params)
            
            results = response.get("results", [])
            if results:
                return results[0]  # Return first match
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get group by name from Authentik: {e}")
            return None
    
    async def create_group(
        self,
        name: str,
        is_superuser: bool = False,
        parent_name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new group in Authentik"""
        try:
            group_data = {
                "name": name,
                "is_superuser": is_superuser
            }
            
            # Set parent if specified
            if parent_name:
                parent_group = await self.get_group_by_name(parent_name)
                if parent_group:
                    group_data["parent"] = parent_group["pk"]
            
            # Add attributes if provided
            if attributes:
                group_data["attributes"] = attributes
            
            logger.info(f"Creating group in Authentik: {name}")
            response = await self._make_request("POST", "/core/groups/", group_data)
            return response
            
        except Exception as e:
            logger.error(f"Failed to create group in Authentik: {e}")
            raise AuthentikAPIError(f"Group creation failed: {str(e)}")
    
    async def _add_user_to_groups(self, user_pk: int, group_names: List[str]):
        """Add user to specified groups"""
        for group_name in group_names:
            try:
                group = await self.get_group_by_name(group_name)
                if not group:
                    logger.warning(f"Group '{group_name}' not found in Authentik")
                    continue
                
                # Add user to group
                group_pk = group["pk"]
                user_data = {"pk": user_pk}
                
                await self._make_request(
                    "POST", 
                    f"/core/groups/{group_pk}/add_user/", 
                    user_data
                )
                
                logger.info(f"Added user {user_pk} to group '{group_name}'")
                
            except Exception as e:
                logger.error(f"Failed to add user to group '{group_name}': {e}")
    
    async def sync_user_groups(self, user_pk: int, group_names: List[str]):
        """Sync user's groups (remove from old groups, add to new ones)"""
        try:
            # Get current user data
            user_response = await self._make_request("GET", f"/core/users/{user_pk}/")
            current_groups = user_response.get("groups", [])
            
            # Get target group PKs
            target_group_pks = []
            for group_name in group_names:
                group = await self.get_group_by_name(group_name)
                if group:
                    target_group_pks.append(group["pk"])
            
            # Remove user from groups not in target list
            for group_pk in current_groups:
                if group_pk not in target_group_pks:
                    try:
                        user_data = {"pk": user_pk}
                        await self._make_request(
                            "POST", 
                            f"/core/groups/{group_pk}/remove_user/", 
                            user_data
                        )
                        logger.info(f"Removed user {user_pk} from group PK {group_pk}")
                    except Exception as e:
                        logger.error(f"Failed to remove user from group PK {group_pk}: {e}")
            
            # Add user to new groups
            await self._add_user_to_groups(user_pk, group_names)
            
        except Exception as e:
            logger.error(f"Failed to sync user groups: {e}")
    
    async def set_user_password(self, user_pk: int, password: str):
        """Set user password in Authentik"""
        try:
            password_data = {"password": password}
            await self._make_request("POST", f"/core/users/{user_pk}/set_password/", password_data)
            logger.info(f"Password set for user PK {user_pk}")
            
        except Exception as e:
            logger.error(f"Failed to set password for user: {e}")
            raise AuthentikAPIError(f"Password setting failed: {str(e)}")
    
    def is_configured(self) -> bool:
        """Check if Authentik service is properly configured"""
        return bool(self.api_token and self.base_url)


# Global instance
authentik_service = AuthentikService()


# Utility functions
async def create_organization_admin(
    email: str, 
    name: str, 
    company_name: str,
    password: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a business admin user in Authentik for a new organization
    """
    if not authentik_service.is_configured():
        logger.warning("Authentik service not configured - skipping user creation")
        return None
    
    try:
        # Generate username from email
        username = email.split('@')[0]
        
        # Check if user already exists
        existing_user = await authentik_service.get_user_by_email(email)
        if existing_user:
            logger.info(f"User already exists in Authentik: {email}")
            return existing_user
        
        # Create user with business admin role
        user_attributes = {
            "company_name": company_name,
            "role": "business_admin",
            "created_via": "sonicus_registration"
        }
        
        user_data = await authentik_service.create_user(
            email=email,
            username=username,
            name=name,
            password=password,
            groups=["sonicus-business-admin"],  # Add to business admin group
            attributes=user_attributes
        )
        
        return user_data
        
    except Exception as e:
        logger.error(f"Failed to create organization admin in Authentik: {e}")
        return None


async def ensure_default_groups():
    """Ensure default Sonicus groups exist in Authentik"""
    if not authentik_service.is_configured():
        return
    
    default_groups = [
        {"name": "sonicus-super-admin", "is_superuser": True},
        {"name": "sonicus-business-admin", "is_superuser": False},
        {"name": "sonicus-staff", "is_superuser": False},
        {"name": "sonicus-user", "is_superuser": False}
    ]
    
    for group_config in default_groups:
        try:
            existing_group = await authentik_service.get_group_by_name(group_config["name"])
            if not existing_group:
                await authentik_service.create_group(
                    name=group_config["name"],
                    is_superuser=group_config["is_superuser"],
                    attributes={
                        "description": f"Sonicus {group_config['name'].split('-')[1].replace('_', ' ').title()} users",
                        "created_by": "sonicus_system"
                    }
                )
                logger.info(f"Created default group: {group_config['name']}")
        except Exception as e:
            logger.error(f"Failed to create default group {group_config['name']}: {e}")
