#!/usr/bin/env python3
"""
Database migration script for multi-tenant setup.
This script adds the new database tracking columns to the User model.
"""

import sys
import os
import logging
from sqlalchemy import text
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db.session import engine
from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run database migration to add new User model fields."""
    
    migration_queries = [
        # Add database_created column
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS database_created BOOLEAN DEFAULT FALSE;
        """,
        
        # Add database_created_at column
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS database_created_at TIMESTAMP;
        """,
        
        # Update existing users to mark them as needing database creation
        """
        UPDATE users 
        SET database_created = FALSE 
        WHERE database_created IS NULL;
        """
    ]
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                for i, query in enumerate(migration_queries, 1):
                    logger.info(f"Running migration step {i}/{len(migration_queries)}")
                    conn.execute(text(query))
                    logger.info(f"✓ Migration step {i} completed successfully")
                
                # Commit the transaction
                trans.commit()
                logger.info("✅ All migration steps completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"❌ Migration failed, rolling back: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Failed to run migration: {e}")
        sys.exit(1)

def verify_migration():
    """Verify that the migration was applied correctly."""
    
    verification_queries = [
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'database_created';",
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'database_created_at';",
        "SELECT COUNT(*) as user_count FROM users;"
    ]
    
    try:
        with engine.connect() as conn:
            # Check if columns exist
            result1 = conn.execute(text(verification_queries[0]))
            database_created_exists = result1.fetchone() is not None
            
            result2 = conn.execute(text(verification_queries[1]))
            database_created_at_exists = result2.fetchone() is not None
            
            result3 = conn.execute(text(verification_queries[2]))
            user_count_row = result3.fetchone()
            user_count = user_count_row[0] if user_count_row else 0
            
            logger.info(f"✓ database_created column exists: {database_created_exists}")
            logger.info(f"✓ database_created_at column exists: {database_created_at_exists}")
            logger.info(f"✓ Total users in database: {user_count}")
            
            if database_created_exists and database_created_at_exists:
                logger.info("✅ Migration verification successful!")
                return True
            else:
                logger.error("❌ Migration verification failed!")
                return False
                
    except Exception as e:
        logger.error(f"❌ Failed to verify migration: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting multi-tenant database migration...")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # Run migration
    run_migration()
    
    # Verify migration
    if verify_migration():
        logger.info("🎉 Migration completed successfully!")
        
        logger.info("\n📋 Next steps:")
        logger.info("1. Restart your application to use the new multi-tenant system")
        logger.info("2. Existing users will have their personal databases created on first login")
        logger.info("3. New users will automatically get personal databases upon registration")
        logger.info("4. Use the admin dashboard to monitor and manage user databases")
        
    else:
        logger.error("💥 Migration verification failed!")
        sys.exit(1)
