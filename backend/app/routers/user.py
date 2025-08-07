from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import secrets
from jose import jwt
from passlib.context import CryptContext
from typing import Optional

from app.models.user import User, PaymentMethod, UserRole
from app.models.organization import Organization, SubscriptionTier, OrganizationStatus
from app.schemas.user import UserCreateSchema, UserReadSchema, TokenSchema
from app.core.security import get_current_user, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from app.db.session import get_db  # Use regular DB session for registration
from app.services.email import send_password_reset_email
from app.services.payment_methods_service import PaymentMethodsService
from app.services.user_registration_service import user_registration_service
from app.core.cache import redis_client
from pydantic import BaseModel
import logging
import uuid

# Set up logger
logger = logging.getLogger(__name__)

# Configure password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    # Access the actual value from the SQLAlchemy column
    hashed_password = getattr(user, 'hashed_password')
    if not verify_password(password, hashed_password):
        return None
    return user

router = APIRouter()

@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserReadSchema)
async def register_user(
    user_data: UserCreateSchema, 
    db: Session = Depends(get_db)  # Use regular DB session for user registration
):
    """
    Register a new user and organization in the system for B2B2C.
    
    Creates a new organization and assigns the registering user as Business Admin.
    Optionally creates user in Authentik for OIDC authentication support.
    
    Parameters:
    - **user_data**: Required user information including email, password, and company details
    
    Returns:
    - User information (excluding password)
    
    Raises:
    - 400: Email already registered or missing required company information
    """
    try:
        # Convert Pydantic model to dict for the service
        user_data_dict = {
            'email': user_data.email,
            'password': user_data.password,
            'company_name': user_data.company_name,
            'business_type': user_data.business_type,
            'country': user_data.country,
            'telephone': user_data.telephone,
            'preferred_payment_method': user_data.preferred_payment_method
        }
        
        # Use the enhanced registration service
        user, organization, authentik_user = await user_registration_service.register_organization_user(
            user_data=user_data_dict,
            db=db,
            create_in_authentik=True  # Enable Authentik user creation
        )
        
        # Log registration success with details
        auth_status = "✓ Authentik" if authentik_user else "✗ Local only"
        logger.info(f"Registration completed for {user.email} - {auth_status}")
        
        # Return user data as dictionary to avoid SQLAlchemy serialization issues
        return {
            "id": user.id,
            "email": user.email,
            "is_active": getattr(user, 'is_active', True),
            "role": getattr(user, 'role', UserRole.BUSINESS_ADMIN),
            "organization_id": str(getattr(user, 'organization_id', '')) if getattr(user, 'organization_id', None) else None
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
        
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Registration failed, please try again"
        )

@router.post("/token", response_model=None)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)  # Use regular DB session for login
):
    """
    Login user and get access token.
    
    Parameters:
    - **username**: User email
    - **password**: User password
    
    Returns:
    - Access token and token type
    
    Raises:
    - 401: Invalid credentials
    """
    logger.info(f"Login attempt for email: {form_data.username}")
    
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    logger.info(f"Successful login for user: {user.email}")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/request-password-reset")
def request_password_reset(
    email: str, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)  # Use regular DB session
):
    """
    Request password reset for a user.
    
    Sends a password reset email with a token to the specified email address.
    
    Parameters:
    - **email**: Email address to send reset link to
    
    Returns:
    - Success message
    """
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal whether the email exists for security reasons
        return {"message": "If the email exists, a password reset link has been sent."}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store token in cache (expire in 1 hour)
    try:
        # Use the custom set method with expire parameter
        user_email = getattr(user, 'email')
        redis_client.set(f"password_reset:{reset_token}", user_email, expire=3600)
    except Exception as e:
        logger.error(f"Failed to store reset token in cache: {e}")
    
    # Send reset email
    send_password_reset_email(background_tasks, email, reset_token)
    
    return {"message": "If the email exists, a password reset link has been sent."}

@router.get("/users/me", response_model=UserReadSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user profile information.
    
    Retrieves the profile information for the currently authenticated user.
    Requires authentication via Bearer token.
    
    Returns:
    - User profile information
    
    Raises:
    - 401: User not authenticated
    """
    # Check cache first
    cache_key = f"user_profile:{current_user.id}"
    cached_user = redis_client.get_json(cache_key)
    
    if cached_user:
        return cached_user
    
    # Return user data as dictionary to avoid SQLAlchemy serialization issues
    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": getattr(current_user, 'is_active', True),
        "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        "organization_id": str(getattr(current_user, 'organization_id')) if getattr(current_user, 'organization_id') is not None else None
    }
    
    # Cache the user data for 5 minutes
    redis_client.set_json(cache_key, user_data, expire=300)
    
    return user_data

# Registration completion schema
class RegistrationCompletionSchema(BaseModel):
    telephone: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None

@router.put("/complete-registration", response_model=UserReadSchema)
def complete_registration(
    completion_data: RegistrationCompletionSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)  # Use regular DB for now, can enhance later
):
    """
    Complete user registration by adding telephone and payment method preferences.
    
    This endpoint allows users to provide additional information after initial registration:
    - Telephone number (optional)
    - Preferred payment method (optional)
    
    Returns the updated user profile.
    """
    # Validate payment method if provided
    if completion_data.preferred_payment_method:
        validation = PaymentMethodsService.validate_payment_method(
            completion_data.preferred_payment_method
        )
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payment method: {validation['reason']}"
            )
    
    # Update user with new information
    if completion_data.telephone is not None:
        setattr(current_user, 'telephone', completion_data.telephone)
    
    if completion_data.preferred_payment_method is not None:
        setattr(current_user, 'preferred_payment_method', completion_data.preferred_payment_method)
    
    try:
        db.commit()
        db.refresh(current_user)
        
        # Clear user cache to reflect changes
        cache_key = f"user_profile:{current_user.id}"
        redis_client.delete(cache_key)
        
        logger.info(f"Registration completed for user {current_user.email}")
        
        # Return user data as dictionary to avoid SQLAlchemy serialization issues
        return {
            "id": current_user.id,
            "email": current_user.email,
            "is_active": getattr(current_user, 'is_active', True),
            "telephone": getattr(current_user, 'telephone', None),
            "preferred_payment_method": getattr(current_user, 'preferred_payment_method', None)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing registration for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user profile"
        )

@router.get("/payment-methods/available")
def get_user_available_payment_methods(
    currency: str = "USD",
    platform: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get available payment methods for the current user."""
    return PaymentMethodsService.get_available_payment_methods(
        currency=currency,
        platform=platform
    )

@router.get("/payment-methods/recommended")
def get_user_recommended_payment_methods(
    currency: str = "USD", 
    amount: Optional[float] = None,
    platform: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get recommended payment methods for the current user."""
    return PaymentMethodsService.get_recommended_payment_methods(
        currency=currency,
        amount=amount,
        platform=platform
    )