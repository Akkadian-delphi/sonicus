"""
Odoo CRM Integration Service for lead management and customer tracking
Handles lead creation, updates, and synchronization with Odoo CRM system
"""

import requests
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class OdooCRMService:
    """Service for managing leads and customers in Odoo CRM"""
    
    def __init__(self):
        self.odoo_url = getattr(settings, 'ODOO_URL', None)
        self.database = getattr(settings, 'ODOO_DATABASE', None)
        self.username = getattr(settings, 'ODOO_USERNAME', None)
        self.api_key = getattr(settings, 'ODOO_API_KEY', None)
        self.enabled = getattr(settings, 'ODOO_LEAD_ENABLED', True)
        
        self.session = requests.Session()
        self.authenticated = False
        
        if not all([self.odoo_url, self.database, self.username, self.api_key]) and self.enabled:
            logger.warning("Odoo configuration incomplete - CRM integration disabled")
            self.enabled = False
    
    async def authenticate(self) -> bool:
        """Authenticate with Odoo using API key"""
        if not self.enabled:
            return True
            
        try:
            # Odoo authentication endpoint
            auth_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [self.database, self.username, self.api_key, {}]
                }
            }
            
            response = self.session.post(
                f"{self.odoo_url}/jsonrpc",
                json=auth_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    self.authenticated = True
                    logger.info("Successfully authenticated with Odoo")
                    return True
                else:
                    logger.error(f"Odoo authentication failed: {result.get('error')}")
                    return False
            else:
                logger.error(f"Odoo authentication request failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error authenticating with Odoo: {e}")
            return False
    
    async def create_lead(self, lead_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new lead in Odoo CRM"""
        if not self.enabled:
            logger.info(f"Odoo disabled - would create lead: {lead_data.get('name')}")
            return {
                "id": f"mock_lead_{datetime.utcnow().timestamp()}",
                "name": lead_data.get("name"),
                "email": lead_data.get("email"),
                "status": "new"
            }
        
        # Ensure authentication
        if not self.authenticated:
            if not await self.authenticate():
                return None
        
        try:
            # Prepare lead data for Odoo
            odoo_lead_data = {
                "name": lead_data["name"],
                "contact_name": lead_data.get("contact_name", lead_data["name"]),
                "email_from": lead_data["email"],
                "phone": lead_data.get("phone", ""),
                "website": lead_data.get("website", ""),
                "company_name": lead_data.get("company_name", lead_data["name"]),
                "description": lead_data.get("description", ""),
                "source_id": await self._get_source_id(lead_data.get("source", "sonicus_registration")),
                "stage_id": await self._get_default_stage_id(),
                "user_id": await self._get_default_user_id(),
                "team_id": await self._get_default_team_id(),
                "tag_ids": await self._get_tag_ids(["sonicus", "business_registration"]),
                "priority": "1",  # Normal priority
                "date_open": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add custom fields if available
            if "subscription_plan" in lead_data:
                odoo_lead_data["x_subscription_plan"] = lead_data["subscription_plan"]
            if "stripe_customer_id" in lead_data:
                odoo_lead_data["x_stripe_customer_id"] = lead_data["stripe_customer_id"]
            
            # Create lead via Odoo API
            create_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.database,
                        self.username,
                        self.api_key,
                        "crm.lead",
                        "create",
                        [odoo_lead_data]
                    ]
                }
            }
            
            response = self.session.post(
                f"{self.odoo_url}/jsonrpc",
                json=create_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    lead_id = result["result"]
                    logger.info(f"Odoo lead created successfully: {lead_id}")
                    
                    # Return lead details
                    return {
                        "id": lead_id,
                        "name": lead_data["name"],
                        "email": lead_data["email"],
                        "status": "created",
                        "odoo_url": f"{self.odoo_url}/web#id={lead_id}&model=crm.lead"
                    }
                else:
                    logger.error(f"Odoo lead creation failed: {result.get('error')}")
                    return None
            else:
                logger.error(f"Odoo API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Odoo lead: {e}")
            return None
    
    async def update_lead(self, lead_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing lead in Odoo"""
        if not self.enabled:
            logger.info(f"Odoo disabled - would update lead {lead_id}: {updates}")
            return True
        
        if not self.authenticated:
            if not await self.authenticate():
                return False
        
        try:
            update_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.database,
                        self.username,
                        self.api_key,
                        "crm.lead",
                        "write",
                        [[lead_id], updates]
                    ]
                }
            }
            
            response = self.session.post(
                f"{self.odoo_url}/jsonrpc",
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    logger.info(f"Odoo lead {lead_id} updated successfully")
                    return True
                else:
                    logger.error(f"Odoo lead update failed: {result.get('error')}")
                    return False
            else:
                logger.error(f"Odoo API request failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating Odoo lead {lead_id}: {e}")
            return False
    
    async def get_lead(self, lead_id: int) -> Optional[Dict[str, Any]]:
        """Get lead details from Odoo"""
        if not self.enabled:
            return {
                "id": lead_id,
                "name": "Mock Lead",
                "email": "mock@example.com",
                "stage": "new"
            }
        
        if not self.authenticated:
            if not await self.authenticate():
                return None
        
        try:
            read_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.database,
                        self.username,
                        self.api_key,
                        "crm.lead",
                        "read",
                        [lead_id],
                        {"fields": ["name", "email_from", "phone", "stage_id", "user_id", "company_name"]}
                    ]
                }
            }
            
            response = self.session.post(
                f"{self.odoo_url}/jsonrpc",
                json=read_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result["result"][0] if result["result"] else None
                else:
                    logger.error(f"Odoo lead retrieval failed: {result.get('error')}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Odoo lead {lead_id}: {e}")
            return None
    
    async def search_leads(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for leads in Odoo based on criteria"""
        if not self.enabled:
            return []
        
        if not self.authenticated:
            if not await self.authenticate():
                return []
        
        try:
            # Build search domain
            domain = []
            if "email" in search_criteria:
                domain.append(["email_from", "=", search_criteria["email"]])
            if "company_name" in search_criteria:
                domain.append(["company_name", "ilike", search_criteria["company_name"]])
            
            search_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.database,
                        self.username,
                        self.api_key,
                        "crm.lead",
                        "search_read",
                        [domain],
                        {"fields": ["name", "email_from", "phone", "stage_id", "company_name"], "limit": 10}
                    ]
                }
            }
            
            response = self.session.post(
                f"{self.odoo_url}/jsonrpc",
                json=search_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", [])
            else:
                logger.error(f"Odoo search request failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching Odoo leads: {e}")
            return []
    
    async def _get_source_id(self, source_name: str) -> Optional[int]:
        """Get or create a lead source"""
        if not self.enabled:
            return 1  # Mock source ID
        
        try:
            # Search for existing source
            search_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.database,
                        self.username,
                        self.api_key,
                        "utm.source",
                        "search",
                        [["name", "=", source_name]]
                    ]
                }
            }
            
            response = self.session.post(f"{self.odoo_url}/jsonrpc", json=search_data)
            result = response.json()
            
            if result.get("result"):
                return result["result"][0]
            
            # Create source if not found
            create_data = {
                "jsonrpc": "2.0", 
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.database,
                        self.username, 
                        self.api_key,
                        "utm.source",
                        "create",
                        [{"name": source_name}]
                    ]
                }
            }
            
            response = self.session.post(f"{self.odoo_url}/jsonrpc", json=create_data)
            result = response.json()
            return result.get("result")
            
        except Exception as e:
            logger.error(f"Error getting/creating source {source_name}: {e}")
            return None
    
    async def _get_default_stage_id(self) -> Optional[int]:
        """Get default lead stage (usually 'New')"""
        # This would typically be the first stage in the pipeline
        return 1  # Mock stage ID
    
    async def _get_default_user_id(self) -> Optional[int]:
        """Get default user for lead assignment"""
        # This would typically be a sales person or admin
        return 1  # Mock user ID
    
    async def _get_default_team_id(self) -> Optional[int]:
        """Get default sales team"""
        return 1  # Mock team ID
    
    async def _get_tag_ids(self, tag_names: List[str]) -> List[int]:
        """Get or create tags and return their IDs"""
        if not self.enabled:
            return [1, 2]  # Mock tag IDs
        
        # This would search/create tags and return their IDs
        return []  # Simplified for now
    
    async def convert_lead_to_customer(self, lead_id: int, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a lead to a customer/partner in Odoo"""
        if not self.enabled:
            return {"id": f"customer_{lead_id}", "status": "converted"}
        
        # This would use Odoo's lead conversion functionality
        # Implementation would depend on specific Odoo setup and requirements
        logger.info(f"Converting lead {lead_id} to customer (not implemented)")
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get Odoo service status and configuration"""
        return {
            "enabled": self.enabled,
            "configured": bool(all([self.odoo_url, self.database, self.username, self.api_key])),
            "authenticated": self.authenticated,
            "odoo_url": self.odoo_url,
            "database": self.database,
            "username": self.username
        }


# Global Odoo service instance  
odoo_service = OdooCRMService()
