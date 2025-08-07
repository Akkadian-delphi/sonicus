#!/usr/bin/env python3
"""
Database setup and troubleshooting script for Sonicus.
This script helps diagnose and fix database connection issues.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.core.config import settings
    from app.db.session import engine
    from sqlalchemy import text, create_engine
    from sqlalchemy_utils import database_exists, create_database
    import psycopg2
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you've installed all requirements: pip install -r requirements.txt")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def test_postgres_service():
    """Test if PostgreSQL service is running."""
    logger.info("Testing PostgreSQL service...")
    
    try:
        # Try to connect to default postgres database
        test_conn = psycopg2.connect(
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database="postgres"  # Connect to default postgres db
        )
        test_conn.close()
        logger.info("✅ PostgreSQL service is running and accessible")
        return True
    except psycopg2.OperationalError as e:
        if "password authentication failed" in str(e):
            logger.error("❌ Password authentication failed")
            return False
        elif "connection refused" in str(e):
            logger.error("❌ PostgreSQL service is not running")
            return False
        else:
            logger.error(f"❌ Connection error: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def show_connection_info():
    """Display current database connection settings."""
    logger.info("Current database configuration:")
    logger.info(f"  Host: {settings.POSTGRES_SERVER}")
    logger.info(f"  Port: {settings.POSTGRES_PORT}")
    logger.info(f"  User: {settings.POSTGRES_USER}")
    logger.info(f"  Password: {'*' * len(settings.POSTGRES_PASSWORD)}")
    logger.info(f"  Database: {settings.POSTGRES_DB}")
    logger.info(f"  Schema: {settings.POSTGRES_SCHEMA}")

def create_database_if_needed():
    """Create the application database if it doesn't exist."""
    logger.info(f"Checking if database '{settings.POSTGRES_DB}' exists...")
    
    try:
        db_url = str(engine.url)
        if database_exists(db_url):
            logger.info("✅ Database already exists")
            return True
        else:
            logger.info(f"Creating database '{settings.POSTGRES_DB}'...")
            create_database(db_url)
            logger.info("✅ Database created successfully")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False

def create_schema_if_needed():
    """Create the application schema if it doesn't exist."""
    logger.info(f"Checking if schema '{settings.POSTGRES_SCHEMA}' exists...")
    
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.POSTGRES_SCHEMA}"))
            conn.commit()
            logger.info("✅ Schema exists or created successfully")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to create schema: {e}")
        return False

def show_troubleshooting_tips():
    """Display troubleshooting tips for common issues."""
    logger.info("\n🔧 TROUBLESHOOTING TIPS:")
    logger.info("1. Start PostgreSQL service:")
    logger.info("   - macOS: brew services start postgresql")
    logger.info("   - Linux: sudo systemctl start postgresql")
    logger.info("   - Windows: Start PostgreSQL service from Services")
    
    logger.info("\n2. Check if PostgreSQL is running:")
    logger.info("   - macOS/Linux: brew services list | grep postgresql")
    logger.info("   - All platforms: netstat -an | grep 5432")
    
    logger.info("\n3. Test manual connection:")
    logger.info(f"   psql -h {settings.POSTGRES_SERVER} -U {settings.POSTGRES_USER} -d postgres")
    
    logger.info("\n4. Reset postgres user password (if needed):")
    logger.info("   - Connect as superuser: sudo -u postgres psql")
    logger.info("   - Change password: ALTER USER postgres PASSWORD 'your_password';")
    
    logger.info("\n5. Create database manually (if needed):")
    logger.info(f"   createdb -h {settings.POSTGRES_SERVER} -U {settings.POSTGRES_USER} {settings.POSTGRES_DB}")
    
    logger.info("\n6. Check .env file has correct credentials")

def main():
    """Main setup and diagnostic function."""
    logger.info("🚀 Sonicus Database Setup and Diagnostics")
    logger.info("=" * 50)
    
    show_connection_info()
    logger.info("")
    
    # Test PostgreSQL service
    if not test_postgres_service():
        show_troubleshooting_tips()
        return False
    
    # Create database if needed
    if not create_database_if_needed():
        show_troubleshooting_tips()
        return False
    
    # Create schema if needed
    if not create_schema_if_needed():
        show_troubleshooting_tips()
        return False
    
    logger.info("\n✅ Database setup completed successfully!")
    logger.info("You can now start the Sonicus application with: python run.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
