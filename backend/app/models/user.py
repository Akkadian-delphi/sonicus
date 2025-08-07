from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum
from app.db.base import Base

# Forward declaration to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.user_b2c import UserSubscription

class SubscriptionStatus(enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class UserRole(enum.Enum):
    SUPER_ADMIN = "super_admin"        # Platform owner
    BUSINESS_ADMIN = "business_admin"  # Organization admin
    STAFF = "staff"                    # Organization staff member
    USER = "user"                      # End user

class PaymentMethod(enum.Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Required for JWT auth
    authentik_user_id = Column(Integer, nullable=True)  # Authentik user PK
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # B2B2C Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)  # User role within organization
    
    # User profile information
    telephone = Column(String, nullable=True)  # Optional phone number
    preferred_payment_method = Column(Enum(PaymentMethod), nullable=True)  # User's preferred payment method
    
    # B2B2C Company information
    company_name = Column(String, nullable=True)  # Company/Organization name
    business_type = Column(String, nullable=True)  # Type of business (Healthcare, Wellness, etc.)
    country = Column(String, nullable=True)  # Country code (e.g., "FR", "DE", "ES")
    
    # Trial and subscription management
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    trial_start_date = Column(DateTime, nullable=True)
    trial_end_date = Column(DateTime, nullable=True)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    last_login = Column(DateTime, nullable=True)
    
    # Database management
    database_created = Column(Boolean, default=False)  # Track if user's database was created
    database_created_at = Column(DateTime, nullable=True)  # When database was created
    
    # Add relationships - properly defined (ALL temporarily disabled to fix login)
    # organization = relationship("Organization", back_populates="users")
    # subscription = relationship("UserSubscription", back_populates="user", uselist=False)  # One-to-one relationship
    # sound_packages = relationship("UserSoundPackage", back_populates="user")  # User's sound package assignments
    # preferences = relationship("UserPreferences", back_populates="user", uselist=False)  # User preferences
    # analytics = relationship("UserAnalytics", back_populates="user")  # User analytics data
    # sessions = relationship("UserSession", back_populates="user")  # User session data
    # content_plays = relationship("ContentPlay", back_populates="user")  # User content play records
    # invoices = relationship("Invoice", back_populates="user")
    
    @property
    def is_trial_active(self) -> bool:
        """Check if user's trial is still active."""
        if self.trial_start_date is None or self.trial_end_date is None:
            return False
        return bool(datetime.utcnow() <= self.trial_end_date)
    
    @property
    def days_left_in_trial(self) -> int:
        """Calculate days left in trial."""
        if self.trial_end_date is None:
            return 0
        delta = self.trial_end_date - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def has_active_subscription(self) -> bool:
        """Check if user has active paid subscription."""
        return bool(self.subscription_status == SubscriptionStatus.ACTIVE)
    
    @property
    def can_access_content(self) -> bool:
        """Check if user can access premium content."""
        return self.is_trial_active or self.has_active_subscription
    
    def start_trial(self):
        """Start 14-day trial for new user."""
        self.trial_start_date = datetime.utcnow()
        self.trial_end_date = self.trial_start_date + timedelta(days=14)
        self.subscription_status = SubscriptionStatus.TRIAL
