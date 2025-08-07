"""
Redis cache client for the Sonicus application.
"""
import json
import logging
from typing import Any, Dict, Optional, Union
import redis
from redis.exceptions import AuthenticationError, ConnectionError, RedisError
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client for caching operations"""
    
    _instance = None
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.__init__()
            
            # Initialize connection variables
            host = None
            port = None
            
            try:
                # Ensure we have the correct Redis connection URL with authentication
                # Extract components from settings to build a proper connection
                host = settings.REDIS_HOST
                port = settings.REDIS_PORT
                db = settings.REDIS_DB
                password = settings.REDIS_PASSWORD
                
                # Log connection attempt (without password)
                logger.info(f"Connecting to Redis at {host}:{port}/{db}")
                
                # Use from_url with proper credentials
                if password:
                    # Ensure password is properly included in the URL
                    redis_url = f"redis://:{password}@{host}:{port}/{db}"
                    logger.debug("Using Redis with authentication")
                else:
                    redis_url = f"redis://{host}:{port}/{db}"
                    logger.warning("Connecting to Redis without authentication - this may fail if authentication is required")
                
                cls._instance.client = redis.Redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                
                # Test connection
                cls._instance.client.ping()
                logger.info("Connected to Redis server successfully")
            except AuthenticationError as e:
                logger.error(f"Redis authentication failed: {str(e)}")
                logger.error("Check that REDIS_PASSWORD is correctly set in your environment")
                cls._instance.client = None
            except ConnectionError as e:
                logger.error(f"Redis connection error: {str(e)}")
                if host and port:
                    logger.error(f"Check that Redis is running at {host}:{port}")
                cls._instance.client = None
            except RedisError as e:
                logger.error(f"Redis connection failed: {str(e)}")
                cls._instance.client = None
            except Exception as e:
                logger.error(f"Unexpected error connecting to Redis: {str(e)}")
                cls._instance.client = None
        return cls._instance

    def get(self, key: str) -> Optional[str]:
        """Get a value from Redis cache"""
        try:
            if not self.client:
                return None
            result = self.client.get(key)
            return str(result) if result is not None else None
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None

    def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set a value in Redis cache with optional expiration in seconds"""
        try:
            if not self.client:
                return False
            result = self.client.set(key, value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
            return False
    
    def get_json(self, key: str) -> Optional[Union[Dict[str, Any], list]]:
        """Get a JSON value from Redis cache"""
        try:
            if not self.client:
                return None
            data = self.client.get(key)
            if data:
                return json.loads(str(data))
            return None
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from Redis for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Redis get_json error: {str(e)}")
            return None
    
    def set_json(self, key: str, value: Union[Dict[str, Any], list], expire: Optional[int] = None) -> bool:
        """Set a JSON value in Redis cache with optional expiration in seconds"""
        try:
            if not self.client:
                return False
            json_data = json.dumps(value, default=str)
            result = self.client.set(key, json_data, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis set_json error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from Redis cache"""
        try:
            if not self.client:
                return False
            result = self.client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}")
            return False

# Create a singleton Redis client instance for the application
redis_client = RedisClient()