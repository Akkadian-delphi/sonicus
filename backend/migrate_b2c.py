"""
B2B2C to B2C Migration - Phase 1: Database Schema Changes

This script migrates the database from B2B2C (multi-organization) to B2C (direct user) architecture.
"""

import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_b2b2c_to_b2c():
    """Execute the B2B2C to B2C migration"""
    
    conn = psycopg2.connect(
        host='localhost',
        port=5433,
        database='sonicus_db', 
        user='postgres',
        password='e1efefe'
    )
    
    cur = None
    try:
        cur = conn.cursor()
        
        logger.info("Starting B2B2C to B2C migration...")
        
        # Phase 1: Create new B2C tables
        logger.info("Phase 1: Creating new B2C tables...")
        
        # Create user_subscriptions table (user-level subscriptions)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sonicus.user_subscriptions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id INTEGER NOT NULL REFERENCES sonicus.users(id),
                subscription_tier VARCHAR(50) NOT NULL DEFAULT 'starter',
                subscription_status VARCHAR(50) NOT NULL DEFAULT 'trial',
                billing_cycle VARCHAR(20) DEFAULT 'monthly',
                price_per_cycle DECIMAL(10,2),
                currency VARCHAR(3) DEFAULT 'USD',
                trial_start_date TIMESTAMPTZ,
                trial_end_date TIMESTAMPTZ,
                subscription_start_date TIMESTAMPTZ,
                subscription_end_date TIMESTAMPTZ,
                auto_renew BOOLEAN DEFAULT TRUE,
                payment_method_id VARCHAR(255),
                last_payment_date TIMESTAMPTZ,
                next_payment_date TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        ''')
        
        # Create user_sound_packages table (direct user-to-package assignments)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sonicus.user_sound_packages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id INTEGER NOT NULL REFERENCES sonicus.users(id),
                sound_package_id UUID NOT NULL REFERENCES sonicus.sound_packages(id),
                access_granted_at TIMESTAMPTZ DEFAULT NOW(),
                access_expires_at TIMESTAMPTZ,
                is_active BOOLEAN DEFAULT TRUE,
                usage_count INTEGER DEFAULT 0,
                last_used_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(user_id, sound_package_id)
            );
        ''')
        
        # Create user_preferences table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sonicus.user_preferences (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id INTEGER NOT NULL REFERENCES sonicus.users(id) UNIQUE,
                preferred_session_length INTEGER DEFAULT 20, -- minutes
                preferred_time_of_day VARCHAR(20), -- morning, afternoon, evening
                notification_preferences JSONB DEFAULT '{}',
                theme_preferences JSONB DEFAULT '{}',
                audio_preferences JSONB DEFAULT '{}',
                privacy_settings JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        ''')
        
        # Create user_analytics table (personal analytics)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sonicus.user_analytics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id INTEGER NOT NULL REFERENCES sonicus.users(id),
                date DATE NOT NULL,
                sessions_count INTEGER DEFAULT 0,
                total_listening_time_minutes INTEGER DEFAULT 0,
                unique_sounds_played INTEGER DEFAULT 0,
                average_session_length FLOAT DEFAULT 0,
                completion_rate FLOAT DEFAULT 0,
                stress_level_before FLOAT,
                stress_level_after FLOAT,
                mood_improvement_score FLOAT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(user_id, date)
            );
        ''')
        
        # Phase 2: Modify existing tables to remove organization dependencies
        logger.info("Phase 2: Removing organization dependencies...")
        
        # Update users table - remove organization_id dependency
        cur.execute('''
            ALTER TABLE sonicus.users 
            DROP CONSTRAINT IF EXISTS users_organization_id_fkey;
        ''')
        
        cur.execute('''
            ALTER TABLE sonicus.users 
            ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50) DEFAULT 'starter',
            ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE;
        ''')
        
        # Update sound_packages table - remove organization restriction
        cur.execute('''
            ALTER TABLE sonicus.sound_packages 
            DROP CONSTRAINT IF EXISTS sound_packages_organization_id_fkey;
        ''')
        
        cur.execute('''
            ALTER TABLE sonicus.sound_packages 
            ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS requires_subscription BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS minimum_tier VARCHAR(50) DEFAULT 'starter';
        ''')
        
        # Update webhook_endpoints table - remove organization filtering
        cur.execute('''
            ALTER TABLE sonicus.webhook_endpoints 
            DROP CONSTRAINT IF EXISTS webhook_endpoints_organization_id_fkey;
        ''')
        
        # Phase 3: Create indexes for performance
        logger.info("Phase 3: Creating indexes...")
        
        cur.execute('CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON sonicus.user_subscriptions(user_id);')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON sonicus.user_subscriptions(subscription_status);')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_user_sound_packages_user_id ON sonicus.user_sound_packages(user_id);')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_user_sound_packages_active ON sonicus.user_sound_packages(user_id, is_active);')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_user_analytics_user_date ON sonicus.user_analytics(user_id, date);')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON sonicus.users(subscription_status);')
        
        # Phase 4: Data migration - Move existing data to new structure
        logger.info("Phase 4: Migrating existing data...")
        
        # Migrate users - set subscription details based on their organization
        cur.execute('''
            UPDATE sonicus.users 
            SET subscription_tier = COALESCE(
                (SELECT subscription_tier FROM sonicus.organizations WHERE id = users.organization_id),
                'starter'
            ),
            subscription_status = CASE 
                WHEN (SELECT subscription_status::text FROM sonicus.organizations WHERE id = users.organization_id) = 'ACTIVE' THEN 'ACTIVE'::subscriptionstatus
                WHEN (SELECT subscription_status::text FROM sonicus.organizations WHERE id = users.organization_id) = 'EXPIRED' THEN 'EXPIRED'::subscriptionstatus
                WHEN (SELECT subscription_status::text FROM sonicus.organizations WHERE id = users.organization_id) = 'CANCELLED' THEN 'CANCELLED'::subscriptionstatus
                ELSE 'TRIAL'::subscriptionstatus
            END,
            trial_end_date = COALESCE(
                (SELECT trial_end_date FROM sonicus.organizations WHERE id = users.organization_id),
                NOW() + INTERVAL '14 days'
            ),
            is_premium = COALESCE(
                (SELECT subscription_tier != 'starter' FROM sonicus.organizations WHERE id = users.organization_id),
                FALSE
            )
            WHERE organization_id IS NOT NULL;
        ''')
        
        # Create user subscriptions for all existing users
        cur.execute('''
            INSERT INTO sonicus.user_subscriptions (
                user_id, subscription_tier, subscription_status, 
                trial_start_date, trial_end_date, created_at
            )
            SELECT 
                u.id,
                u.subscription_tier,
                u.subscription_status::text,
                u.created_at,
                u.trial_end_date,
                NOW()
            FROM sonicus.users u
            WHERE NOT EXISTS (
                SELECT 1 FROM sonicus.user_subscriptions us WHERE us.user_id = u.id
            );
        ''')
        
        # Create user preferences for all existing users
        cur.execute('''
            INSERT INTO sonicus.user_preferences (user_id, created_at)
            SELECT id, NOW()
            FROM sonicus.users
            WHERE NOT EXISTS (
                SELECT 1 FROM sonicus.user_preferences up WHERE up.user_id = users.id
            );
        ''')
        
        # Migrate sound package assignments from organization level to user level
        # Since organization_sound_packages has different structure, we'll make all sound_packages available to users
        cur.execute('''
            INSERT INTO sonicus.user_sound_packages (
                user_id, sound_package_id, access_granted_at, created_at
            )
            SELECT DISTINCT
                u.id as user_id,
                sp.id as sound_package_id,
                NOW(),
                NOW()
            FROM sonicus.users u
            CROSS JOIN sonicus.sound_packages sp
            WHERE u.organization_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM sonicus.user_sound_packages usp 
                WHERE usp.user_id = u.id AND usp.sound_package_id = sp.id
            )
            LIMIT 1000; -- Limit to avoid too many assignments
        ''')
        
        # Make sound packages public (remove organization restrictions)
        cur.execute('''
            UPDATE sonicus.sound_packages 
            SET is_public = TRUE,
                requires_subscription = CASE 
                    WHEN organization_id IS NOT NULL THEN TRUE 
                    ELSE FALSE 
                END,
                minimum_tier = 'starter';
        ''')
        
        conn.commit()
        logger.info("✅ B2B2C to B2C migration completed successfully!")
        
        # Phase 5: Report migration results
        cur.execute("SELECT COUNT(*) FROM sonicus.users;")
        result = cur.fetchone()
        user_count = result[0] if result else 0
        
        cur.execute("SELECT COUNT(*) FROM sonicus.user_subscriptions;")
        result = cur.fetchone()
        subscription_count = result[0] if result else 0
        
        cur.execute("SELECT COUNT(*) FROM sonicus.user_sound_packages;")
        result = cur.fetchone()
        package_assignments = result[0] if result else 0
        
        logger.info(f"Migration Summary:")
        logger.info(f"  - Users migrated: {user_count}")
        logger.info(f"  - User subscriptions created: {subscription_count}")
        logger.info(f"  - Sound package assignments: {package_assignments}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        if cur is not None:
            cur.close()
        conn.close()

if __name__ == "__main__":
    migrate_b2b2c_to_b2c()
