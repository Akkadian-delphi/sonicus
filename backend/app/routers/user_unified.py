"""
Unified User Management Router

Consolidates and improves upon user.py, user_b2c.py, and users_simple.py
Supports both B2B2C (organization-based) and B2C (direct customer) modes
Includes comprehensive user management, authentication, and analytics
"""

from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List, Dict, Any
import secrets
import logging

# Core dependencies
from app.db.session import get_db
from app.core.auth_dependencies import get_current_user
from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.cache import redis_client

# Models
from app.models.user import User, UserRole, PaymentMethod, SubscriptionStatus
from app.models.user_b2c import UserSubscription, UserPreferences, UserSoundPackage, UserAnalytics
from app.models.organization import Organization
from app.models.sound_package import SoundPackage

# Schemas
from app.schemas.user_unified import (
    CustomerRegistrationSchema,
    OrganizationRegistrationSchema,
    UserRegistrationCompletionSchema,
    UserReadSchema,
    UserProfileSchema,
    UserB2CProfileSchema,
    UserPreferencesSchema,
    UserPreferencesResponseSchema,
    UserAnalyticsSchema,
    UserSoundPackageSchema,
    SubscriptionUpdateSchema,
    SubscriptionResponseSchema,
    UserLoginSchema,
    TokenSchema,
    PasswordResetRequestSchema,
    PasswordResetSchema,
    TrialStartResponseSchema,
    SuccessResponseSchema,
    DailyAnalyticsSchema,
    create_user_response
)

# Services
from app.services.user_registration_service import user_registration_service
from app.services.email import send_password_reset_email
from app.services.payment_methods_service import PaymentMethodsService

# Utils
from passlib.context import CryptContext

# Set up logger and password hashing
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/api/users", tags=["users"])

# === Helper Functions ===

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
    hashed_password = getattr(user, 'hashed_password')
    if not hashed_password or not verify_password(password, hashed_password):
        return None
    return user

async def get_platform_mode(db: Session) -> str:
    """Detect if platform is in B2B2C or B2C mode."""
    org_count = db.query(func.count(Organization.id)).scalar() or 0
    return "B2B2C" if org_count > 0 else "B2C"

# === Authentication Endpoints ===

@router.post("/login", response_model=TokenSchema)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login user and get access token.
    Supports both B2B2C and B2C authentication.
    """
    logger.info(f"Login attempt for email: {form_data.username}")
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    try:
        db.execute(
            User.__table__.update()
            .where(User.id == getattr(user, 'id'))
            .values(last_login=datetime.utcnow())
        )
        db.commit()
    except Exception as e:
        logger.warning(f"Could not update last login for {form_data.username}: {e}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": getattr(user, 'email')}, 
        expires_delta=access_token_expires
    )
    
    logger.info(f"Successful login for user: {getattr(user, 'email')}")
    
    return TokenSchema(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserReadSchema(**create_user_response(user))
    )

@router.post("/register/customer", status_code=status.HTTP_201_CREATED, response_model=UserReadSchema)
async def register_customer(
    customer_data: CustomerRegistrationSchema,
    db: Session = Depends(get_db)
):
    """
    Register a new B2C customer (when no organizations exist).
    Creates an individual customer account without organization association.
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == customer_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = get_password_hash(customer_data.password)
        
        # Create customer user
        new_customer = User(
            email=customer_data.email,
            hashed_password=hashed_password,
            company_name=customer_data.name,  # Use name as company_name for compatibility
            role=UserRole.USER,
            organization_id=None,
            is_active=True
        )
        
        # Start trial
        new_customer.start_trial()
        
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        
        logger.info(f"B2C customer registered: {customer_data.email}")
        
        return UserReadSchema(**create_user_response(new_customer))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Customer registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/register/organization", status_code=status.HTTP_201_CREATED, response_model=UserReadSchema)
async def register_organization_user(
    user_data: OrganizationRegistrationSchema,
    db: Session = Depends(get_db)
):
    """
    Register a new organization and business admin user for B2B2C.
    Creates organization and assigns user as Business Admin.
    """
    try:
        user_data_dict = {
            'email': user_data.email,
            'password': user_data.password,
            'company_name': user_data.company_name,
            'business_type': user_data.business_type,
            'country': user_data.country,
            'telephone': user_data.telephone,
            'preferred_payment_method': user_data.preferred_payment_method
        }
        
        user, organization, authentik_user = await user_registration_service.register_organization_user(
            user_data=user_data_dict,
            db=db,
            create_in_authentik=True
        )
        
        auth_status = "✓ Authentik" if authentik_user else "✗ Local only"
        logger.info(f"B2B2C registration completed for {getattr(user, 'email')} - {auth_status}")
        
        return UserReadSchema(**create_user_response(user))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Organization registration failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Registration failed, please try again"
        )

