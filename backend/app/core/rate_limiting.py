"""
Advanced API Rate Limiting and Throttling System

This module provides comprehensive rate limiting with:
- Multiple rate limiting strategies (fixed window, sliding window, token bucket)
- User-based and IP-based rate limiting
- Role-based rate limits
- Rate limit monitoring and analytics  
- Adaptive rate limiting
- Rate limit exemptions and overrides
"""

import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Callable, Any
from functools import wraps
from dataclasses import dataclass
from enum import Enum

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler  # type: ignore[import-untyped]
    from slowapi.util import get_remote_address  # type: ignore[import-untyped]
    from slowapi.errors import RateLimitExceeded  # type: ignore[import-untyped]
    from limits import RateLimitItem, parse  # type: ignore[import-untyped]
    SLOWAPI_AVAILABLE = True
except ImportError:
    RateLimitExceeded = Exception
    SLOWAPI_AVAILABLE = False

from app.core.redis_caching import advanced_cache

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


class RateLimitScope(Enum):
    """Rate limit scope."""
    GLOBAL = "global"
    USER = "user"
    IP = "ip"
    ENDPOINT = "endpoint"
    ROLE = "role"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests: int = 100
    window: int = 3600  # seconds
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    scope: RateLimitScope = RateLimitScope.IP
    burst_requests: int = 0  # Additional burst capacity
    burst_window: int = 60  # Burst window in seconds
    exempt_roles: Optional[List[str]] = None
    exempt_ips: Optional[List[str]] = None
    custom_key_func: Optional[Callable] = None

    def __post_init__(self):
        if self.exempt_roles is None:
            self.exempt_roles = []
        if self.exempt_ips is None:
            self.exempt_ips = []


@dataclass
class RateLimitInfo:
    """Rate limit information."""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: int
    strategy: str
    scope: str
    exceeded: bool = False
    current_usage: int = 0


