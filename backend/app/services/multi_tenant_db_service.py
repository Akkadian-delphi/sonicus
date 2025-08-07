"""
Multi-tenant database management service - Updated for B2B2C architecture.
Creates and manages separate PostgreSQL databases for organizations and users.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.db.base import Base

logger = logging.getLogger(__name__)

class MultiTenantDatabaseService:
    """Service for managing user-specific databases - Enhanced for B2B2C."""
    
    def __init__(self):
        # Master database connection for creating user databases
        db_url = settings.DATABASE_URL or "postgresql://user:password@localhost/sonicus"
        master_url = db_url.replace("postgresql+asyncpg", "postgresql")
        
        # Build connection URL for postgres database
        if "://" in master_url:
            protocol_part = master_url.split("://")[0]
            remaining_part = master_url.split("://")[1]
            
            if "@" in remaining_part:
                auth_part, host_part = remaining_part.split("@", 1)
                # Replace database name with 'postgres'
                if "/" in host_part:
                    host_port_part = host_part.split("/")[0]
                    postgres_url = f"{protocol_part}://{auth_part}@{host_port_part}/postgres"
                else:
                    postgres_url = f"{protocol_part}://{auth_part}@{host_part}/postgres"
            else:
                postgres_url = f"{protocol_part}://{remaining_part}/postgres"
        else:
            postgres_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/postgres"
        
        self.master_engine = create_engine(postgres_url, echo=settings.SQL_ECHO)
        
    def get_user_database_name(self, user_id: int) -> str:
        """Generate database name based on user ID."""
        return f"sonicus_user_{user_id}"
    
    def get_user_database_url(self, user_id: int) -> str:
        """Get database URL for a specific user."""
        db_name = self.get_user_database_name(user_id)
        base_url = settings.DATABASE_URL or "postgresql://user:password@localhost/sonicus"
        
        # Replace database name in the URL
        if "://" in base_url:
            protocol_part = base_url.split("://")[0]
            remaining_part = base_url.split("://")[1]
            
            if "@" in remaining_part:
                auth_part, host_part = remaining_part.split("@", 1)
                if "/" in host_part:
                    host_port_part = host_part.split("/")[0]
                    return f"{protocol_part}://{auth_part}@{host_port_part}/{db_name}"
                else:
                    return f"{protocol_part}://{auth_part}@{host_part}/{db_name}"
        
        # Fallback to manual construction
        return (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
            f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{db_name}"
        )
    
    async def create_user_database(self, user: User) -> bool:
        """
        Create a new database for a user.
        
        Args:
            user: User object with id
            
        Returns:
            bool: True if database was created successfully
        """
        user_id = getattr(user, 'id', None)
        if not user_id:
            logger.error(f"User {getattr(user, 'email', 'unknown')} has no id")
            return False
            
        db_name = self.get_user_database_name(user_id)
        
        try:
            # Create database using raw connection
            connection = psycopg2.connect(
                host=settings.POSTGRES_SERVER,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database="postgres"
            )
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = connection.cursor()
            
            # Check if database already exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_name,)
            )
            
            if cursor.fetchone():
                logger.info(f"Database {db_name} already exists for user {user.email}")
                cursor.close()
                connection.close()
                return True
            
            # Create the database
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            logger.info(f"Created database {db_name} for user {user.email}")
            
            cursor.close()
            connection.close()
            
            # Initialize the database schema
            await self.initialize_user_database_schema(user_id)
            
            # Update user record to mark database as created
            await self._mark_database_created(user)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database for user {user.email}: {e}")
            return False
    
    async def initialize_user_database_schema(self, user_id: int) -> bool:
        """Initialize the database schema for a user database."""
        try:
            db_url = self.get_user_database_url(user_id)
            engine = create_engine(db_url, echo=settings.SQL_ECHO)
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            
            # Add any initial data or custom setup here
            with engine.connect() as conn:
                # Example: Insert default therapy sound categories
                conn.execute(text("""
                    INSERT INTO therapy_sounds (title, description, category, duration, secure_storage_path, is_premium)
                    VALUES 
                    ('Welcome Sound', 'Your personal welcome therapy sound', 'Personal', 30.0, '/default/welcome.mp3', false)
                    ON CONFLICT DO NOTHING
                """))
                conn.commit()
            
            engine.dispose()
            logger.info(f"Initialized schema for user database: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize schema for user {user_id}: {e}")
            return False
    
    def get_user_database_engine(self, user_id: int):
        """Get SQLAlchemy engine for a user's database."""
        db_url = self.get_user_database_url(user_id)
        return create_engine(db_url, echo=settings.SQL_ECHO)
    
    def get_user_database_session(self, user_id: int):
        """Get database session for a user's database."""
        engine = self.get_user_database_engine(user_id)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    
    async def delete_user_database(self, user_id: int) -> bool:
        """
        Delete a user's database (use with caution).
        
        Args:
            user_id: User's ID
            
        Returns:
            bool: True if database was deleted successfully
        """
        db_name = self.get_user_database_name(user_id)
        
        try:
            connection = psycopg2.connect(
                host=settings.POSTGRES_SERVER,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database="postgres"
            )
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = connection.cursor()
            
            # Terminate active connections to the database
            cursor.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """)
            
            # Drop the database
            cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
            logger.info(f"Deleted database {db_name}")
            
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete database {db_name}: {e}")
            return False
    
    async def backup_user_database(self, user_id: int, backup_path: str) -> bool:
        """
        Create a backup of user's database.
        
        Args:
            user_id: User's ID
            backup_path: Path where to store the backup
            
        Returns:
            bool: True if backup was created successfully
        """
        db_name = self.get_user_database_name(user_id)
        
        try:
            import subprocess
            
            # Use pg_dump to create backup
            cmd = [
                'pg_dump',
                '-h', settings.POSTGRES_SERVER,
                '-p', str(settings.POSTGRES_PORT),
                '-U', settings.POSTGRES_USER,
                '-d', db_name,
                '-f', backup_path,
                '--no-password'
            ]
            
            # Set password as environment variable
            env = {'PGPASSWORD': settings.POSTGRES_PASSWORD}
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Created backup for database {db_name} at {backup_path}")
                return True
            else:
                logger.error(f"Backup failed for {db_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to backup database {db_name}: {e}")
            return False
    
    async def get_database_info(self, user_id: int) -> Dict[str, Any]:
        """Get information about a user's database."""
        db_name = self.get_user_database_name(user_id)
        
        try:
            db_url = self.get_user_database_url(user_id)
            engine = create_engine(db_url, echo=False)
            
            with engine.connect() as conn:
                # Get database size
                size_result = conn.execute(text(f"""
                    SELECT pg_size_pretty(pg_database_size('{db_name}')) as size
                """))
                size_row = size_result.fetchone()
                size = size_row[0] if size_row else "Unknown"
                
                # Get table count
                tables_result = conn.execute(text("""
                    SELECT COUNT(*) as table_count
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """))
                tables_row = tables_result.fetchone()
                table_count = tables_row[0] if tables_row else 0
                
                # Get connection count
                connections_result = conn.execute(text(f"""
                    SELECT COUNT(*) as connections
                    FROM pg_stat_activity
                    WHERE datname = '{db_name}'
                """))
                connections_row = connections_result.fetchone()
                connections = connections_row[0] if connections_row else 0
            
            engine.dispose()
            
            return {
                "database_name": db_name,
                "size": size,
                "table_count": table_count,
                "active_connections": connections,
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Failed to get database info for {user_id}: {e}")
            return {
                "database_name": db_name,
                "status": "error",
                "error": str(e)
            }
    
    async def _mark_database_created(self, user: User) -> None:
        """Mark user's database as created in the master database."""
        try:
            from app.db.session import get_db
            
            # This is a bit tricky since we need to update the user in the master DB
            # We'll need to create a new session to the master database
            from sqlalchemy.orm import sessionmaker
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.master_engine)
            
            with SessionLocal() as db:
                # Find user by id and update
                user_id = getattr(user, 'id', None)
                if user_id:
                    master_user = db.query(User).filter(User.id == user_id).first()
                    if master_user:
                        setattr(master_user, 'database_created', True)
                        setattr(master_user, 'database_created_at', datetime.now())
                        db.commit()
                        logger.info(f"Marked database as created for user: {user_id}")
                        
        except Exception as e:
            logger.error(f"Failed to mark database as created for user: {e}")
            # Don't raise exception as this is not critical

# Global instance
multi_tenant_db_service = MultiTenantDatabaseService()
