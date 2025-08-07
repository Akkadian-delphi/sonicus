#!/usr/bin/env python3
"""
Migration script to add company information fields to users table.
This adds support for B2B2C registration with company information.
"""

import asyncio
import sys
import os
import logging

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.migrations import DatabaseMigrationService
from app.core.config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Run company fields migration."""
    try:
        logger.info("🚀 Starting company information fields migration...")
        
        # Initialize migration service
        migration_service = DatabaseMigrationService()
        
        # Run the company fields migration
        success = await migration_service.add_company_information_fields()
        
        if success:
            logger.info("✅ Company information fields migration completed successfully!")
            print("\n" + "="*60)
            print("🎉 MIGRATION SUCCESSFUL!")
            print("✅ Added company_name, business_type, and country fields to users table")
            print("✅ Created performance indexes for new fields")
            print("✅ Your registration form can now collect company information")
            print("="*60)
            return 0
        else:
            logger.error("❌ Company information fields migration failed!")
            print("\n" + "="*60)
            print("❌ MIGRATION FAILED!")
            print("Please check the logs for details")
            print("="*60)
            return 1
            
    except Exception as e:
        logger.error(f"💥 Migration script failed: {e}")
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    # Run the migration
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
