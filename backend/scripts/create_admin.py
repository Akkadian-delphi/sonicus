#!/usr/bin/env python
"""
Script to create an admin user for the Sonicus application.

Usage:
    python scripts/create_admin.py --email admin@example.com --password securepassword

Options:
    --email          Email address for the admin user (required)
    --password       Password for the admin user (required)
    --verify         Verify password complexity (default: True)
    --force          Don't ask for confirmation (default: False)
    --inactive       Create the user as inactive (default: False)
"""
import argparse
import sys
import os
import logging
import re
from pathlib import Path
import getpass

# Ensure that the application root directory is in sys.path
app_root = Path(__file__).parent.parent
sys.path.append(str(app_root))

from app.db.session import SessionLocal, engine
from app.models.user import User
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.therapy_sound import TherapySound
from app.db.base import Base  # Import Base for metadata
from passlib.context import CryptContext

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levellevel)s - %(message)s")
logger = logging.getLogger("create-admin")

# Set up the password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_database_tables():
    """Create all database tables if they don't exist."""
    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")

def validate_password(password: str) -> bool:
    """
    Validate password complexity.
    
    Requirements:
    - At least 8 characters
    - Contains at least one lowercase letter
    - Contains at least one uppercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < 8:
        print("Password must be at least 8 characters long.")
        return False
        
    if not re.search(r"[a-z]", password):
        print("Password must contain at least one lowercase letter.")
        return False
        
    if not re.search(r"[A-Z]", password):
        print("Password must contain at least one uppercase letter.")
        return False
        
    if not re.search(r"\d", password):
        print("Password must contain at least one digit.")
        return False
        
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        print("Password must contain at least one special character.")
        return False
        
    return True

def create_admin_user(email: str, password: str, verify_password: bool = True, inactive: bool = False) -> None:
    """Create an admin user with the given email and password."""
    # Verify password complexity if requested
    if verify_password and not validate_password(password):
        logger.error("Password does not meet complexity requirements.")
        sys.exit(1)
    
    # Ensure database tables exist
    create_database_tables()
    
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            if existing_user.is_superuser:
                logger.info(f"Admin user with email {email} already exists.")
                return
            else:
                logger.info(f"User with email {email} exists but is not an admin. Upgrading to admin...")
                existing_user.is_superuser = True
                db.commit()
                logger.info(f"User {email} has been upgraded to admin status.")
                return
        
        # Create new admin user with securely hashed password
        hashed_password = pwd_context.hash(password)
        
        new_admin = User(
            email=email,
            hashed_password=hashed_password,
            is_active=not inactive,  # Set active status based on parameter
            is_superuser=True
        )
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        
        logger.info(f"Admin user created successfully with email: {email}")
        
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def main() -> None:
    """Parse command line arguments and create the admin user."""
    parser = argparse.ArgumentParser(description="Create an admin user for the Sonicus application.")
    parser.add_argument("--email", help="Email address for the admin user")
    parser.add_argument("--password", help="Password for the admin user")
    parser.add_argument("--verify", action="store_true", default=True, help="Verify password complexity")
    parser.add_argument("--no-verify", dest="verify", action="store_false", help="Skip password complexity verification")
    parser.add_argument("--force", action="store_true", help="Don't ask for confirmation")
    parser.add_argument("--inactive", action="store_true", help="Create the user as inactive")
    
    args = parser.parse_args()
    
    # Interactive mode if email or password not provided
    email = args.email
    if not email:
        email = input("Enter admin email address: ")
    
    password = args.password
    if not password:
        password = getpass.getpass("Enter admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            logger.error("Passwords don't match.")
            sys.exit(1)
    
    # Confirm creation unless forced
    if not args.force:
        confirm = input(f"Create admin user with email '{email}'? (Y/n): ")
        if confirm.lower() not in ["", "y", "yes"]:
            logger.info("Admin user creation cancelled.")
            sys.exit(0)
    
    try:
        create_admin_user(email, password, args.verify, args.inactive)
    except Exception as e:
        logger.error(f"Failed to create admin user: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