class RateLimitStorage:
    """Storage backend for rate limit data."""
    
    def __init__(self):
        self.cache = advanced_cache
    
    def get_usage(self, key: str) -> Dict[str, Any]:
        """Get current usage for a rate limit key."""
        try:
            usage_data = self.cache.get('rate_limit', key)
            if usage_data:
                return usage_data
            return {
                "count": 0,
                "window_start": time.time(),
                "requests": [],
                "burst_count": 0,
                "burst_window_start": time.time()
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit usage for key {key}: {e}")
            return {"count": 0, "window_start": time.time(), "requests": []}
    
    def update_usage(self, key: str, usage_data: Dict[str, Any], ttl: int = 3600):
        """Update usage data for a rate limit key."""
        try:
            return self.cache.set('rate_limit', key, usage_data, ttl=ttl)
        except Exception as e:
            logger.error(f"Failed to update rate limit usage for key {key}: {e}")
            return False
    
    def cleanup_expired(self, key: str, window_seconds: int):
        """Clean up expired entries for sliding window."""
        try:
            usage_data = self.get_usage(key)
            current_time = time.time()
            
            # Remove expired requests
            usage_data["requests"] = [
                req_time for req_time in usage_data["requests"]
                if current_time - req_time < window_seconds
            ]
            
            usage_data["count"] = len(usage_data["requests"])
            self.update_usage(key, usage_data, ttl=window_seconds)
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries for key {key}: {e}")


class RateLimitChecker:
    """Rate limit checking logic."""
    
    def __init__(self, storage: RateLimitStorage):
        self.storage = storage
    
    def check_fixed_window(self, key: str, config: RateLimitConfig) -> RateLimitInfo:
        """Check rate limit using fixed window strategy."""
        usage_data = self.storage.get_usage(key)
        current_time = time.time()
        
        # Check if we need to reset the window
        time_since_window_start = current_time - usage_data["window_start"]
        if time_since_window_start >= config.window:
            usage_data = {
                "count": 0,
                "window_start": current_time,
                "requests": [],
                "burst_count": 0,
                "burst_window_start": current_time
            }
        
        # Check burst limits if configured
        burst_exceeded = False
        if config.burst_requests > 0:
            burst_time_since_start = current_time - usage_data.get("burst_window_start", current_time)
            if burst_time_since_start >= config.burst_window:
                usage_data["burst_count"] = 0
                usage_data["burst_window_start"] = current_time
            
            if usage_data.get("burst_count", 0) >= config.burst_requests:
                burst_exceeded = True
        
        # Calculate remaining requests
        remaining = max(0, config.requests - usage_data["count"])
        reset_time = datetime.fromtimestamp(usage_data["window_start"] + config.window)
        retry_after = int((usage_data["window_start"] + config.window) - current_time)
        
        exceeded = usage_data["count"] >= config.requests or burst_exceeded
        
        return RateLimitInfo(
            limit=config.requests,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=max(0, retry_after),
            strategy=config.strategy.value,
            scope=config.scope.value,
            exceeded=exceeded,
            current_usage=usage_data["count"]
        )
    
    def check_sliding_window(self, key: str, config: RateLimitConfig) -> RateLimitInfo:
        """Check rate limit using sliding window strategy."""
        # Clean up expired entries first
        self.storage.cleanup_expired(key, config.window)
        
        usage_data = self.storage.get_usage(key)
        current_time = time.time()
        
        # Count requests in the sliding window
        window_start = current_time - config.window
        recent_requests = [
            req_time for req_time in usage_data["requests"]
            if req_time >= window_start
        ]
        
        current_count = len(recent_requests)
        remaining = max(0, config.requests - current_count)
        reset_time = datetime.fromtimestamp(current_time + config.window)
        
        # For sliding window, retry_after is based on oldest request
        if recent_requests and current_count >= config.requests:
            oldest_request = min(recent_requests)
            retry_after = int((oldest_request + config.window) - current_time)
        else:
            retry_after = 0
        
        exceeded = current_count >= config.requests
        
        return RateLimitInfo(
            limit=config.requests,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=max(0, retry_after),
            strategy=config.strategy.value,
            scope=config.scope.value,
            exceeded=exceeded,
            current_usage=current_count
        )
    
    def check_token_bucket(self, key: str, config: RateLimitConfig) -> RateLimitInfo:
        """Check rate limit using token bucket strategy."""
        usage_data = self.storage.get_usage(key)
        current_time = time.time()
        
        # Initialize bucket if needed
        if "tokens" not in usage_data:
            usage_data["tokens"] = config.requests
            usage_data["last_refill"] = current_time
        
        # Calculate tokens to add based on time elapsed
        time_elapsed = current_time - usage_data["last_refill"]
        tokens_to_add = int(time_elapsed * (config.requests / config.window))
        
        # Refill tokens
        usage_data["tokens"] = min(config.requests, usage_data["tokens"] + tokens_to_add)
        usage_data["last_refill"] = current_time
        
        remaining = usage_data["tokens"]
        exceeded = remaining <= 0
        
        # For token bucket, reset time is when we'll have tokens again
        if exceeded:
            seconds_for_next_token = config.window / config.requests
            reset_time = datetime.fromtimestamp(current_time + seconds_for_next_token)
            retry_after = int(seconds_for_next_token)
        else:
            reset_time = datetime.fromtimestamp(current_time + config.window)
            retry_after = 0
        
        return RateLimitInfo(
            limit=config.requests,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
            strategy=config.strategy.value,
            scope=config.scope.value,
            exceeded=exceeded,
            current_usage=config.requests - remaining
        )
    
    def record_request(self, key: str, config: RateLimitConfig):
        """Record a request for rate limiting."""
        usage_data = self.storage.get_usage(key)
        current_time = time.time()
        
        if config.strategy == RateLimitStrategy.FIXED_WINDOW:
            usage_data["count"] += 1
            
            # Handle burst tracking
            if config.burst_requests > 0:
                burst_time_since_start = current_time - usage_data.get("burst_window_start", current_time)
                if burst_time_since_start >= config.burst_window:
                    usage_data["burst_count"] = 0
                    usage_data["burst_window_start"] = current_time
                usage_data["burst_count"] = usage_data.get("burst_count", 0) + 1
            
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            usage_data["requests"].append(current_time)
            usage_data["count"] = len(usage_data["requests"])
            
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            usage_data["tokens"] = max(0, usage_data.get("tokens", config.requests) - 1)
        
        self.storage.update_usage(key, usage_data, ttl=config.window * 2)


class AdvancedRateLimiter:
    """
    Advanced rate limiting system with multiple strategies and scopes.
    """
    
    def __init__(self):
        self.storage = RateLimitStorage()
        self.checker = RateLimitChecker(self.storage)
        self.configs: Dict[str, RateLimitConfig] = {}
        self.global_config = RateLimitConfig()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "exempted_requests": 0,
            "start_time": datetime.utcnow()
        }
    
    def add_rate_limit(self, name: str, config: RateLimitConfig):
        """Add a named rate limit configuration."""
        self.configs[name] = config
        logger.info(f"Added rate limit '{name}': {config.requests}/{config.window}s")
    
    def generate_key(self, request: Request, config: RateLimitConfig, user_id: Optional[int] = None) -> str:
        """Generate a rate limit key based on scope and configuration."""
        
        if config.custom_key_func:
            return config.custom_key_func(request, user_id)
        
        key_parts = ["rate_limit"]
        
        if config.scope == RateLimitScope.GLOBAL:
            key_parts.append("global")
        elif config.scope == RateLimitScope.USER and user_id:
            key_parts.append(f"user:{user_id}")
        elif config.scope == RateLimitScope.IP:
            try:
                if SLOWAPI_AVAILABLE:
                    from slowapi.util import get_remote_address as get_ip
                    ip = get_ip(request)
                else:
                    ip = getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
            except Exception:
                ip = 'unknown'
            key_parts.append(f"ip:{ip}")
        elif config.scope == RateLimitScope.ENDPOINT:
            endpoint = f"{request.method}:{request.url.path}"
            key_parts.append(f"endpoint:{hashlib.md5(endpoint.encode()).hexdigest()[:8]}")
        elif config.scope == RateLimitScope.ROLE:
            # This would need role information from the request
            role = getattr(request.state, 'user_role', 'anonymous')
            key_parts.append(f"role:{role}")
        
        return ":".join(key_parts)
    
    def is_exempt(self, request: Request, config: RateLimitConfig, user_role: Optional[str] = None) -> bool:
        """Check if a request is exempt from rate limiting."""
        
        # Check role exemptions
        if user_role and config.exempt_roles and user_role in config.exempt_roles:
            return True
        
        # Check IP exemptions
        try:
            if SLOWAPI_AVAILABLE:
                from slowapi.util import get_remote_address as get_ip
                ip = get_ip(request)
            else:
                ip = getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
        except Exception:
            ip = 'unknown'
            
        if config.exempt_ips and ip in config.exempt_ips:
            return True
        
        return False
    
    def check_rate_limit(
        self, 
        request: Request, 
        config_name: str = "default",
        user_id: Optional[int] = None,
        user_role: Optional[str] = None
    ) -> RateLimitInfo:
        """
        Check if a request should be rate limited.
        
        Args:
            request: FastAPI request object
            config_name: Name of the rate limit configuration to use
            user_id: User ID for user-based rate limiting
            user_role: User role for role-based exemptions
            
        Returns:
            RateLimitInfo: Rate limit status information
        """
        
        self.stats["total_requests"] += 1
        
        # Get configuration
        config = self.configs.get(config_name, self.global_config)
        
        # Check exemptions
        if self.is_exempt(request, config, user_role):
            self.stats["exempted_requests"] += 1
            return RateLimitInfo(
                limit=config.requests,
                remaining=config.requests,
                reset_time=datetime.utcnow() + timedelta(seconds=config.window),
                retry_after=0,
                strategy=config.strategy.value,
                scope=config.scope.value,
                exceeded=False
            )
        
        # Generate rate limit key
        key = self.generate_key(request, config, user_id)
        
        # Check rate limit based on strategy
        if config.strategy == RateLimitStrategy.FIXED_WINDOW:
            rate_info = self.checker.check_fixed_window(key, config)
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            rate_info = self.checker.check_sliding_window(key, config)
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            rate_info = self.checker.check_token_bucket(key, config)
        else:
            # Fallback to fixed window
            rate_info = self.checker.check_fixed_window(key, config)
        
        # Record the request if not exceeded
        if not rate_info.exceeded:
            self.checker.record_request(key, config)
        else:
            self.stats["blocked_requests"] += 1
        
        return rate_info
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        uptime = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
        
        return {
            "total_requests": self.stats["total_requests"],
            "blocked_requests": self.stats["blocked_requests"],
            "exempted_requests": self.stats["exempted_requests"],
            "block_rate": (self.stats["blocked_requests"] / max(1, self.stats["total_requests"])) * 100,
            "requests_per_second": self.stats["total_requests"] / max(1, uptime),
            "uptime_seconds": uptime,
            "active_configs": list(self.configs.keys()),
            "config_count": len(self.configs)
        }


