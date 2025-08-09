"""
IONOS DNS Service for automated subdomain management
Handles DNS record creation, deletion, and verification for multi-tenant subdomains
"""

import requests
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class IONOSDNSService:
    """Service for managing DNS records via IONOS API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'IONOS_API_KEY', None)
        self.base_url = "https://api.hosting.ionos.com/dns/v1"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        self.enabled = getattr(settings, 'DNS_MANAGEMENT_ENABLED', True)
        
        if not self.api_key and self.enabled:
            logger.warning("IONOS API key not configured - DNS management disabled")
            self.enabled = False
    
    async def get_zone_id(self, domain: str) -> Optional[str]:
        """Get the zone ID for a domain (e.g., 'sonicus.eu')"""
        if not self.enabled:
            logger.info("DNS management disabled - skipping zone lookup")
            return None
            
        try:
            response = requests.get(
                f"{self.base_url}/zones",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get zones: {response.status_code} - {response.text}")
                return None
            
            zones = response.json()
            for zone in zones:
                if zone.get('name') == domain:
                    return zone.get('id')
            
            logger.error(f"Zone not found for domain: {domain}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting zone ID for {domain}: {e}")
            return None
    
    async def create_subdomain_record(self, subdomain: str, target_ip: str) -> bool:
        """Create A record for subdomain pointing to server IP"""
        if not self.enabled:
            logger.info(f"DNS management disabled - would create {subdomain}.sonicus.eu -> {target_ip}")
            return True  # Return success for development
            
        try:
            # Get zone ID for sonicus.eu domain
            zone_id = await self.get_zone_id("sonicus.eu")
            if not zone_id:
                logger.error("Could not get zone ID for sonicus.eu")
                return False
            
            # Create A record for subdomain
            record_data = {
                "name": subdomain,
                "type": "A",
                "content": target_ip,
                "ttl": getattr(settings, 'DNS_TTL', 3600),
                "prio": 0,
                "disabled": False
            }
            
            response = requests.post(
                f"{self.base_url}/zones/{zone_id}/records",
                headers=self.headers,
                json=record_data,
                timeout=30
            )
            
            if response.status_code == 201:
                logger.info(f"DNS record created successfully: {subdomain}.sonicus.eu -> {target_ip}")
                return True
            else:
                logger.error(f"Failed to create DNS record: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Error creating DNS record for {subdomain}: {e}")
            return False
    
    async def delete_subdomain_record(self, subdomain: str) -> bool:
        """Delete DNS record for subdomain"""
        if not self.enabled:
            logger.info(f"DNS management disabled - would delete {subdomain}.sonicus.eu")
            return True
            
        try:
            # Get zone ID for sonicus.eu domain
            zone_id = await self.get_zone_id("sonicus.eu")
            if not zone_id:
                return False
            
            # Find the record to delete
            record_id = await self.get_record_id(zone_id, subdomain)
            if not record_id:
                logger.warning(f"DNS record not found for {subdomain}")
                return False
            
            # Delete the record
            response = requests.delete(
                f"{self.base_url}/zones/{zone_id}/records/{record_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"DNS record deleted successfully: {subdomain}.sonicus.eu")
                return True
            else:
                logger.error(f"Failed to delete DNS record: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting DNS record for {subdomain}: {e}")
            return False
    
    async def get_record_id(self, zone_id: str, subdomain: str) -> Optional[str]:
        """Get record ID for a specific subdomain"""
        try:
            response = requests.get(
                f"{self.base_url}/zones/{zone_id}/records",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get records: {response.status_code}")
                return None
            
            records = response.json()
            for record in records:
                if record.get('name') == subdomain and record.get('type') == 'A':
                    return record.get('id')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting record ID for {subdomain}: {e}")
            return None
    
    async def list_subdomain_records(self) -> List[Dict[str, Any]]:
        """List all A records for subdomains"""
        if not self.enabled:
            return []
            
        try:
            zone_id = await self.get_zone_id("sonicus.eu")
            if not zone_id:
                return []
            
            response = requests.get(
                f"{self.base_url}/zones/{zone_id}/records",
                headers=self.headers,
                params={"type": "A"},
                timeout=30
            )
            
            if response.status_code == 200:
                records = response.json()
                # Filter out main domain records
                subdomains = [
                    record for record in records 
                    if record.get('name') and record.get('name') != '@' and record.get('name') != 'www'
                ]
                return subdomains
            else:
                logger.error(f"Failed to list records: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing subdomain records: {e}")
            return []
    
    async def update_subdomain_record(self, subdomain: str, new_target_ip: str) -> bool:
        """Update existing DNS record with new IP"""
        if not self.enabled:
            logger.info(f"DNS management disabled - would update {subdomain}.sonicus.eu -> {new_target_ip}")
            return True
            
        try:
            zone_id = await self.get_zone_id("sonicus.eu")
            if not zone_id:
                return False
            
            record_id = await self.get_record_id(zone_id, subdomain)
            if not record_id:
                logger.warning(f"DNS record not found for {subdomain} - creating new record")
                return await self.create_subdomain_record(subdomain, new_target_ip)
            
            # Update the record
            record_data = {
                "name": subdomain,
                "type": "A",
                "content": new_target_ip,
                "ttl": getattr(settings, 'DNS_TTL', 3600),
                "prio": 0,
                "disabled": False
            }
            
            response = requests.put(
                f"{self.base_url}/zones/{zone_id}/records/{record_id}",
                headers=self.headers,
                json=record_data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"DNS record updated successfully: {subdomain}.sonicus.eu -> {new_target_ip}")
                return True
            else:
                logger.error(f"Failed to update DNS record: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating DNS record for {subdomain}: {e}")
            return False
    
    async def validate_subdomain_format(self, subdomain: str) -> bool:
        """Validate subdomain format and check against reserved names"""
        # Basic format validation
        if not subdomain or len(subdomain) < 3 or len(subdomain) > 63:
            return False
        
        # Must start and end with alphanumeric
        if not (subdomain[0].isalnum() and subdomain[-1].isalnum()):
            return False
        
        # Only alphanumeric and hyphens allowed
        if not all(c.isalnum() or c == '-' for c in subdomain):
            return False
        
        # Check against reserved subdomains
        reserved = {
            'www', 'api', 'admin', 'app', 'mail', 'ftp', 'blog', 
            'shop', 'support', 'docs', 'cdn', 'assets', 'static',
            'test', 'staging', 'dev', 'demo', 'help', 'status'
        }
        
        if subdomain.lower() in reserved:
            return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get DNS service status and configuration"""
        return {
            "enabled": self.enabled,
            "api_configured": bool(self.api_key),
            "base_url": self.base_url,
            "dns_ttl": getattr(settings, 'DNS_TTL', 3600),
            "server_ip": getattr(settings, 'SERVER_PUBLIC_IP', 'not_configured')
        }


# Global DNS service instance
dns_service = IONOSDNSService()
