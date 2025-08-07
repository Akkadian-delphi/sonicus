"""
Subscription management service for handling trials and paid subscriptions.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional

from app.models.user import User, SubscriptionStatus
from app.models.subscription import Subscription
from app.core.cache import redis_client
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service class for managing user subscriptions and trials."""
    
    @staticmethod
    def check_and_update_expired_trials(db: Session) -> int:
        """
        Check for expired trials and update user status.
        Returns the number of users updated.
        """
        try:
            # Find users with expired trials
            expired_trial_users = db.query(User).filter(
                User.subscription_status == SubscriptionStatus.TRIAL,  # type: ignore
                User.trial_end_date < datetime.utcnow()  # type: ignore
            ).all()
            
            updated_count = 0
            for user in expired_trial_users:
                user.subscription_status = SubscriptionStatus.EXPIRED
                updated_count += 1
                logger.info(f"Updated expired trial for user {user.email}")
            
            if updated_count > 0:
                db.commit()
                logger.info(f"Updated {updated_count} expired trial users")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating expired trials: {e}")
            db.rollback()
            return 0
    
    @staticmethod
    def get_trial_status(user: User) -> dict:
        """Get detailed trial status for a user."""
        if user.trial_start_date is None or user.trial_end_date is None:
            return {
                "has_trial": False,
                "is_active": False,
                "days_remaining": 0,
                "expired": False
            }
        
        now = datetime.utcnow()
        days_remaining = max(0, (user.trial_end_date - now).days)
        is_active = user.trial_end_date > now
        expired = user.trial_end_date <= now and user.subscription_status == SubscriptionStatus.TRIAL
        
        return {
            "has_trial": True,
            "is_active": is_active,
            "days_remaining": days_remaining,
            "trial_start": user.trial_start_date,
            "trial_end": user.trial_end_date,
            "expired": expired
        }
    
    @staticmethod
    def can_user_access_premium_content(user: User) -> bool:
        """Check if user can access premium content."""
        # Superusers always have access
        if user.is_superuser is True:  # Use explicit comparison
            return True
        
        # Check if user has active paid subscription
        if user.subscription_status == SubscriptionStatus.ACTIVE:  # type: ignore
            return True
        
        # Check if user has active trial
        if user.subscription_status == SubscriptionStatus.TRIAL and user.is_trial_active:  # type: ignore
            return True
        
        return False
    
    @staticmethod
    def get_user_subscription_info(user: User, db: Session) -> dict:
        """Get comprehensive subscription information for a user."""
        trial_status = SubscriptionService.get_trial_status(user)
        can_access_premium = SubscriptionService.can_user_access_premium_content(user)
        
        # Get active subscriptions
        active_subscriptions = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).all()
        
        return {
            "user_id": user.id,
            "email": user.email,
            "subscription_status": user.subscription_status.value,
            "trial_info": trial_status,
            "can_access_premium": can_access_premium,
            "active_subscriptions": len(active_subscriptions),
            "is_superuser": user.is_superuser
        }
    
    @staticmethod
    def create_trial_for_user(user: User, days: int = 7) -> bool:
        """Create a trial for a user."""
        try:
            user.trial_start_date = datetime.utcnow()
            user.trial_end_date = user.trial_start_date + timedelta(days=days)
            user.subscription_status = SubscriptionStatus.TRIAL
            return True
        except Exception as e:
            logger.error(f"Error creating trial for user {user.email}: {e}")
            return False
    
    @staticmethod
    def upgrade_user_to_paid(user: User, db: Session) -> bool:
        """Upgrade user from trial to paid subscription."""
        try:
            user.subscription_status = SubscriptionStatus.ACTIVE
            
            # Clear trial-related cache
            cache_key = f"user:{user.id}"
            redis_client.delete(cache_key)
            
            db.commit()
            logger.info(f"Upgraded user {user.email} to paid subscription")
            return True
            
        except Exception as e:
            logger.error(f"Error upgrading user {user.email}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_expiring_trials(db: Session, days_ahead: int = 3) -> List[User]:
        """Get users whose trials will expire in the specified number of days."""
        expiry_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        expiring_users = db.query(User).filter(
            User.subscription_status == SubscriptionStatus.TRIAL,  # type: ignore
            and_(
                User.trial_end_date <= expiry_date,  # type: ignore
                User.trial_end_date > datetime.utcnow()  # type: ignore
            )
        ).all()
        
        return expiring_users
    
    @staticmethod
    def send_trial_expiry_notifications(db: Session) -> int:
        """
        Send notifications to users whose trials are expiring soon.
        This is a placeholder - implement with your email service.
        """
        expiring_users = SubscriptionService.get_expiring_trials(db, days_ahead=2)
        
        notification_count = 0
        for user in expiring_users:
            # Here you would integrate with your email service
            # For now, just log
            trial_info = SubscriptionService.get_trial_status(user)
            logger.info(f"Trial expiry notification needed for {user.email} - {trial_info['days_remaining']} days left")
            notification_count += 1
        
        return notification_count
