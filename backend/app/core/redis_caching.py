"""
Advanced Redis Caching System

This module provides comprehensive caching functionality with:
- Intelligent cache key management
- Automatic cache invalidation
- Cache warming strategies
- Performance monitoring
- Multi-level caching support
- Cache statistics and analytics
"""

import logging
import json
import hashlib
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from dataclasses import dataclass
import threading

from app.core.cache import redis_client

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for cache behavior."""
    default_ttl: int = 3600  # 1 hour
    max_key_length: int = 250
    compression_enabled: bool = True
    version: str = "v1"
    key_prefix: str = "sonicus"


class CacheKey:
    """Intelligent cache key generator and manager."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
    
    def generate(self, namespace: str, identifier: Union[str, Dict, List], **kwargs) -> str:
        """
        Generate a cache key with consistent formatting.
        
        Args:
            namespace: Cache namespace (e.g., 'user', 'org', 'sound')
            identifier: Primary identifier (can be complex object)
            **kwargs: Additional key components
            
        Returns:
            str: Generated cache key
        """
        try:
            # Start with prefix and version
            key_parts = [self.config.key_prefix, self.config.version, namespace]
            
            # Add identifier
            if isinstance(identifier, (dict, list)):
                # Hash complex objects for consistent keys
                identifier_str = json.dumps(identifier, sort_keys=True, default=str)
                identifier_hash = hashlib.md5(identifier_str.encode()).hexdigest()[:8]
                key_parts.append(identifier_hash)
            else:
                key_parts.append(str(identifier))
            
            # Add additional components
            for key, value in sorted(kwargs.items()):
                if value is not None:
                    key_parts.append(f"{key}:{value}")
            
            # Join and validate length
            cache_key = ":".join(key_parts)
            
            if len(cache_key) > self.config.max_key_length:
                # Hash the key if it's too long
                key_hash = hashlib.md5(cache_key.encode()).hexdigest()
                cache_key = f"{self.config.key_prefix}:hashed:{key_hash}"
            
            return cache_key
            
        except Exception as e:
            logger.error(f"Failed to generate cache key: {e}")
            # Fallback to simple key
            return f"{self.config.key_prefix}:fallback:{hash(str(identifier))}"
    
    def parse(self, cache_key: str) -> Dict[str, Optional[str]]:
        """Parse a cache key back into components."""
        try:
            parts = cache_key.split(":")
            if len(parts) >= 3:
                return {
                    "prefix": parts[0],
                    "version": parts[1],
                    "namespace": parts[2],
                    "identifier": parts[3] if len(parts) > 3 else None,
                    "full_key": cache_key
                }
        except Exception as e:
            logger.warning(f"Failed to parse cache key '{cache_key}': {e}")
        
        return {"full_key": cache_key}


