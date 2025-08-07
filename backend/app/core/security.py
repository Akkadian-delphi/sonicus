import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models.user import User
from app.db.session import get_db, SessionLocal
from app.core.cache import redis_client

# Set up logger
logger = logging.getLogger(__name__)

# Get security settings from environment with better defaults
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
if SECRET_KEY == "dev-secret-key-change-in-production" and os.getenv("ENV") == "production":
    logger.warning("Using default SECRET_KEY in production. This is a security risk!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Update tokenUrl to include prefix - this is necessary for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    
    Args:
        data: The payload to encode in the token
        expires_delta: Optional override for token expiration time
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create access token: {str(e)}")
        raise

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency for extracting and validating the current user from a JWT token.
    
    Args:
        token: The JWT token from the request
        db: Database session
        
    Returns:
        User: The authenticated user object
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and verify the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: Optional[str] = payload.get("sub")
        if user_email is None:
            logger.warning("Missing 'sub' claim in token")
            raise credentials_exception
            
        # Check token version/blacklist in Redis if implemented
        # This would allow for token revocation
            
    except JWTError as e:
        logger.warning(f"JWT error: {str(e)}")
        raise credentials_exception
    
    # Try to get user from cache first
    cache_key = f"auth_user:{user_email}"
    cached_user = redis_client.get_json(cache_key)
    
    if cached_user and isinstance(cached_user, dict):
        # Create a User object from cached data
        user = User(
            id=cached_user.get("id"),
            email=cached_user.get("email"),
            hashed_password="",  # We don't cache the password hash
            is_active=cached_user.get("is_active", True),
            is_superuser=cached_user.get("is_superuser", False)
        )
        return user
        
    # If not in cache, get from database by email
    user = db.query(User).filter(User.email == user_email).first()
    
    if user is None:
        logger.warning(f"User with email {user_email} not found in database")
        raise credentials_exception
        
    if user.is_active is False:
        logger.warning(f"Inactive user {user_email} attempted to access protected endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    
    # Cache the user object for 5 minutes
    redis_client.set_json(cache_key, {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser
    }, expire=300)
    
    return user

def get_admin_user(current_user: User = Depends(get_current_user)):
    """
    Dependency for endpoints that require admin access.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The authenticated admin user
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if current_user.is_superuser is False:
        logger.warning(f"Non-admin user {current_user.id} attempted to access admin endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Administrator privileges required"
        )
    return current_user