# Global rate limiter instance
rate_limiter = AdvancedRateLimiter()

# Set up default configurations
default_configs = {
    "default": RateLimitConfig(requests=100, window=3600, scope=RateLimitScope.IP),
    "auth": RateLimitConfig(requests=10, window=900, scope=RateLimitScope.IP),  # Auth endpoints
    "api": RateLimitConfig(requests=1000, window=3600, scope=RateLimitScope.USER),  # API endpoints
    "upload": RateLimitConfig(requests=5, window=300, scope=RateLimitScope.USER),  # File uploads
    "strict": RateLimitConfig(requests=20, window=600, scope=RateLimitScope.IP),  # Strict endpoints
}

for name, config in default_configs.items():
    rate_limiter.add_rate_limit(name, config)


# Rate limiting decorators and middleware
def rate_limit(config_name: str = "default"):
    """
    Decorator to apply rate limiting to FastAPI endpoints.
    
    Args:
        config_name: Name of the rate limit configuration to use
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if hasattr(arg, 'method') and hasattr(arg, 'url'):
                    request = arg
                    break
            
            if not request:
                # Look in kwargs
                request = kwargs.get('request')
            
            if not request:
                logger.warning("Could not find request object for rate limiting")
                return await func(*args, **kwargs)
            
            # Check rate limit
            rate_info = rate_limiter.check_rate_limit(request, config_name)
            
            if rate_info.exceeded:
                headers = {
                    "X-RateLimit-Limit": str(rate_info.limit),
                    "X-RateLimit-Remaining": str(rate_info.remaining),
                    "X-RateLimit-Reset": str(int(rate_info.reset_time.timestamp())),
                    "Retry-After": str(rate_info.retry_after)
                }
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": rate_info.limit,
                        "remaining": rate_info.remaining,
                        "reset_time": rate_info.reset_time.isoformat(),
                        "retry_after": rate_info.retry_after
                    },
                    headers=headers
                )
            
            # Add rate limit headers to response
            response = await func(*args, **kwargs)
            
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(rate_info.limit)
                response.headers["X-RateLimit-Remaining"] = str(rate_info.remaining)
                response.headers["X-RateLimit-Reset"] = str(int(rate_info.reset_time.timestamp()))
            
            return response
        
        return wrapper
    return decorator


# Dependency for FastAPI
async def check_rate_limit_dependency(
    request: Request, 
    config_name: str = "default"
) -> RateLimitInfo:
    """FastAPI dependency for rate limiting."""
    rate_info = rate_limiter.check_rate_limit(request, config_name)
    
    if rate_info.exceeded:
        headers = {
            "X-RateLimit-Limit": str(rate_info.limit),
            "X-RateLimit-Remaining": str(rate_info.remaining),
            "X-RateLimit-Reset": str(int(rate_info.reset_time.timestamp())),
            "Retry-After": str(rate_info.retry_after)
        }
        
        detail = {
            "error": "Rate limit exceeded",
            "limit": rate_info.limit,
            "remaining": rate_info.remaining,
            "reset_time": rate_info.reset_time.isoformat(),
            "retry_after": rate_info.retry_after
        }
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers
        )
    
    return rate_info


# Convenience functions
def add_rate_limit_config(name: str, config: RateLimitConfig):
    """Add a new rate limit configuration."""
    rate_limiter.add_rate_limit(name, config)


def get_rate_limit_stats() -> Dict[str, Any]:
    """Get rate limiting statistics."""
    return rate_limiter.get_stats()