@router.post("/password-reset/request", response_model=SuccessResponseSchema)
async def request_password_reset(
    request: PasswordResetRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset for a user."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal whether the email exists
        return SuccessResponseSchema(
            message="If the email exists, a password reset link has been sent."
        )
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store token in cache (expire in 1 hour)
    try:
        user_email = getattr(user, 'email')
        redis_client.set(f"password_reset:{reset_token}", user_email, expire=3600)
        
        # Send reset email
        send_password_reset_email(background_tasks, request.email, reset_token)
        
        logger.info(f"Password reset requested for: {request.email}")
        
    except Exception as e:
        logger.error(f"Failed to process password reset for {request.email}: {e}")
    
    return SuccessResponseSchema(
        message="If the email exists, a password reset link has been sent."
    )

# === User Profile Endpoints ===

@router.get("/me", response_model=UserProfileSchema)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's complete profile information."""
    cache_key = f"user_profile:{getattr(current_user, 'id')}"
    cached_user = redis_client.get_json(cache_key)
    
    if cached_user and isinstance(cached_user, dict):
        try:
            return UserProfileSchema(**cached_user)
        except Exception as e:
            logger.warning(f"Invalid cached user data: {e}")
            redis_client.delete(cache_key)
    
    user_data = create_user_response(current_user, include_sensitive=True)
    
    # Cache for 5 minutes
    redis_client.set_json(cache_key, user_data, expire=300)
    
    return UserProfileSchema(**user_data)

@router.get("/me/b2c", response_model=UserB2CProfileSchema)
async def get_b2c_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get B2C-specific user profile with enhanced analytics."""
    try:
        # Get subscription details
        subscription = db.query(UserSubscription).filter(
            UserSubscription.user_id == getattr(current_user, 'id')
        ).first()
        
        # Get basic analytics
        total_sessions = db.query(func.count(UserAnalytics.id)).filter(
            UserAnalytics.user_id == getattr(current_user, 'id')
        ).scalar() or 0
        
        total_listening_time = db.query(func.sum(UserAnalytics.total_listening_time_minutes)).filter(
            UserAnalytics.user_id == getattr(current_user, 'id')
        ).scalar() or 0
        
        # Calculate wellness streak
        wellness_streak = 0  # This would require more complex logic
        
        return UserB2CProfileSchema(
            id=getattr(current_user, 'id'),
            email=getattr(current_user, 'email'),
            name=getattr(current_user, 'company_name'),  # Using company_name as name
            subscription_tier=getattr(subscription, 'subscription_tier', 'free') if subscription else 'free',
            subscription_status=getattr(subscription, 'subscription_status', 'trial') if subscription else 'trial',
            is_premium=subscription is not None and getattr(subscription, 'subscription_tier') != 'free',
            trial_end_date=getattr(current_user, 'trial_end_date'),
            total_sessions=total_sessions,
            total_listening_hours=round(float(total_listening_time) / 60, 2) if total_listening_time else 0.0,
            wellness_streak_days=wellness_streak,
            created_at=getattr(current_user, 'created_at'),
            has_subscription_details=subscription is not None,
            has_preferences=db.query(UserPreferences).filter(
                UserPreferences.user_id == getattr(current_user, 'id')
            ).first() is not None
        )
        
    except Exception as e:
        logger.error(f"Error getting B2C profile for user {getattr(current_user, 'id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile"
        )

@router.put("/me/complete", response_model=UserProfileSchema)
async def complete_user_registration(
    completion_data: UserRegistrationCompletionSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete user registration with additional information."""
    try:
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
        
        # Update user information using SQL update to avoid SQLAlchemy attribute issues
        user_id = getattr(current_user, 'id')
        update_values = {}
        
        if completion_data.telephone is not None:
            update_values['telephone'] = completion_data.telephone
        
        if completion_data.preferred_payment_method is not None:
            update_values['preferred_payment_method'] = completion_data.preferred_payment_method
        
        if update_values:
            db.execute(
                User.__table__.update()
                .where(User.id == user_id)
                .values(**update_values)
            )
            db.commit()
            
            # Clear cache
            cache_key = f"user_profile:{user_id}"
            redis_client.delete(cache_key)
            
            # Refresh user object
            db.refresh(current_user)
            
        logger.info(f"Registration completed for user {getattr(current_user, 'email')}")
        
        return UserProfileSchema(**create_user_response(current_user, include_sensitive=True))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing registration for user {getattr(current_user, 'id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user profile"
        )

# === Subscription Management ===

@router.get("/me/subscription", response_model=Optional[SubscriptionResponseSchema])
async def get_user_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription details."""
    subscription = db.query(UserSubscription).filter(
        UserSubscription.user_id == getattr(current_user, 'id')
    ).first()
    
    if not subscription:
        return None
    
    return SubscriptionResponseSchema(
        id=getattr(subscription, 'id'),
        subscription_tier=getattr(subscription, 'subscription_tier'),
        subscription_status=getattr(subscription, 'subscription_status'),
        billing_cycle=getattr(subscription, 'billing_cycle'),
        price_per_cycle=getattr(subscription, 'price_per_cycle'),
        currency=getattr(subscription, 'currency'),
        trial_start_date=getattr(subscription, 'trial_start_date'),
        trial_end_date=getattr(subscription, 'trial_end_date'),
        subscription_start_date=getattr(subscription, 'subscription_start_date'),
        subscription_end_date=getattr(subscription, 'subscription_end_date'),
        auto_renew=getattr(subscription, 'auto_renew'),
        next_payment_date=getattr(subscription, 'next_payment_date'),
        created_at=getattr(subscription, 'created_at')
    )

@router.post("/me/trial/start", response_model=TrialStartResponseSchema)
async def start_user_trial(
    tier: str = "starter",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a trial for the current user."""
    try:
        user_id = getattr(current_user, 'id')
        
        # Check if user already has an active trial or subscription
        existing_subscription = db.query(UserSubscription).filter(
            UserSubscription.user_id == user_id
        ).first()
        
        if existing_subscription and getattr(existing_subscription, 'subscription_status') in ['active', 'trial']:
            raise HTTPException(
                status_code=400,
                detail="User already has an active subscription or trial"
            )
        
        # Start trial on the user model
        current_user.start_trial()
        
        # Create or update subscription record
        if existing_subscription:
            db.execute(
                UserSubscription.__table__.update()
                .where(UserSubscription.id == getattr(existing_subscription, 'id'))
                .values(
                    subscription_tier=tier,
                    subscription_status="trial",
                    trial_start_date=getattr(current_user, 'trial_start_date'),
                    trial_end_date=getattr(current_user, 'trial_end_date'),
                    updated_at=datetime.utcnow()
                )
            )
        else:
            new_subscription = UserSubscription(
                user_id=user_id,
                subscription_tier=tier,
                subscription_status="trial",
                trial_start_date=getattr(current_user, 'trial_start_date'),
                trial_end_date=getattr(current_user, 'trial_end_date')
            )
            db.add(new_subscription)
        
        db.commit()
        db.refresh(current_user)
        
        trial_end = getattr(current_user, 'trial_end_date')
        days_remaining = (trial_end - datetime.utcnow()).days if trial_end else 0
        
        logger.info(f"Trial started for user {getattr(current_user, 'email')} - tier: {tier}")
        
        return TrialStartResponseSchema(
            message=f"Trial started successfully for {tier} tier",
            trial_end_date=trial_end,
            days_remaining=max(0, days_remaining),
            tier=tier
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting trial for user {getattr(current_user, 'id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error starting trial"
        )

# === Preferences Management ===

@router.get("/me/preferences", response_model=Optional[UserPreferencesResponseSchema])
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's preferences."""
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == getattr(current_user, 'id')
    ).first()
    
    if not preferences:
        return None
    
    return UserPreferencesResponseSchema(
        id=getattr(preferences, 'id'),
        user_id=getattr(preferences, 'user_id'),
        preferred_session_length=getattr(preferences, 'preferred_session_length'),
        preferred_time_of_day=getattr(preferences, 'preferred_time_of_day'),
        notification_preferences=getattr(preferences, 'notification_preferences'),
        theme_preferences=getattr(preferences, 'theme_preferences'),
        audio_preferences=getattr(preferences, 'audio_preferences'),
        privacy_settings=getattr(preferences, 'privacy_settings'),
        created_at=getattr(preferences, 'created_at'),
        updated_at=getattr(preferences, 'updated_at')
    )

@router.put("/me/preferences", response_model=UserPreferencesResponseSchema)
async def update_user_preferences(
    preferences_data: UserPreferencesSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's preferences."""
    user_id = getattr(current_user, 'id')
    
    try:
        existing_preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if existing_preferences:
            # Update existing preferences
            update_values = {
                'preferred_session_length': preferences_data.preferred_session_length,
                'preferred_time_of_day': preferences_data.preferred_time_of_day,
                'notification_preferences': preferences_data.notification_preferences or {},
                'theme_preferences': preferences_data.theme_preferences or {},
                'audio_preferences': preferences_data.audio_preferences or {},
                'privacy_settings': preferences_data.privacy_settings or {},
                'updated_at': datetime.utcnow()
            }
            
            db.execute(
                UserPreferences.__table__.update()
                .where(UserPreferences.user_id == user_id)
                .values(**update_values)
            )
        else:
            # Create new preferences
            new_preferences = UserPreferences(
                user_id=user_id,
                preferred_session_length=preferences_data.preferred_session_length,
                preferred_time_of_day=preferences_data.preferred_time_of_day,
                notification_preferences=preferences_data.notification_preferences or {},
                theme_preferences=preferences_data.theme_preferences or {},
                audio_preferences=preferences_data.audio_preferences or {},
                privacy_settings=preferences_data.privacy_settings or {}
            )
            db.add(new_preferences)
        
        db.commit()
        
        # Get updated preferences
        updated_preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        return UserPreferencesResponseSchema(
            id=getattr(updated_preferences, 'id'),
            user_id=user_id,
            preferred_session_length=getattr(updated_preferences, 'preferred_session_length'),
            preferred_time_of_day=getattr(updated_preferences, 'preferred_time_of_day'),
            notification_preferences=getattr(updated_preferences, 'notification_preferences'),
            theme_preferences=getattr(updated_preferences, 'theme_preferences'),
            audio_preferences=getattr(updated_preferences, 'audio_preferences'),
            privacy_settings=getattr(updated_preferences, 'privacy_settings'),
            created_at=getattr(updated_preferences, 'created_at'),
            updated_at=getattr(updated_preferences, 'updated_at')
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating preferences for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating preferences"
        )

# === Analytics Endpoints ===

@router.get("/me/analytics", response_model=UserAnalyticsSchema)
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's analytics for the specified period."""
    user_id = getattr(current_user, 'id')
    
    try:
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        # Get analytics data
        analytics_data = db.query(UserAnalytics).filter(
            and_(
                UserAnalytics.user_id == user_id,
                UserAnalytics.date >= start_date
            )
        ).all()
        
        if not analytics_data:
            return UserAnalyticsSchema(
                period_days=days,
                total_sessions=0,
                total_listening_hours=0.0,
                average_session_length=0.0,
                completion_rate=0.0,
                wellness_streak_days=0,
                average_wellness_improvement=None,
                daily_analytics=[]
            )
        
        # Calculate aggregated metrics
        total_sessions = sum(getattr(a, 'sessions_count', 0) for a in analytics_data)
        total_listening_minutes = sum(getattr(a, 'total_listening_time_minutes', 0) for a in analytics_data)
        total_listening_hours = round(total_listening_minutes / 60.0, 2)
        
        avg_session_length = round(total_listening_minutes / max(total_sessions, 1), 1)
        
        # Calculate completion rate
        completion_rates = [getattr(a, 'completion_rate', 0) for a in analytics_data if getattr(a, 'completion_rate', 0) > 0]
        avg_completion_rate = round(sum(completion_rates) / max(len(completion_rates), 1), 1)
        
        # Calculate wellness improvement
        improvements = []
        for a in analytics_data:
            stress_before = getattr(a, 'stress_level_before', None)
            stress_after = getattr(a, 'stress_level_after', None)
            if stress_before and stress_after:
                improvements.append(stress_before - stress_after)
        
        avg_wellness_improvement = round(sum(improvements) / max(len(improvements), 1), 2) if improvements else None
        
        # Calculate wellness streak (consecutive days with sessions)
        wellness_streak = 0
        sorted_dates = sorted([getattr(a, 'date') for a in analytics_data], reverse=True)
        current_date = datetime.utcnow().date()
        
        for date in sorted_dates:
            if (current_date - date).days <= wellness_streak + 1:
                wellness_streak += 1
                current_date = date
            else:
                break
        
        # Prepare daily analytics
        daily_analytics = []
        for a in analytics_data:
            mood_improvement = None
            stress_before = getattr(a, 'stress_level_before', None)
            stress_after = getattr(a, 'stress_level_after', None)
            if stress_before and stress_after:
                mood_improvement = stress_before - stress_after
            
            daily_analytics.append(DailyAnalyticsSchema(
                date=getattr(a, 'date').isoformat(),
                sessions_count=getattr(a, 'sessions_count', 0),
                listening_time_minutes=getattr(a, 'total_listening_time_minutes', 0),
                completion_rate=getattr(a, 'completion_rate', 0.0),
                mood_improvement=mood_improvement
            ))
        
        return UserAnalyticsSchema(
            period_days=days,
            total_sessions=total_sessions,
            total_listening_hours=total_listening_hours,
            average_session_length=avg_session_length,
            completion_rate=avg_completion_rate,
            wellness_streak_days=wellness_streak,
            average_wellness_improvement=avg_wellness_improvement,
            daily_analytics=daily_analytics
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving analytics"
        )

# === Sound Package Management ===

@router.get("/me/sound-packages", response_model=List[UserSoundPackageSchema])
async def get_user_sound_packages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sound packages assigned to the current user."""
    user_id = getattr(current_user, 'id')
    
    try:
        # Get user's sound package assignments with package details
        assignments = db.query(UserSoundPackage, SoundPackage).join(
            SoundPackage, UserSoundPackage.sound_package_id == SoundPackage.id
        ).filter(
            and_(
                UserSoundPackage.user_id == user_id,
                UserSoundPackage.is_active == True
            )
        ).all()
        
        packages = []
        for assignment, package in assignments:
            packages.append(UserSoundPackageSchema(
                id=getattr(assignment, 'id'),
                sound_package_id=getattr(assignment, 'sound_package_id'),
                package_name=getattr(package, 'name', 'Unknown Package'),
                description=getattr(package, 'description'),
                access_granted_at=getattr(assignment, 'access_granted_at'),
                access_expires_at=getattr(assignment, 'access_expires_at'),
                usage_count=getattr(assignment, 'usage_count', 0),
                last_used_at=getattr(assignment, 'last_used_at'),
                is_active=getattr(assignment, 'is_active', True)
            ))
        
        return packages
        
    except Exception as e:
        logger.error(f"Error getting sound packages for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sound packages"
        )

# === Payment Methods ===

@router.get("/payment-methods/available")
async def get_available_payment_methods(
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
async def get_recommended_payment_methods(
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

# === Health Check ===

@router.get("/health")
async def users_health():
    """Health check for unified users service."""
    return {
        "status": "Unified Users service is running",
        "service": "users-unified",
        "features": [
            "B2B2C organization registration",
            "B2C customer registration",
            "Authentication with JWT tokens",
            "User preferences management",
            "Analytics and reporting",
            "Sound package assignments",
            "Subscription management",
            "Password reset functionality"
        ]
    }

@router.get("/info")
async def users_info():
    """Get information about the unified users service."""
    return {
        "service": "users-unified",
        "description": "Comprehensive user management combining B2B2C and B2C features",
        "version": "1.0.0",
        "endpoints": [
            "POST /login - User authentication",
            "POST /register/customer - B2C customer registration",
            "POST /register/organization - B2B2C organization registration",
            "GET /me - Current user profile",
            "GET /me/b2c - B2C-specific profile",
            "PUT /me/complete - Complete registration",
            "GET /me/subscription - User subscription details",
            "POST /me/trial/start - Start trial",
            "GET /me/preferences - User preferences",
            "PUT /me/preferences - Update preferences",
            "GET /me/analytics - User analytics",
            "GET /me/sound-packages - Assigned sound packages",
            "GET /payment-methods/available - Available payment methods",
            "POST /password-reset/request - Request password reset"
        ],
        "status": "Active"
    }