class CacheStats:
    """Cache performance statistics."""
    
    def __init__(self):
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
            "total_requests": 0,
            "cache_size_bytes": 0,
            "avg_response_time": 0.0,
            "start_time": datetime.utcnow().isoformat()
        }
        self._lock = threading.Lock()
    
    def record_hit(self, response_time: float = 0.0):
        """Record a cache hit."""
        with self._lock:
            self.stats["hits"] += 1
            self.stats["total_requests"] += 1
            self._update_avg_response_time(response_time)
    
    def record_miss(self, response_time: float = 0.0):
        """Record a cache miss."""
        with self._lock:
            self.stats["misses"] += 1
            self.stats["total_requests"] += 1
            self._update_avg_response_time(response_time)
    
    def record_set(self):
        """Record a cache set operation."""
        with self._lock:
            self.stats["sets"] += 1
    
    def record_delete(self):
        """Record a cache delete operation."""
        with self._lock:
            self.stats["deletes"] += 1
    
    def record_error(self):
        """Record a cache error."""
        with self._lock:
            self.stats["errors"] += 1
    
    def _update_avg_response_time(self, response_time: float):
        """Update average response time."""
        if self.stats["total_requests"] > 1:
            current_avg = self.stats["avg_response_time"]
            new_avg = ((current_avg * (self.stats["total_requests"] - 1)) + response_time) / self.stats["total_requests"]
            self.stats["avg_response_time"] = new_avg
        else:
            self.stats["avg_response_time"] = response_time
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.stats["hits"] + self.stats["misses"]
        return (self.stats["hits"] / total * 100) if total > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get all statistics."""
        with self._lock:
            stats = self.stats.copy()
        
        stats["hit_rate_percent"] = self.get_hit_rate()
        stats["uptime_seconds"] = (datetime.utcnow() - datetime.fromisoformat(stats["start_time"])).total_seconds()
        
        return stats


class AdvancedRedisCache:
    """
    Advanced Redis caching system with intelligent features.
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.key_generator = CacheKey(self.config)
        self.stats = CacheStats()
        self.redis_client = redis_client
    
    def get(self, namespace: str, identifier: Union[str, Dict, List], **kwargs) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            namespace: Cache namespace
            identifier: Cache identifier
            **kwargs: Additional key components
            
        Returns:
            Any: Cached value or None if not found
        """
        start_time = time.time()
        
        try:
            cache_key = self.key_generator.generate(namespace, identifier, **kwargs)
            
            # Try to get from Redis
            cached_data = self.redis_client.get_json(cache_key)
            
            response_time = time.time() - start_time
            
            if cached_data is not None:
                self.stats.record_hit(response_time)
                
                # Check if it's a wrapped cache object with metadata
                if isinstance(cached_data, dict) and "_cache_meta" in cached_data:
                    # Check expiration
                    if self._is_expired(cached_data["_cache_meta"]):
                        self.delete(namespace, identifier, **kwargs)
                        self.stats.record_miss(response_time)
                        return None
                    
                    return cached_data["data"]
                else:
                    return cached_data
            else:
                self.stats.record_miss(response_time)
                return None
                
        except Exception as e:
            logger.error(f"Cache get error for {namespace}:{identifier}: {e}")
            self.stats.record_error()
            return None
    
    def set(
        self, 
        namespace: str, 
        identifier: Union[str, Dict, List], 
        value: Any, 
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            namespace: Cache namespace
            identifier: Cache identifier
            value: Value to cache
            ttl: Time to live in seconds
            **kwargs: Additional key components
            
        Returns:
            bool: Success status
        """
        try:
            cache_key = self.key_generator.generate(namespace, identifier, **kwargs)
            ttl = ttl or self.config.default_ttl
            
            # Wrap value with metadata
            cache_data = {
                "data": value,
                "_cache_meta": {
                    "created_at": datetime.utcnow().isoformat(),
                    "ttl": ttl,
                    "namespace": namespace,
                    "identifier": str(identifier),
                    "version": self.config.version
                }
            }
            
            success = self.redis_client.set_json(cache_key, cache_data, expire=ttl)
            
            if success:
                self.stats.record_set()
            else:
                self.stats.record_error()
            
            return success
            
        except Exception as e:
            logger.error(f"Cache set error for {namespace}:{identifier}: {e}")
            self.stats.record_error()
            return False
    
    def delete(self, namespace: str, identifier: Union[str, Dict, List], **kwargs) -> bool:
        """
        Delete a value from cache.
        
        Args:
            namespace: Cache namespace
            identifier: Cache identifier
            **kwargs: Additional key components
            
        Returns:
            bool: Success status
        """
        try:
            cache_key = self.key_generator.generate(namespace, identifier, **kwargs)
            success = self.redis_client.delete(cache_key)
            
            if success:
                self.stats.record_delete()
            
            return success
            
        except Exception as e:
            logger.error(f"Cache delete error for {namespace}:{identifier}: {e}")
            self.stats.record_error()
            return False
    
    def invalidate_namespace(self, namespace: str) -> int:
        """
        Invalidate all cache entries in a namespace.
        
        Args:
            namespace: Namespace to invalidate
            
        Returns:
            int: Number of keys deleted
        """
        try:
            if not self.redis_client.client:
                return 0
            
            pattern = f"{self.config.key_prefix}:{self.config.version}:{namespace}:*"
            deleted_count = 0
            
            for key in self.redis_client.client.scan_iter(match=pattern):
                try:
                    self.redis_client.client.delete(key)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete cache key {key}: {e}")
            
            logger.info(f"Invalidated {deleted_count} cache entries in namespace '{namespace}'")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate namespace '{namespace}': {e}")
            return 0
    
    def _is_expired(self, cache_meta: Dict[str, Any]) -> bool:
        """Check if cached data is expired."""
        try:
            created_at = datetime.fromisoformat(cache_meta["created_at"])
            ttl = cache_meta.get("ttl", self.config.default_ttl)
            expiry_time = created_at + timedelta(seconds=ttl)
            
            return datetime.utcnow() > expiry_time
            
        except Exception as e:
            logger.warning(f"Failed to check cache expiration: {e}")
            return True  # Assume expired on error
    
    def warm_cache(self, warm_functions: List[Callable]) -> Dict[str, Any]:
        """
        Warm the cache by pre-loading frequently accessed data.
        
        Args:
            warm_functions: List of functions to call for cache warming
            
        Returns:
            Dict: Warming results
        """
        results = {
            "started_at": datetime.utcnow().isoformat(),
            "functions_executed": 0,
            "cache_entries_created": 0,
            "errors": []
        }
        
        try:
            for func in warm_functions:
                try:
                    func()
                    results["functions_executed"] += 1
                except Exception as e:
                    error_msg = f"Cache warming function {func.__name__} failed: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Estimate cache entries created (approximate)
            results["cache_entries_created"] = self.stats.stats["sets"]
            results["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Cache warming completed: {results['functions_executed']} functions executed")
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            results["errors"].append(str(e))
        
        return results
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get comprehensive cache information."""
        try:
            info = {
                "config": {
                    "default_ttl": self.config.default_ttl,
                    "key_prefix": self.config.key_prefix,
                    "version": self.config.version
                },
                "stats": self.stats.get_stats(),
                "redis_info": {},
                "namespaces": {}
            }
            
            # Get Redis info if available
            if self.redis_client.client:
                try:
                    # Use direct Redis client info method
                    raw_redis_client = self.redis_client.client
                    if hasattr(raw_redis_client, 'info'):
                        redis_info = raw_redis_client.info()
                        
                        # Ensure redis_info is a dict
                        if isinstance(redis_info, dict):
                            info["redis_info"] = {
                                "used_memory": redis_info.get("used_memory", 0),
                                "used_memory_human": redis_info.get("used_memory_human", "0B"),
                                "connected_clients": redis_info.get("connected_clients", 0),
                                "total_commands_processed": redis_info.get("total_commands_processed", 0),
                                "keyspace_hits": redis_info.get("keyspace_hits", 0),
                                "keyspace_misses": redis_info.get("keyspace_misses", 0)
                            }
                        else:
                            logger.warning("Redis info() returned non-dict result")
                            info["redis_info"] = {}
                    else:
                        logger.warning("Redis client does not have info() method")
                        info["redis_info"] = {}
                except Exception as e:
                    logger.warning(f"Failed to get Redis info: {e}")
                    info["redis_info"] = {
                        "used_memory": 0,
                        "used_memory_human": "0B",
                        "connected_clients": 0,
                        "total_commands_processed": 0,
                        "keyspace_hits": 0,
                        "keyspace_misses": 0
                    }
            
            # Analyze namespaces
            info["namespaces"] = self._analyze_namespaces()
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {"error": str(e)}
    
    def _analyze_namespaces(self) -> Dict[str, Dict[str, Any]]:
        """Analyze cache usage by namespace."""
        namespaces = {}
        
        try:
            if not self.redis_client.client:
                return namespaces
            
            pattern = f"{self.config.key_prefix}:{self.config.version}:*"
            
            for key in self.redis_client.client.scan_iter(match=pattern, count=1000):
                try:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    parsed_key = self.key_generator.parse(key_str)
                    namespace = parsed_key.get("namespace", "unknown")
                    
                    if namespace not in namespaces:
                        namespaces[namespace] = {
                            "key_count": 0,
                            "estimated_size": 0
                        }
                    
                    namespaces[namespace]["key_count"] += 1
                    
                    # Estimate size (this is approximate)
                    try:
                        size = self.redis_client.client.memory_usage(key)
                        if size:
                            namespaces[namespace]["estimated_size"] += size
                    except:
                        pass  # memory_usage not available in all Redis versions
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze cache key {key}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to analyze namespaces: {e}")
        
        return namespaces


def cached(
    namespace: str, 
    ttl: Optional[int] = None, 
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        namespace: Cache namespace
        ttl: Time to live in seconds
        key_func: Custom key generation function
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Generate cache key
                if key_func:
                    cache_identifier = key_func(*args, **kwargs)
                else:
                    # Use function name and arguments as key
                    cache_identifier = {
                        "func": func.__name__,
                        "args": str(args),
                        "kwargs": str(sorted(kwargs.items()))
                    }
                
                # Try to get from cache
                cached_result = advanced_cache.get(namespace, cache_identifier)
                
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                advanced_cache.set(namespace, cache_identifier, result, ttl=ttl)
                
                return result
                
            except Exception as e:
                logger.error(f"Cache decorator error for {func.__name__}: {e}")
                # Fallback to executing function without caching
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global cache instance
advanced_cache = AdvancedRedisCache()


# Convenience functions
def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return advanced_cache.get_cache_info()


def invalidate_cache_namespace(namespace: str) -> int:
    """Invalidate all cache entries in a namespace."""
    return advanced_cache.invalidate_namespace(namespace)


def warm_cache(functions: List[Callable]) -> Dict[str, Any]:
    """Warm the cache with the provided functions."""
    return advanced_cache.warm_cache(functions)
