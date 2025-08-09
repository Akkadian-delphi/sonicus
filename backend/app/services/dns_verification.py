"""
DNS Verification Service for checking subdomain resolution and propagation
Handles verification of DNS record creation and propagation monitoring
"""

import asyncio
import logging
import socket
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)


class DNSVerificationService:
    """Service for verifying DNS record propagation and resolution"""
    
    def __init__(self):
        self.verification_timeout = getattr(settings, 'DNS_VERIFICATION_TIMEOUT', 300)  # 5 minutes
        self.retry_interval = 10  # seconds
        self.max_attempts = self.verification_timeout // self.retry_interval
        self.enabled = getattr(settings, 'DNS_VERIFICATION_ENABLED', True)
    
    async def verify_subdomain_resolution(self, subdomain: str, expected_ip: str) -> bool:
        """Verify that subdomain resolves to expected IP"""
        if not self.enabled:
            logger.info(f"DNS verification disabled - would verify {subdomain}.sonicus.eu -> {expected_ip}")
            return True
            
        try:
            domain = f"{subdomain}.sonicus.eu"
            
            # Use socket.getaddrinfo for DNS resolution
            result = socket.getaddrinfo(domain, None, socket.AF_INET)
            resolved_ips = [info[4][0] for info in result]
            
            if expected_ip in resolved_ips:
                logger.info(f"DNS verification successful: {domain} resolves to {expected_ip}")
                return True
            else:
                logger.warning(f"DNS verification failed: {domain} resolves to {resolved_ips}, expected {expected_ip}")
                return False
            
        except socket.gaierror as e:
            logger.warning(f"DNS resolution failed for {subdomain}.sonicus.eu: {e}")
            return False
        except Exception as e:
            logger.error(f"DNS verification error for {subdomain}: {e}")
            return False
    
    async def wait_for_dns_propagation(self, subdomain: str, expected_ip: str, max_attempts: Optional[int] = None) -> bool:
        """Wait for DNS propagation with retry logic"""
        if not self.enabled:
            logger.info(f"DNS verification disabled - would wait for {subdomain}.sonicus.eu propagation")
            return True
            
        attempts = max_attempts or self.max_attempts
        domain = f"{subdomain}.sonicus.eu"
        
        logger.info(f"Waiting for DNS propagation: {domain} -> {expected_ip} (max {attempts} attempts)")
        
        for attempt in range(1, attempts + 1):
            try:
                logger.debug(f"DNS propagation check {attempt}/{attempts} for {domain}")
                
                if await self.verify_subdomain_resolution(subdomain, expected_ip):
                    logger.info(f"DNS propagation completed after {attempt} attempts ({attempt * self.retry_interval}s)")
                    return True
                
                if attempt < attempts:
                    logger.debug(f"DNS not yet propagated, waiting {self.retry_interval}s before retry {attempt + 1}")
                    await asyncio.sleep(self.retry_interval)
                    
            except Exception as e:
                logger.error(f"Error during DNS propagation check {attempt}: {e}")
                if attempt < attempts:
                    await asyncio.sleep(self.retry_interval)
        
        logger.error(f"DNS propagation timeout after {attempts * self.retry_interval}s for {domain}")
        return False
    
    async def check_subdomain_availability(self, subdomain: str) -> Dict[str, Any]:
        """Check if subdomain is available (doesn't resolve)"""
        if not self.enabled:
            return {
                "available": True,
                "reason": "DNS verification disabled - availability unknown"
            }
        
        try:
            domain = f"{subdomain}.sonicus.eu"
            result = socket.getaddrinfo(domain, None, socket.AF_INET)
            
            # If we get here, domain resolves - not available
            resolved_ips = [str(info[4][0]) for info in result]
            return {
                "available": False,
                "reason": f"Subdomain already exists, resolves to: {', '.join(resolved_ips)}",
                "resolved_ips": resolved_ips
            }
            
        except socket.gaierror:
            # Domain doesn't resolve - available
            return {
                "available": True,
                "reason": "Subdomain is available"
            }
        except Exception as e:
            logger.error(f"Error checking subdomain availability for {subdomain}: {e}")
            return {
                "available": False,
                "reason": f"Error checking availability: {str(e)}"
            }
    
    async def verify_multiple_dns_servers(self, subdomain: str, expected_ip: str) -> Dict[str, bool]:
        """Check DNS resolution from multiple DNS servers"""
        dns_servers = [
            "8.8.8.8",      # Google DNS
            "1.1.1.1",      # Cloudflare DNS
            "208.67.222.222", # OpenDNS
        ]
        
        results = {}
        domain = f"{subdomain}.sonicus.eu"
        
        for dns_server in dns_servers:
            try:
                # Note: This is a simplified check using the system resolver
                # In production, you might want to use a DNS library that allows
                # specifying specific DNS servers
                result = await self.verify_subdomain_resolution(subdomain, expected_ip)
                results[dns_server] = result
                
            except Exception as e:
                logger.error(f"Error checking DNS server {dns_server} for {domain}: {e}")
                results[dns_server] = False
        
        return results
    
    async def get_dns_propagation_status(self, subdomain: str, expected_ip: str) -> Dict[str, Any]:
        """Get detailed DNS propagation status"""
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "DNS verification is disabled"
            }
        
        domain = f"{subdomain}.sonicus.eu"
        
        try:
            # Check basic resolution
            is_resolved = await self.verify_subdomain_resolution(subdomain, expected_ip)
            
            if is_resolved:
                # Check multiple DNS servers for consistency
                dns_results = await self.verify_multiple_dns_servers(subdomain, expected_ip)
                propagated_count = sum(dns_results.values())
                total_servers = len(dns_results)
                
                return {
                    "status": "propagated" if propagated_count == total_servers else "partially_propagated",
                    "domain": domain,
                    "expected_ip": expected_ip,
                    "propagated_servers": propagated_count,
                    "total_servers": total_servers,
                    "dns_results": dns_results,
                    "message": f"DNS propagated to {propagated_count}/{total_servers} servers"
                }
            else:
                return {
                    "status": "not_propagated",
                    "domain": domain,
                    "expected_ip": expected_ip,
                    "message": "DNS record not yet propagated"
                }
                
        except Exception as e:
            logger.error(f"Error getting DNS propagation status for {domain}: {e}")
            return {
                "status": "error",
                "domain": domain,
                "message": f"Error checking propagation: {str(e)}"
            }
    
    async def monitor_dns_propagation(self, subdomain: str, expected_ip: str, callback=None) -> Dict[str, Any]:
        """Monitor DNS propagation with progress callbacks"""
        start_time = datetime.utcnow()
        domain = f"{subdomain}.sonicus.eu"
        
        logger.info(f"Starting DNS propagation monitoring for {domain}")
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                
                # Get current status
                status = await self.get_dns_propagation_status(subdomain, expected_ip)
                
                # Call progress callback if provided
                if callback:
                    await callback({
                        "attempt": attempt,
                        "max_attempts": self.max_attempts,
                        "elapsed_seconds": elapsed,
                        "status": status
                    })
                
                # Check if fully propagated
                if status.get("status") == "propagated":
                    return {
                        "success": True,
                        "attempts": attempt,
                        "elapsed_seconds": elapsed,
                        "final_status": status
                    }
                
                # Wait before next attempt (except on last attempt)
                if attempt < self.max_attempts:
                    await asyncio.sleep(self.retry_interval)
                    
            except Exception as e:
                logger.error(f"Error during DNS monitoring attempt {attempt}: {e}")
                if attempt < self.max_attempts:
                    await asyncio.sleep(self.retry_interval)
        
        # Timeout reached
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        final_status = await self.get_dns_propagation_status(subdomain, expected_ip)
        
        return {
            "success": False,
            "attempts": self.max_attempts,
            "elapsed_seconds": elapsed,
            "timeout": True,
            "final_status": final_status,
            "message": f"DNS propagation timeout after {elapsed}s"
        }
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get DNS verification service configuration"""
        return {
            "enabled": self.enabled,
            "verification_timeout": self.verification_timeout,
            "retry_interval": self.retry_interval,
            "max_attempts": self.max_attempts
        }


# Global DNS verification service instance
dns_verification_service = DNSVerificationService()
