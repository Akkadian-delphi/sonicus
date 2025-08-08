from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, text
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.b2b2c_session import get_contextual_db_session
from app.core.auth_dependencies import get_super_admin_user
from app.models.user import User, SubscriptionStatus
from app.models.therapy_sound import TherapySound
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.therapy_sound import TherapySoundResponse, TherapySoundCreate, TherapySoundUpdate

router = APIRouter(
    prefix="/admin", 
    tags=["Admin"]
)

# Dashboard Statistics
@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Get dashboard statistics for admin panel."""
    
    # Total users
    total_users = db.query(User).count()
    
    # Active trial users
    trial_users = db.query(User).filter(
        User.subscription_status == SubscriptionStatus.TRIAL,  # type: ignore
        User.trial_end_date > datetime.utcnow()  # type: ignore
    ).count()
    
    # Paid subscribers
    paid_subscribers = db.query(User).filter(
        User.subscription_status == SubscriptionStatus.ACTIVE  # type: ignore
    ).count()
    
    # Expired users
    expired_users = db.query(User).filter(
        User.subscription_status == SubscriptionStatus.EXPIRED  # type: ignore
    ).count()
    
    # Total sounds
    total_sounds = db.query(TherapySound).count()
    
    # New users this month
    month_ago = datetime.utcnow() - timedelta(days=30)
    new_users_this_month = db.query(User).filter(
        User.created_at >= month_ago
    ).count()
    
    # Revenue this month (if you have invoice data)
    revenue_this_month = db.query(func.sum(Invoice.amount)).filter(
        Invoice.created_at >= month_ago,
        Invoice.status == "paid"
    ).scalar() or 0
    
    return {
        "total_users": total_users,
        "trial_users": trial_users,
        "paid_subscribers": paid_subscribers,
        "expired_users": expired_users,
        "total_sounds": total_sounds,
        "new_users_this_month": new_users_this_month,
        "revenue_this_month": float(revenue_this_month),
        "conversion_rate": round((paid_subscribers / total_users * 100), 2) if total_users > 0 else 0
    }

# User Management
@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[SubscriptionStatus] = None,
    search: Optional[str] = None,
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Get all users with pagination and filtering."""
    
    query = db.query(User)
    
    # Filter by subscription status
    if status:
        query = query.filter(User.subscription_status == status)  # type: ignore
    
    # Search by email
    if search:
        query = query.filter(User.email.contains(search.lower()))
    
    # Order by creation date (newest first)
    query = query.order_by(desc(User.created_at))
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}")
async def get_user_details(
    user_id: int,
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Get detailed user information."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's subscriptions
    subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).all()
    
    # Get user's invoices
    invoices = db.query(Invoice).filter(Invoice.user_id == user_id).all()
    
    return {
        "user": user,
        "subscriptions": subscriptions,
        "invoices": invoices,
        "is_trial_active": user.is_trial_active,
        "days_left_in_trial": user.days_left_in_trial,
        "can_access_content": user.can_access_content
    }

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Update user information."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return {"message": "User updated successfully", "user": user}

@router.post("/users/{user_id}/extend-trial")
async def extend_user_trial(
    user_id: int,
    days: int = Query(..., ge=1, le=365),
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Extend user's trial period."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Extend trial
    if user.trial_end_date is not None:
        current_end_date = user.trial_end_date
        user.trial_end_date = current_end_date + timedelta(days=days)  # type: ignore
    else:
        # Start new trial if none exists
        user.trial_start_date = datetime.utcnow()
        user.trial_end_date = user.trial_start_date + timedelta(days=days)
    
    user.subscription_status = SubscriptionStatus.TRIAL
    
    db.commit()
    return {"message": f"Trial extended by {days} days", "new_trial_end": user.trial_end_date}

@router.post("/users/{user_id}/activate-subscription")
async def activate_user_subscription(
    user_id: int,
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Manually activate user's subscription."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.subscription_status = SubscriptionStatus.ACTIVE
    db.commit()
    
    return {"message": "User subscription activated", "user": user}

# Sound Management
@router.get("/sounds", response_model=List[TherapySoundResponse])
async def get_all_sounds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Get all therapy sounds."""
    
    sounds = db.query(TherapySound).offset(skip).limit(limit).all()
    return sounds

@router.post("/sounds", response_model=TherapySoundResponse)
async def create_sound(
    sound_data: TherapySoundCreate,
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Create new therapy sound."""
    
    sound = TherapySound(**sound_data.dict())
    db.add(sound)
    db.commit()
    db.refresh(sound)
    
    return sound

@router.put("/sounds/{sound_id}")
async def update_sound(
    sound_id: int,
    sound_update: TherapySoundUpdate,
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Update therapy sound."""
    
    sound = db.query(TherapySound).filter(TherapySound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")
    
    for field, value in sound_update.dict(exclude_unset=True).items():
        setattr(sound, field, value)
    
    db.commit()
    db.refresh(sound)
    
    return {"message": "Sound updated successfully", "sound": sound}

@router.delete("/sounds/{sound_id}")
async def delete_sound(
    sound_id: int,
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Delete therapy sound."""
    
    sound = db.query(TherapySound).filter(TherapySound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")
    
    db.delete(sound)
    db.commit()
    
    return {"message": "Sound deleted successfully"}

# Subscription Management
@router.get("/subscriptions")
async def get_all_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Get all subscriptions."""
    
    subscriptions = db.query(Subscription).join(User).offset(skip).limit(limit).all()
    return subscriptions

# System Health
@router.get("/system/health")
async def system_health(
    current_admin: User = Depends(get_super_admin_user),
    db: Session = Depends(get_contextual_db_session)
):
    """Get system health status."""
    
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check for users with expired trials that need attention
    expired_trials = db.query(User).filter(
        User.subscription_status == SubscriptionStatus.TRIAL,  # type: ignore
        User.trial_end_date < datetime.utcnow()  # type: ignore
    ).count()
    
    return {
        "database": db_status,
        "expired_trials_needing_attention": expired_trials,
        "timestamp": datetime.utcnow()
    }
