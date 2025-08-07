"""
Database migration utilities for B2B2C schema updates.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import create_engine, text, MetaData, inspect, Index, ForeignKeyConstraint
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.db.base import Base
from app.models.user import User
from app.models.organization import Organization, OrganizationSoundPackage, OrganizationAnalytics
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.therapy_sound import TherapySound

logger = logging.getLogger(__name__)

class DatabaseMigrationService:
    """Service for managing database schema migrations for B2B2C architecture."""
    
    def __init__(self, engine=None):
        """Initialize migration service with database engine."""
        if engine is None:
            # Use main database engine
            db_url = settings.DATABASE_URL or "postgresql://user:password@localhost/sonicus"
            connection_url = db_url.replace("postgresql+asyncpg", "postgresql")
            self.engine = create_engine(connection_url)
        else:
            self.engine = engine
    
    async def migrate_to_b2b2c_schema(self) -> bool:
        """
        Execute complete migration to B2B2C schema.
        
        Returns:
            bool: True if migration successful
        """
        try:
            logger.info("Starting B2B2C schema migration...")
            
            # Step 1: Create organization tables
            success = await self.create_organization_tables()
            if not success:
                return False
            
            # Step 2: Update user table with organization fields
            success = await self.update_user_table_for_b2b2c()
            if not success:
                return False
            
            # Step 3: Create indexes for performance
            success = await self.create_performance_indexes()
            if not success:
                return False
            
            # Step 4: Add foreign key constraints
            success = await self.add_foreign_key_constraints()
            if not success:
                return False
            
            # Step 5: Test with sample data
            success = await self.test_migration_with_sample_data()
            if not success:
                return False
            
            logger.info("B2B2C schema migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"B2B2C migration failed: {e}")
            return False
    
    async def create_organization_tables(self) -> bool:
        """Create organization-related tables."""
        try:
            logger.info("Creating organization tables...")
            
            # Create all tables defined in the models
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("Organization tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create organization tables: {e}")
            return False
    
    async def update_user_table_for_b2b2c(self) -> bool:
        """Update user table with organization and role fields."""
        try:
            logger.info("Updating user table for B2B2C...")
            
            with self.engine.connect() as conn:
                # Check if columns already exist
                inspector = inspect(self.engine)
                columns = [col['name'] for col in inspector.get_columns('users')]
                
                # Add organization_id column if it doesn't exist
                if 'organization_id' not in columns:
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN organization_id UUID REFERENCES organizations(id)
                        """))
                        conn.commit()
                        logger.info("Added organization_id column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("organization_id column already exists")
                        else:
                            raise e
                
                # Add role column if it doesn't exist
                if 'role' not in columns:
                    try:
                        # First create the enum type if it doesn't exist
                        conn.execute(text("""
                            CREATE TYPE userrole AS ENUM (
                                'SUPER_ADMIN', 'BUSINESS_ADMIN', 'STAFF', 'USER'
                            )
                        """))
                        conn.commit()
                        logger.info("Created userrole enum type")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("userrole enum type already exists")
                        else:
                            logger.error(f"Failed to create enum type: {e}")
                    
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN role userrole DEFAULT 'USER'
                        """))
                        conn.commit()
                        logger.info("Added role column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("role column already exists")
                        else:
                            raise e
                
                # Add database management fields if they don't exist
                if 'firebase_uid' not in columns:
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN firebase_uid VARCHAR UNIQUE
                        """))
                        conn.commit()
                        logger.info("Added firebase_uid column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("firebase_uid column already exists")
                        else:
                            raise e
                
                if 'database_created' not in columns:
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN database_created BOOLEAN DEFAULT FALSE
                        """))
                        conn.commit()
                        logger.info("Added database_created column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("database_created column already exists")
                        else:
                            raise e
                
                if 'database_created_at' not in columns:
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN database_created_at TIMESTAMP
                        """))
                        conn.commit()
                        logger.info("Added database_created_at column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("database_created_at column already exists")
                        else:
                            raise e
                
                # Add other missing user fields
                if 'telephone' not in columns:
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN telephone VARCHAR
                        """))
                        conn.commit()
                        logger.info("Added telephone column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("telephone column already exists")
                        else:
                            raise e
                
                if 'created_at' not in columns:
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN created_at TIMESTAMP DEFAULT NOW()
                        """))
                        conn.commit()
                        logger.info("Added created_at column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("created_at column already exists")
                        else:
                            raise e
                
                if 'subscription_status' not in columns:
                    try:
                        # Create subscription status enum
                        conn.execute(text("""
                            CREATE TYPE subscriptionstatus AS ENUM (
                                'TRIAL', 'ACTIVE', 'EXPIRED', 'CANCELLED'
                            )
                        """))
                        conn.commit()
                        logger.info("Created subscriptionstatus enum type")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("subscriptionstatus enum type already exists")
                        else:
                            logger.error(f"Failed to create subscription status enum: {e}")
                    
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN subscription_status subscriptionstatus DEFAULT 'TRIAL'
                        """))
                        conn.commit()
                        logger.info("Added subscription_status column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("subscription_status column already exists")
                        else:
                            raise e
            
            logger.info("User table updated successfully for B2B2C")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user table: {e}")
            return False
    
    async def create_performance_indexes(self) -> bool:
        """Create indexes for improved query performance."""
        try:
            logger.info("Creating performance indexes...")
            
            indexes_to_create = [
                # User table indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_organization_id ON users(organization_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role ON users(role)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at)",
                
                # Organization table indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_domain ON organizations(domain)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_status ON organizations(subscription_status)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_tier ON organizations(subscription_tier)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_created_at ON organizations(created_at)",
                
                # Organization sound packages indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_org_sound_packages_org_id ON organization_sound_packages(organization_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_org_sound_packages_active ON organization_sound_packages(is_active)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_org_sound_packages_created_at ON organization_sound_packages(created_at)",
                
                # Organization analytics indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_org_analytics_org_id ON organization_analytics(organization_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_org_analytics_date ON organization_analytics(date)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_org_analytics_org_date ON organization_analytics(organization_id, date)",
                
                # Subscription indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_org_id ON subscriptions(organization_id) WHERE organization_id IS NOT NULL",
                
                # Invoice indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_invoices_user_id ON invoices(user_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_invoices_status ON invoices(status)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_invoices_created_at ON invoices(created_at)",
                
                # Therapy sound indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_therapy_sounds_category ON therapy_sounds(category)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_therapy_sounds_premium ON therapy_sounds(is_premium)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_therapy_sounds_active ON therapy_sounds(is_active) WHERE is_active IS NOT NULL",
            ]
            
            with self.engine.connect() as conn:
                for index_sql in indexes_to_create:
                    try:
                        conn.execute(text(index_sql))
                        logger.debug(f"Created index: {index_sql}")
                    except Exception as e:
                        # Index might already exist, log but continue
                        logger.debug(f"Index creation skipped (might exist): {e}")
                
                conn.commit()
            
            logger.info("Performance indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create performance indexes: {e}")
            return False
    
    async def add_foreign_key_constraints(self) -> bool:
        """Add foreign key constraints and data integrity rules."""
        try:
            logger.info("Adding foreign key constraints...")
            
            constraints_to_add = [
                # User constraints
                """
                ALTER TABLE users 
                ADD CONSTRAINT fk_users_organization_id 
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL
                """,
                
                # Organization sound packages constraints
                """
                ALTER TABLE organization_sound_packages 
                ADD CONSTRAINT fk_org_sound_packages_organization_id 
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
                """,
                
                # Organization analytics constraints
                """
                ALTER TABLE organization_analytics 
                ADD CONSTRAINT fk_org_analytics_organization_id 
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
                """,
                
                # Add check constraints for data integrity
                """
                ALTER TABLE organizations 
                ADD CONSTRAINT chk_organizations_subscription_tier 
                CHECK (subscription_tier IN ('starter', 'professional', 'enterprise', 'custom'))
                """,
                
                """
                ALTER TABLE organizations 
                ADD CONSTRAINT chk_organizations_subscription_status 
                CHECK (subscription_status IN ('trial', 'active', 'suspended', 'cancelled'))
                """,
                
                """
                ALTER TABLE users 
                ADD CONSTRAINT chk_users_role 
                CHECK (role IN ('super_admin', 'business_admin', 'staff', 'user'))
                """,
                
                # Ensure organization admins belong to their organization
                """
                ALTER TABLE users 
                ADD CONSTRAINT chk_users_org_admin_belongs_to_org 
                CHECK (
                    (role != 'business_admin') OR 
                    (role = 'business_admin' AND organization_id IS NOT NULL)
                )
                """,
            ]
            
            with self.engine.connect() as conn:
                for constraint_sql in constraints_to_add:
                    try:
                        conn.execute(text(constraint_sql))
                        logger.debug(f"Added constraint: {constraint_sql[:50]}...")
                    except Exception as e:
                        # Constraint might already exist, log but continue
                        logger.debug(f"Constraint creation skipped (might exist): {e}")
                
                conn.commit()
            
            logger.info("Foreign key constraints added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add foreign key constraints: {e}")
            return False
    
    async def test_migration_with_sample_data(self) -> bool:
        """Test the migration by creating sample B2B2C data."""
        try:
            logger.info("Testing migration with sample data...")
            
            with self.engine.connect() as conn:
                # Create a sample organization
                org_result = conn.execute(text("""
                    INSERT INTO organizations (
                        id, name, display_name, primary_contact_email, 
                        subscription_tier, subscription_status, max_users, max_sound_libraries
                    ) VALUES (
                        gen_random_uuid(), 'Test Organization', 'Test Org Display', 
                        'admin@testorg.com', 'professional', 'trial', 50, 10
                    ) 
                    RETURNING id
                """))
                org_row = org_result.fetchone()
                if not org_row:
                    raise Exception("Failed to create test organization")
                org_id = org_row[0]
                logger.info(f"Created test organization with ID: {org_id}")
                
                # Create a business admin user for the organization
                user_result = conn.execute(text("""
                    INSERT INTO users (
                        email, firebase_uid, organization_id, role, 
                        created_at, subscription_status, hashed_password, is_active
                    ) VALUES (
                        'test.admin@testorg.com', 'test_firebase_uid_123', 
                        :org_id, 'BUSINESS_ADMIN', NOW(), 'TRIAL', 'dummy_hash', true
                    )
                    RETURNING id
                """), {"org_id": org_id})
                user_row = user_result.fetchone()
                if not user_row:
                    raise Exception("Failed to create test user")
                user_id = user_row[0]
                logger.info(f"Created test business admin user with ID: {user_id}")
                
                # Create a sound package for the organization
                package_result = conn.execute(text("""
                    INSERT INTO organization_sound_packages (
                        id, organization_id, package_name, description, 
                        sound_ids, is_active
                    ) VALUES (
                        gen_random_uuid(), :org_id, 'Test Wellness Package', 
                        'A test package for employee wellness', 
                        '["sound1", "sound2"]', true
                    )
                    RETURNING id
                """), {"org_id": org_id})
                package_row = package_result.fetchone()
                if not package_row:
                    raise Exception("Failed to create test package")
                package_id = package_row[0]
                logger.info(f"Created test sound package with ID: {package_id}")
                
                # Create analytics record
                analytics_result = conn.execute(text("""
                    INSERT INTO organization_analytics (
                        id, organization_id, date, total_users, 
                        active_users_today, total_sessions
                    ) VALUES (
                        gen_random_uuid(), :org_id, NOW(), 1, 1, 5
                    )
                    RETURNING id
                """), {"org_id": org_id})
                analytics_row = analytics_result.fetchone()
                if not analytics_row:
                    raise Exception("Failed to create test analytics")
                analytics_id = analytics_row[0]
                logger.info(f"Created test analytics record with ID: {analytics_id}")
                
                # Verify the relationships work
                verify_result = conn.execute(text("""
                    SELECT 
                        o.name as org_name,
                        u.email as admin_email,
                        u.role as admin_role,
                        p.package_name,
                        a.total_users
                    FROM organizations o
                    JOIN users u ON u.organization_id = o.id
                    JOIN organization_sound_packages p ON p.organization_id = o.id
                    JOIN organization_analytics a ON a.organization_id = o.id
                    WHERE o.id = :org_id
                """), {"org_id": org_id})
                
                result = verify_result.fetchone()
                if result:
                    logger.info(f"Migration test successful! Data integrity verified:")
                    logger.info(f"  Organization: {result[0]}")
                    logger.info(f"  Admin: {result[1]} ({result[2]})")
                    logger.info(f"  Package: {result[3]}")
                    logger.info(f"  Analytics: {result[4]} users")
                else:
                    logger.error("Migration test failed: Could not verify relationships")
                    return False
                
                conn.commit()
            
            logger.info("Migration test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration test failed: {e}")
            return False
    
    async def add_company_information_fields(self) -> bool:
        """
        Add company information fields to users table for B2B2C registration.
        
        Returns:
            bool: True if migration successful
        """
        try:
            logger.info("Adding company information fields to users table...")
            
            with self.engine.connect() as conn:
                # Check if columns already exist
                inspector = inspect(self.engine)
                columns = [col['name'] for col in inspector.get_columns('users')]
                
                # Add company_name column if it doesn't exist
                if 'company_name' not in columns:
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN company_name VARCHAR
                        """))
                        conn.commit()
                        logger.info("Added company_name column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("company_name column already exists")
                        else:
                            raise e
                
                # Add business_type column if it doesn't exist
                if 'business_type' not in columns:
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN business_type VARCHAR
                        """))
                        conn.commit()
                        logger.info("Added business_type column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("business_type column already exists")
                        else:
                            raise e
                
                # Add country column if it doesn't exist
                if 'country' not in columns:
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN country VARCHAR(2)
                        """))
                        conn.commit()
                        logger.info("Added country column to users table")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e).lower():
                            logger.debug("country column already exists")
                        else:
                            raise e
                
                # Create indexes for the new fields
                indexes_to_create = [
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_company_name ON users(company_name)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_business_type ON users(business_type)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_country ON users(country)",
                ]
                
                for index_sql in indexes_to_create:
                    try:
                        conn.execute(text(index_sql))
                        logger.debug(f"Created index: {index_sql}")
                    except Exception as e:
                        logger.debug(f"Index creation skipped (might exist): {e}")
                
                conn.commit()
            
            logger.info("Company information fields added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add company information fields: {e}")
            return False
    
    async def rollback_b2b2c_migration(self) -> bool:
        """
        Rollback B2B2C migration (use with extreme caution).
        
        Returns:
            bool: True if rollback successful
        """
        try:
            logger.warning("Starting B2B2C migration rollback...")
            
            with self.engine.connect() as conn:
                # Drop tables in reverse order of dependencies
                rollback_statements = [
                    "DROP TABLE IF EXISTS organization_analytics CASCADE",
                    "DROP TABLE IF EXISTS organization_sound_packages CASCADE",
                    "DROP TABLE IF EXISTS organizations CASCADE",
                    "ALTER TABLE users DROP COLUMN IF EXISTS organization_id",
                    "ALTER TABLE users DROP COLUMN IF EXISTS role",
                    "ALTER TABLE users DROP COLUMN IF EXISTS database_created",
                    "ALTER TABLE users DROP COLUMN IF EXISTS database_created_at",
                    "DROP TYPE IF EXISTS userrole",
                ]
                
                for statement in rollback_statements:
                    try:
                        conn.execute(text(statement))
                        logger.debug(f"Executed rollback: {statement}")
                    except Exception as e:
                        logger.debug(f"Rollback statement skipped: {e}")
                
                conn.commit()
            
            logger.warning("B2B2C migration rollback completed")
            return True
            
        except Exception as e:
            logger.error(f"Migration rollback failed: {e}")
            return False

# Global migration service instance
migration_service = DatabaseMigrationService()
