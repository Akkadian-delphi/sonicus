"""
Container Deployment Service for triggering organization-specific container deployments
Handles webhook triggers for containerized Sonicus instance deployment
"""

import requests
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class ContainerDeploymentService:
    """Service for managing containerized deployments via webhooks"""
    
    def __init__(self):
        self.webhook_url = getattr(settings, 'DEPLOYMENT_WEBHOOK_URL', None)
        self.webhook_secret = getattr(settings, 'DEPLOYMENT_WEBHOOK_SECRET', None)
        self.enabled = getattr(settings, 'CONTAINER_DEPLOYMENT_ENABLED', True)
        
        if not self.webhook_url and self.enabled:
            logger.warning("Deployment webhook URL not configured - container deployment disabled")
            self.enabled = False
    
    async def trigger_container_deployment(self, deployment_data: Dict[str, Any]) -> bool:
        """Trigger webhook to deploy dedicated Sonicus container"""
        if not self.enabled or not self.webhook_url:
            logger.info(f"Container deployment disabled - would deploy for {deployment_data.get('subdomain')}")
            return True
        
        try:
            # Prepare webhook payload
            webhook_payload = {
                "event": "organization.container.deploy",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "organization_id": deployment_data["organization_id"],
                    "subdomain": deployment_data["subdomain"],
                    "admin_email": deployment_data["admin_email"],
                    "organization_name": deployment_data["organization_name"],
                    "subscription_id": deployment_data.get("subscription_id"),
                    "container_config": {
                        "image": "sonicus:latest",
                        "subdomain": deployment_data["subdomain"],
                        "environment": {
                            "SUBDOMAIN": deployment_data["subdomain"],
                            "ORG_ID": deployment_data["organization_id"],
                            "ORG_NAME": deployment_data["organization_name"],
                            "ADMIN_EMAIL": deployment_data["admin_email"],
                            "DATABASE_NAME": deployment_data.get("database_config", {}).get("name", f"sonicus_{deployment_data['subdomain']}"),
                            "DATABASE_HOST": deployment_data.get("database_config", {}).get("host", settings.POSTGRES_SERVER),
                            "REDIS_URL": getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
                            "API_V1_STR": "/api/v1"
                        },
                        "resources": {
                            "cpu": deployment_data.get("resources", {}).get("cpu", "0.5"),
                            "memory": deployment_data.get("resources", {}).get("memory", "512Mi"),
                            "storage": deployment_data.get("resources", {}).get("storage", "1Gi")
                        },
                        "networking": {
                            "subdomain": deployment_data["subdomain"],
                            "domain": "sonicus.eu",
                            "ssl_enabled": True,
                            "ports": {
                                "backend": 18100,
                                "frontend": 3000
                            }
                        }
                    },
                    "deployment_options": {
                        "auto_ssl": True,
                        "health_checks": True,
                        "auto_scaling": deployment_data.get("auto_scaling", False),
                        "backup_enabled": True,
                        "monitoring": True
                    }
                }
            }
            
            # Add webhook signature for security
            headers = {
                "Content-Type": "application/json",
                "X-Event-Type": "organization.container.deploy",
                "X-Timestamp": webhook_payload["timestamp"]
            }
            
            if self.webhook_secret:
                headers["X-Webhook-Secret"] = self.webhook_secret
                # Add signature if secret is configured
                signature = self._generate_webhook_signature(webhook_payload)
                headers["X-Signature"] = signature
            
            # Send webhook
            response = requests.post(
                self.webhook_url,
                json=webhook_payload,
                headers=headers,
                timeout=60  # Longer timeout for deployment triggers
            )
            
            if response.status_code == 200:
                logger.info(f"Container deployment webhook triggered successfully for {deployment_data['subdomain']}")
                
                # Parse response for deployment tracking
                try:
                    response_data = response.json()
                    deployment_id = response_data.get("deployment_id")
                    if deployment_id:
                        logger.info(f"Deployment ID: {deployment_id} for organization {deployment_data['organization_id']}")
                except:
                    pass
                
                return True
            else:
                logger.error(f"Container deployment webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to trigger container deployment webhook: {e}")
            return False
    
    async def check_deployment_status(self, organization_id: str, deployment_id: Optional[str] = None) -> Dict[str, Any]:
        """Check the status of container deployment"""
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Container deployment disabled"
            }
        
        try:
            # Construct status check URL
            if deployment_id:
                status_url = f"{self.webhook_url}/status/{deployment_id}"
            else:
                status_url = f"{self.webhook_url}/status/organization/{organization_id}"
            
            headers = {}
            if self.webhook_secret:
                headers["X-Webhook-Secret"] = self.webhook_secret
            
            response = requests.get(status_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {
                    "status": "not_found",
                    "message": "Deployment not found or not yet started"
                }
            else:
                logger.error(f"Deployment status check failed: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"Status check failed: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Failed to check deployment status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def cancel_deployment(self, organization_id: str, deployment_id: Optional[str] = None) -> bool:
        """Cancel an ongoing deployment"""
        if not self.enabled:
            logger.info(f"Container deployment disabled - would cancel for org {organization_id}")
            return True
        
        try:
            cancel_data = {
                "event": "organization.container.cancel",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "organization_id": organization_id,
                    "deployment_id": deployment_id,
                    "reason": "user_requested"
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Event-Type": "organization.container.cancel"
            }
            
            if self.webhook_secret:
                headers["X-Webhook-Secret"] = self.webhook_secret
                signature = self._generate_webhook_signature(cancel_data)
                headers["X-Signature"] = signature
            
            response = requests.post(
                f"{self.webhook_url}/cancel",
                json=cancel_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Container deployment cancelled for organization {organization_id}")
                return True
            else:
                logger.error(f"Failed to cancel deployment: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling deployment: {e}")
            return False
    
    async def update_container_config(self, organization_id: str, config_updates: Dict[str, Any]) -> bool:
        """Update container configuration for existing deployment"""
        if not self.enabled:
            logger.info(f"Container deployment disabled - would update config for org {organization_id}")
            return True
        
        try:
            update_data = {
                "event": "organization.container.update",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "organization_id": organization_id,
                    "config_updates": config_updates
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Event-Type": "organization.container.update"
            }
            
            if self.webhook_secret:
                headers["X-Webhook-Secret"] = self.webhook_secret
                signature = self._generate_webhook_signature(update_data)
                headers["X-Signature"] = signature
            
            response = requests.post(
                f"{self.webhook_url}/update",
                json=update_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Container configuration updated for organization {organization_id}")
                return True
            else:
                logger.error(f"Failed to update container config: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating container config: {e}")
            return False
    
    async def scale_container(self, organization_id: str, scale_config: Dict[str, Any]) -> bool:
        """Scale container resources for organization"""
        if not self.enabled:
            logger.info(f"Container deployment disabled - would scale for org {organization_id}")
            return True
        
        try:
            scale_data = {
                "event": "organization.container.scale",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "organization_id": organization_id,
                    "scale_config": scale_config
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Event-Type": "organization.container.scale"
            }
            
            if self.webhook_secret:
                headers["X-Webhook-Secret"] = self.webhook_secret
                signature = self._generate_webhook_signature(scale_data)
                headers["X-Signature"] = signature
            
            response = requests.post(
                f"{self.webhook_url}/scale",
                json=scale_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Container scaled for organization {organization_id}")
                return True
            else:
                logger.error(f"Failed to scale container: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error scaling container: {e}")
            return False
    
    async def get_container_logs(self, organization_id: str, lines: int = 100) -> Optional[str]:
        """Get container logs for organization"""
        if not self.enabled:
            return "Container deployment disabled - no logs available"
        
        try:
            logs_url = f"{self.webhook_url}/logs/{organization_id}"
            params = {"lines": lines}
            
            headers = {}
            if self.webhook_secret:
                headers["X-Webhook-Secret"] = self.webhook_secret
            
            response = requests.get(logs_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Failed to get container logs: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting container logs: {e}")
            return None
    
    def _generate_webhook_signature(self, payload: Dict[str, Any]) -> str:
        """Generate webhook signature for security"""
        if not self.webhook_secret:
            return ""
        
        try:
            import hmac
            import hashlib
            
            payload_string = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                self.webhook_secret.encode(),
                payload_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return f"sha256={signature}"
            
        except Exception as e:
            logger.error(f"Error generating webhook signature: {e}")
            return ""
    
    def get_status(self) -> Dict[str, Any]:
        """Get deployment service status and configuration"""
        return {
            "enabled": self.enabled,
            "webhook_configured": bool(self.webhook_url),
            "webhook_secured": bool(self.webhook_secret),
            "webhook_url": self.webhook_url if self.webhook_url else "not_configured"
        }


# Global deployment service instance
deployment_service = ContainerDeploymentService()
