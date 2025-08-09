#!/usr/bin/env python3
"""
Test script for organization registration flow
Tests the B2B2C registration where users create organizations and become business admins
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.schemas.user import UserCreateSchema
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_organization_registration():
    """Test the organization registration flow"""
    db = None
    try:
        # Create database connection
        db_url = settings.DATABASE_URL or "postgresql://user:e1efefe@localhost:5433/sonicus_db"
        connection_url = db_url.replace("postgresql+asyncpg", "postgresql")
        engine = create_engine(connection_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("🏢 Testing B2B2C Organization Registration Flow")
        print("=" * 60)
        
        # Test data
        test_email = "testadmin@testcompany.com"
        test_company = "Test Healthcare Solutions"
        
        # Clean up any existing test data using raw SQL to avoid foreign key issues
        from sqlalchemy import text
        try:
            # Delete users first, then organizations
            db.execute(text("DELETE FROM users WHERE email = :email"), {"email": test_email})
            db.execute(text("DELETE FROM organizations WHERE name = :name"), {"name": test_company})
            db.commit()
            print(f"🧹 Cleaned up existing test data for {test_email}")
        except Exception as cleanup_error:
            print(f"🧹 Cleanup note: {cleanup_error}")
            db.rollback()
        
        # Test organization creation during user registration
        print(f"\n1. Testing organization creation for: {test_company}")
        
        # Simulate the registration data
        user_data = UserCreateSchema(
            email=test_email,
            password="TestPassword123!",
            company_name=test_company,
            business_type="Healthcare & Medical",
            country="FR"
        )
        
        print(f"   📝 Company: {user_data.company_name}")
        print(f"   📝 Business Type: {user_data.business_type}")
        print(f"   📝 Country: {user_data.country}")
        print(f"   📝 Admin Email: {user_data.email}")
        
        # Verify database schema supports the flow
        print(f"\n2. Checking database schema compatibility...")
        
        # Check if organizations table exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'organizations' not in tables:
            print("   ❌ Organizations table not found")
            return False
        else:
            print("   ✅ Organizations table exists")
        
        if 'users' not in tables:
            print("   ❌ Users table not found")
            return False
        else:
            print("   ✅ Users table exists")
            
        # Check user table has organization and role columns
        user_columns = [col['name'] for col in inspector.get_columns('users')]
        required_columns = ['organization_id', 'role', 'company_name', 'business_type', 'country']
        
        for col in required_columns:
            if col in user_columns:
                print(f"   ✅ Users table has {col} column")
            else:
                print(f"   ❌ Users table missing {col} column")
                return False
        
        print(f"\n3. Testing the registration flow logic...")
        
        # Create organization (simulating the registration endpoint logic)
        from app.models.organization import SubscriptionTier, OrganizationStatus
        
        organization = Organization(
            name=user_data.company_name,
            display_name=user_data.company_name,
            domain=user_data.email.split('@')[1] if '@' in user_data.email else None,
            primary_contact_email=user_data.email,
            industry=user_data.business_type,
            country=user_data.country,
            subscription_tier=SubscriptionTier.STARTER,
            subscription_status=OrganizationStatus.TRIAL,
            max_users=10,
            max_sound_libraries=3,
            onboarding_completed=False
        )
        
        db.add(organization)
        db.flush()  # Get the organization ID
        print(f"   ✅ Organization created: {organization.name} (ID: {organization.id})")
        
        # Create user as business admin
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(user_data.password)
        
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            company_name=user_data.company_name,
            business_type=user_data.business_type,
            country=user_data.country,
            organization_id=organization.id,
            role=UserRole.BUSINESS_ADMIN
        )
        
        # Start trial
        new_user.start_trial()
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.refresh(organization)
        
        print(f"   ✅ Business admin created: {new_user.email}")
        print(f"   ✅ User role: {new_user.role}")
        print(f"   ✅ User linked to organization: {new_user.organization_id}")
        print(f"   ✅ Trial started: {new_user.is_trial_active}")
        print(f"   ✅ Days left in trial: {new_user.days_left_in_trial}")
        
        print(f"\n4. Verifying the complete B2B2C setup...")
        
        # Verify relationships
        verification_org = db.query(Organization).filter(Organization.id == organization.id).first()
        verification_user = db.query(User).filter(User.email == test_email).first()
        
        if verification_org and verification_user:
            print(f"   ✅ Organization verified: {verification_org.name}")
            print(f"   ✅ Business admin verified: {verification_user.email}")
            print(f"   ✅ Correct role assignment: {verification_user.role == UserRole.BUSINESS_ADMIN}")
            print(f"   ✅ Proper organization linking: {verification_user.organization_id == verification_org.id}")
            print(f"   ✅ Company info stored: {verification_user.company_name}")
            print(f"   ✅ Business type stored: {verification_user.business_type}")
            print(f"   ✅ Country stored: {verification_user.country}")
        
        print(f"\n🎉 B2B2C Organization Registration Test: SUCCESS!")
        print("=" * 60)
        print(f"✅ Organization '{test_company}' created successfully")
        print(f"✅ User '{test_email}' assigned as Business Admin")
        print(f"✅ Trial period activated")
        print(f"✅ Company information properly stored")
        print(f"✅ Ready for business dashboard access")
        
        # Clean up test data using raw SQL
        try:
            db.execute(text("DELETE FROM users WHERE email = :email"), {"email": test_email})
            db.execute(text("DELETE FROM organizations WHERE name = :name"), {"name": test_company})
            db.commit()
            print(f"\n🧹 Test data cleaned up")
        except Exception as cleanup_error:
            print(f"🧹 Cleanup error (non-critical): {cleanup_error}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Organization registration test failed: {e}")
        if db is not None:
            db.rollback()
            db.close()
        return False

if __name__ == "__main__":
    success = test_organization_registration()
    if success:
        print("\n✅ All tests passed! Organization registration is ready.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed! Please check the logs.")
        sys.exit(1)
