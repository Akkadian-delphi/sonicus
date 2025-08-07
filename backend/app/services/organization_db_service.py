"""
Enhanced multi-tenant database service for B2B2C architecture.
Supports both user-based and organization-based database isolation.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import uuid

from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.db.base import Base

logger = logging.getLogger(__name__)

class OrganizationDatabaseService:
    """Service for managing organization-specific databases in B2B2C architecture."""
    
    def __init__(self):
        # Master database connection for creating organization databases
        db_url = settings.DATABASE_URL or "postgresql://user:password@localhost/sonicus"
        master_url = db_url.replace("postgresql+asyncpg", "postgresql")
        
        # Extract connection components for master database
        if "://" in master_url:
            parts = master_url.split("://")[1]
            if "@" in parts:
                auth_part, host_part = parts.split("@", 1)
                if ":" in auth_part:
                    user, password = auth_part.split(":", 1)
                else:
                    user = auth_part
                    password = ""
                
                if "/" in host_part:
                    host_port, _ = host_part.split("/", 1)
                else:
                    host_port = host_part
                
                if ":" in host_port:
                    host, port = host_port.split(":", 1)
                else:
                    host = host_port
                    port = "5432"
            else:
                # Fallback to settings
                user = settings.POSTGRES_USER or "postgres"
                password = settings.POSTGRES_PASSWORD or ""
                host = settings.POSTGRES_SERVER or "localhost"
                port = str(settings.POSTGRES_PORT or 5432)
        else:
            # Fallback to settings
            user = settings.POSTGRES_USER or "postgres"
            password = settings.POSTGRES_PASSWORD or ""
            host = settings.POSTGRES_SERVER or "localhost"
            port = str(settings.POSTGRES_PORT or 5432)
        
        self.master_engine = create_engine(
            f"postgresql://{user}:{password}@{host}:{port}/postgres",
            echo=settings.SQL_ECHO
        )
        
        # Store connection info for organization databases
        self.db_user = user
        self.db_password = password
        self.db_host = host
        self.db_port = port
        
    def get_organization_database_name(self, org_id: str) -> str:
        """Generate database name based on organization ID."""
        # Clean org ID and create valid database name
        clean_id = str(org_id).replace('-', '_')
        return f"sonicus_org_{clean_id}"
    
    def get_organization_database_url(self, org_id: str) -> str:
        """Get database URL for a specific organization."""
        db_name = self.get_organization_database_name(org_id)
        return (
            f"postgresql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{db_name}"
        )
    
    async def create_organization_database(self, organization: Organization) -> bool:
        """
        Create a new database for an organization.
        
        Args:
            organization: Organization object with id
            
        Returns:
            bool: True if database was created successfully
        """
        org_id = str(organization.id)
        org_name = getattr(organization, 'name', 'Unknown Organization')
        db_name = self.get_organization_database_name(org_id)
        
        try:
            # Create database using raw connection
            connection = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
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
                logger.info(f"Database {db_name} already exists for organization {org_name}")
                cursor.close()
                connection.close()
                return True
            
            # Create the database
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            logger.info(f"Created database {db_name} for organization {org_name}")
            
            cursor.close()
            connection.close()
            
            # Initialize the database schema
            await self.initialize_organization_database_schema(org_id)
            
            # Update organization record to mark database as created
            await self._mark_organization_database_created(organization)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database for organization {org_name}: {e}")
            return False
    
    async def initialize_organization_database_schema(self, org_id: str) -> bool:
        """Initialize the database schema for an organization database."""
        try:
            db_url = self.get_organization_database_url(org_id)
            engine = create_engine(db_url, echo=settings.SQL_ECHO)
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            
            # Add organization-specific setup
            with engine.connect() as conn:
                # Set up organization-specific configurations
                conn.execute(text("""
                    -- Create organization-specific indexes
                    CREATE INDEX IF NOT EXISTS idx_org_users_role ON users(role);
                    CREATE INDEX IF NOT EXISTS idx_org_users_created_at ON users(created_at);
                    CREATE INDEX IF NOT EXISTS idx_org_therapy_sounds_category ON therapy_sounds(category);
                    
                    -- Insert default therapy sound categories for this organization
                    INSERT INTO therapy_sounds (title, description, category, duration, secure_storage_path, is_premium)
                    VALUES 
                    ('Welcome to Your Wellness Journey', 'Personalized welcome sound for your organization', 'Welcome', 60.0, '/org/welcome.mp3', false),
                    ('Focus Boost', 'Enhanced focus for workplace productivity', 'Focus', 300.0, '/org/focus.mp3', true),
                    ('Stress Relief', 'Immediate stress relief for busy professionals', 'Relaxation', 480.0, '/org/stress_relief.mp3', true)
                    ON CONFLICT DO NOTHING;
                """))
                conn.commit()
            
            engine.dispose()
            logger.info(f"Initialized schema for organization database: {org_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize schema for organization {org_id}: {e}")
            return False
    
    def get_organization_database_engine(self, org_id: str):
        """Get SQLAlchemy engine for an organization's database."""
        db_url = self.get_organization_database_url(org_id)
        return create_engine(db_url, echo=settings.SQL_ECHO)
    
    def get_organization_database_session(self, org_id: str):
        """Get database session for an organization's database."""
        engine = self.get_organization_database_engine(org_id)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    
    async def delete_organization_database(self, org_id: str) -> bool:
        """
        Delete an organization's database (use with extreme caution).
        
        Args:
            org_id: Organization ID
            
        Returns:
            bool: True if database was deleted successfully
        """
        db_name = self.get_organization_database_name(org_id)
        
        try:
            connection = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
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
            logger.warning(f"Deleted organization database: {db_name}")
            
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete organization database {db_name}: {e}")
            return False
    
    async def backup_organization_database(self, org_id: str, backup_path: str) -> bool:
        """
        Create a backup of organization's database.
        
        Args:
            org_id: Organization ID
            backup_path: Path where to store the backup
            
        Returns:
            bool: True if backup was created successfully
        """
        db_name = self.get_organization_database_name(org_id)
        
        try:
            import subprocess
            import os
            
            # Ensure backup directory exists
            backup_dir = os.path.dirname(backup_path)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Run pg_dump
            cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", self.db_port,
                "-U", self.db_user,
                "-d", db_name,
                "-f", backup_path,
                "--verbose"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully backed up organization database {db_name} to {backup_path}")
                return True
            else:
                logger.error(f"Backup failed for {db_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to backup organization database {db_name}: {e}")
            return False
    
    async def get_organization_database_info(self, org_id: str) -> Dict[str, Any]:
        """
        Get information about an organization's database.
        
        Args:
            org_id: Organization ID
            
        Returns:
            Dict with database information
        """
        db_name = self.get_organization_database_name(org_id)
        
        try:
            engine = self.get_organization_database_engine(org_id)
            
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
                
                # Get user count in this organization database
                users_result = conn.execute(text("""
                    SELECT COUNT(*) as user_count
                    FROM users
                """))
                users_row = users_result.fetchone()
                user_count = users_row[0] if users_row else 0
                
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
                "organization_id": org_id,
                "size": size,
                "table_count": table_count,
                "user_count": user_count,
                "active_connections": connections,
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Failed to get database info for organization {org_id}: {e}")
            return {
                "database_name": db_name,
                "organization_id": org_id,
                "status": "error",
                "error": str(e)
            }
    
    async def list_organization_databases(self) -> List[Dict[str, Any]]:
        """
        List all organization databases.
        
        Returns:
            List of database information dictionaries
        """
        try:
            connection = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database="postgres"
            )
            
            cursor = connection.cursor()
            
            # Get all databases that match organization pattern
            cursor.execute("""
                SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
                FROM pg_database
                WHERE datname LIKE 'sonicus_org_%'
                ORDER BY datname
            """)
            
            databases = []
            for row in cursor.fetchall():
                db_name, size = row
                # Extract org_id from database name
                org_id = db_name.replace('sonicus_org_', '').replace('_', '-')
                
                databases.append({
                    "database_name": db_name,
                    "organization_id": org_id,
                    "size": size,
                    "status": "active"
                })
            
            cursor.close()
            connection.close()
            
            logger.info(f"Found {len(databases)} organization databases")
            return databases
            
        except Exception as e:
            logger.error(f"Failed to list organization databases: {e}")
            return []
    
    async def health_check_all_organization_databases(self) -> Dict[str, Any]:
        """
        Perform health check on all organization databases.
        
        Returns:
            Dict with health check results
        """
        try:
            databases = await self.list_organization_databases()
            health_results = {
                "total_databases": len(databases),
                "healthy_databases": 0,
                "unhealthy_databases": 0,
                "database_details": []
            }
            
            for db_info in databases:
                org_id = db_info["organization_id"]
                try:
                    detailed_info = await self.get_organization_database_info(org_id)
                    if detailed_info["status"] == "healthy":
                        health_results["healthy_databases"] += 1
                    else:
                        health_results["unhealthy_databases"] += 1
                    
                    health_results["database_details"].append(detailed_info)
                    
                except Exception as e:
                    health_results["unhealthy_databases"] += 1
                    health_results["database_details"].append({
                        "organization_id": org_id,
                        "database_name": db_info["database_name"],
                        "status": "error",
                        "error": str(e)
                    })
            
            logger.info(f"Health check completed: {health_results['healthy_databases']}/{health_results['total_databases']} healthy")
            return health_results
            
        except Exception as e:
            logger.error(f"Failed to perform health check: {e}")
            return {
                "total_databases": 0,
                "healthy_databases": 0,
                "unhealthy_databases": 0,
                "database_details": [],
                "error": str(e)
            }
    
    async def _mark_organization_database_created(self, organization: Organization) -> None:
        """Mark organization's database as created in the master database."""
        try:
            from sqlalchemy.orm import sessionmaker
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.master_engine)
            
            with SessionLocal() as db:
                # Find organization by ID and update
                org_id = organization.id
                master_org = db.query(Organization).filter(Organization.id == org_id).first()
                if master_org:
                    # Add database_created fields if they exist
                    if hasattr(master_org, 'database_created'):
                        setattr(master_org, 'database_created', True)
                    if hasattr(master_org, 'database_created_at'):
                        setattr(master_org, 'database_created_at', datetime.now())
                    db.commit()
                    logger.info(f"Marked database as created for organization: {organization.name}")
                        
        except Exception as e:
            logger.error(f"Failed to mark database as created for organization: {e}")
            # Don't raise exception as this is not critical

# Global instance
organization_db_service = OrganizationDatabaseService()
