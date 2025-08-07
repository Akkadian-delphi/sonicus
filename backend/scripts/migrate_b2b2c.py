#!/usr/bin/env python3
"""
B2B2C Database Migration Script
This script performs all necessary database migrations for the B2B2C architecture.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.migrations import migration_service
from app.services.organization_db_service import organization_db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_b2b2c_migration():
    """Execute the complete B2B2C migration process."""
    try:
        logger.info("🚀 Starting B2B2C Database Migration")
        logger.info("=" * 50)
        
        # Step 1: Main database schema migration
        logger.info("📋 Step 1: Migrating main database schema to B2B2C...")
        success = await migration_service.migrate_to_b2b2c_schema()
        if not success:
            logger.error("❌ Main database migration failed!")
            return False
        logger.info("✅ Main database schema migration completed successfully!")
        
        # Step 2: Organization database service health check
        logger.info("📋 Step 2: Verifying organization database service...")
        health_check = await organization_db_service.health_check_all_organization_databases()
        logger.info(f"📊 Organization databases status: {health_check['healthy_databases']}/{health_check['total_databases']} healthy")
        
        # If no organization databases exist yet, that's normal for a fresh migration
        if health_check['total_databases'] == 0:
            logger.info("ℹ️  No organization databases found - this is normal for a fresh B2B2C migration")
        
        logger.info("=" * 50)
        logger.info("🎉 B2B2C Migration completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Organizations can now be created through the Super Admin panel")
        logger.info("2. Each organization will get its own isolated database")
        logger.info("3. Users can be assigned to organizations with specific roles")
        logger.info("4. Business admins can manage their organization's users and content")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ B2B2C migration failed with error: {e}")
        logger.exception("Full error traceback:")
        return False

async def rollback_b2b2c_migration():
    """Rollback the B2B2C migration (use with extreme caution)."""
    logger.warning("⚠️  DANGER: Rolling back B2B2C migration!")
    logger.warning("This will remove all organization data and relationships!")
    
    response = input("Are you sure you want to proceed? Type 'YES' to confirm: ")
    if response != "YES":
        logger.info("Migration rollback cancelled.")
        return False
    
    try:
        success = await migration_service.rollback_b2b2c_migration()
        if success:
            logger.warning("🔄 B2B2C migration rolled back successfully")
        else:
            logger.error("❌ B2B2C migration rollback failed")
        return success
        
    except Exception as e:
        logger.error(f"❌ B2B2C migration rollback failed: {e}")
        return False

async def test_organization_database_creation():
    """Test organization database creation functionality."""
    logger.info("🧪 Testing organization database creation...")
    
    try:
        # Import required models
        from app.models.organization import Organization
        import uuid
        
        # Create a test organization object
        test_org = Organization(
            id=uuid.uuid4(),
            name="Test Migration Organization",
            display_name="Test Org",
            primary_contact_email="test@migration.com",
            subscription_tier="starter",
            subscription_status="trial"
        )
        
        # Test database creation
        logger.info(f"Creating database for test organization: {test_org.name}")
        success = await organization_db_service.create_organization_database(test_org)
        
        if success:
            logger.info("✅ Test organization database created successfully!")
            
            # Get database info
            db_info = await organization_db_service.get_organization_database_info(str(test_org.id))
            logger.info(f"📊 Database info: {db_info}")
            
            # Clean up test database
            logger.info("🧹 Cleaning up test database...")
            cleanup_success = await organization_db_service.delete_organization_database(str(test_org.id))
            if cleanup_success:
                logger.info("✅ Test database cleaned up successfully!")
            else:
                logger.warning("⚠️  Test database cleanup failed - manual cleanup may be required")
        else:
            logger.error("❌ Test organization database creation failed!")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Organization database test failed: {e}")
        return False

def main():
    """Main function to handle command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="B2B2C Database Migration Tool")
    parser.add_argument(
        "action", 
        choices=["migrate", "rollback", "test"],
        help="Action to perform: migrate (run B2B2C migration), rollback (undo migration), test (test org db creation)"
    )
    
    args = parser.parse_args()
    
    exit_code = 0  # Default success code
    
    if args.action == "migrate":
        success = asyncio.run(run_b2b2c_migration())
        exit_code = 0 if success else 1
    elif args.action == "rollback":
        success = asyncio.run(rollback_b2b2c_migration())
        exit_code = 0 if success else 1
    elif args.action == "test":
        success = asyncio.run(test_organization_database_creation())
        exit_code = 0 if success else 1
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
