#!/usr/bin/env python3
"""
Test script for multi-tenant database functionality.
This script demonstrates creating user databases and verifying isolation.
"""

import sys
import os
import asyncio
import logging
from uuid import uuid4

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.services.multi_tenant_db_service import multi_tenant_db_service
from app.models.user import User
from app.models.therapy_sound import TherapySound
from sqlalchemy import text
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_multi_tenant_functionality():
    """Test the multi-tenant database functionality."""
    
    logger.info("🧪 Starting multi-tenant database functionality test...")
    
    # Test 1: Create test users
    logger.info("\n📝 Test 1: Creating test users...")
    
    test_users = []
    for i in range(3):
        user = User(
            id=1000 + i,  # Use predictable test IDs
            email=f"test_user_{i}@example.com",
            is_active=True,
            is_superuser=False,
            hashed_password="",
            telephone=f"+1555000{i:04d}",
            preferred_payment_method=None
        )
        test_users.append(user)
        logger.info(f"Created test user: {user.email} (ID: {        user.firebase_uid})")
    
    # Test 2: Create databases for each user
    logger.info("\n🏗️  Test 2: Creating user databases...")
    
    for i, user in enumerate(test_users):
        logger.info(f"Creating database for user {i+1}: {user.email}")
        
        success = await multi_tenant_db_service.create_user_database(user)
        if success:
            logger.info(f"✅ Database created successfully for {user.email}")
            
            # Test database connection
            db_name = multi_tenant_db_service.get_user_database_name(user.firebase_uid)
            logger.info(f"Database name: {db_name}")
            
        else:
            logger.error(f"❌ Failed to create database for {user.email}")
    
    # Test 3: Verify database isolation
    logger.info("\n🔒 Test 3: Testing database isolation...")
    
    for i, user in enumerate(test_users):
        logger.info(f"Testing database isolation for user {i+1}: {user.email}")
        
        try:
            # Get user database session
            db = multi_tenant_db_service.get_user_database_session(user.firebase_uid)
            
            # Add a test sound to this user's database
            test_sound = TherapySound(
                title=f"Test Sound for {user.email}",
                description=f"Private sound for user {i+1}",
                category="Test",
                duration=60.0,
                secure_storage_path=f"/test/user_{i}_sound.mp3",
                is_premium=False
            )
            
            db.add(test_sound)
            db.commit()
            
            # Verify the sound was added
            sounds_count = db.query(TherapySound).count()
            logger.info(f"✅ User {i+1} has {sounds_count} sounds in their database")
            
            db.close()
            
        except Exception as e:
            logger.error(f"❌ Database isolation test failed for {user.email}: {e}")
    
    # Test 4: Verify cross-database isolation
    logger.info("\n🚧 Test 4: Verifying cross-database isolation...")
    
    total_sounds_per_user = []
    for i, user in enumerate(test_users):
        try:
            db = multi_tenant_db_service.get_user_database_session(user.firebase_uid)
            sounds_count = db.query(TherapySound).count()
            total_sounds_per_user.append(sounds_count)
            logger.info(f"User {i+1} ({user.email}): {sounds_count} sounds")
            db.close()
        except Exception as e:
            logger.error(f"❌ Failed to count sounds for {user.email}: {e}")
    
    # Each user should have exactly 2 sounds (1 default + 1 test)
    expected_sounds = 2
    if all(count == expected_sounds for count in total_sounds_per_user):
        logger.info(f"✅ Cross-database isolation verified! Each user has exactly {expected_sounds} sounds.")
    else:
        logger.warning(f"⚠️  Cross-database isolation may have issues. Expected {expected_sounds} sounds per user, got: {total_sounds_per_user}")
    
    # Test 5: Database information
    logger.info("\n📊 Test 5: Getting database information...")
    
    for i, user in enumerate(test_users):
        try:
            db_info = await multi_tenant_db_service.get_database_info(user.firebase_uid)
            logger.info(f"User {i+1} database info:")
            logger.info(f"  - Database: {db_info.get('database_name')}")
            logger.info(f"  - Size: {db_info.get('size')}")
            logger.info(f"  - Tables: {db_info.get('table_count')}")
            logger.info(f"  - Status: {db_info.get('status')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to get database info for {user.email}: {e}")
    
    # Test 6: Cleanup (optional)
    logger.info("\n🧹 Test 6: Cleanup (deleting test databases)...")
    
    cleanup = input("Do you want to delete the test databases? (y/N): ").lower().strip()
    
    if cleanup == 'y':
        for i, user in enumerate(test_users):
            logger.info(f"Deleting database for user {i+1}: {user.email}")
            
            success = await multi_tenant_db_service.delete_user_database(user.firebase_uid)
            if success:
                logger.info(f"✅ Database deleted successfully for {user.email}")
            else:
                logger.error(f"❌ Failed to delete database for {user.email}")
    else:
        logger.info("🏁 Test databases kept for manual inspection.")
        logger.info("📝 To clean up later, you can use the admin API endpoints:")
        for i, user in enumerate(test_users):
            db_name = multi_tenant_db_service.get_user_database_name(user.firebase_uid)
            logger.info(f"  DELETE /admin/databases/{user.firebase_uid}/delete?confirm=true")
    
    logger.info("\n🎉 Multi-tenant database functionality test completed!")

if __name__ == "__main__":
    asyncio.run(test_multi_tenant_functionality())
