"""
Enhanced database session manager for B2B2C architecture.
Routes database connections based on organization context.
"""

import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.services.organization_db_service import organization_db_service
from app.services.multi_tenant_db_service import multi_tenant_db_service
from app.db.session import SessionLocal as MasterSessionLocal

logger = logging.getLogger(__name__)

class B2B2CSessionManager:
    """Enhanced session manager for B2B2C multi-tenant architecture."""
    
    def __init__(self):
        self._org_engines = {}  # Cache for organization database engines
        self._user_engines = {}  # Cache for user database engines (legacy support)
    
    def get_master_session(self) -> Session:
        """Get a session to the master database."""
        return MasterSessionLocal()
    
    def get_organization_session(self, org_id: str) -> Session:
        """
        Get a database session for a specific organization.
        
        Args:
            org_id: Organization ID
            
        Returns:
            SQLAlchemy session for the organization's database
        """
        try:
            # Check if we have a cached engine for this organization
            if org_id not in self._org_engines:
                engine = organization_db_service.get_organization_database_engine(org_id)
                self._org_engines[org_id] = engine
                logger.debug(f"Created new engine for organization {org_id}")
            
            engine = self._org_engines[org_id]
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            return SessionLocal()
            
        except Exception as e:
            logger.error(f"Failed to get organization session for {org_id}: {e}")
            raise
    
    def get_user_session_legacy(self, firebase_uid: str) -> Session:
        """
        Get a database session for a specific user (legacy support).
        
        Args:
            firebase_uid: User's Firebase UID
            
        Returns:
            SQLAlchemy session for the user's database
        """
        try:
            # Check if we have a cached engine for this user
            if firebase_uid not in self._user_engines:
                # Convert firebase_uid to user_id by querying master database
                with self.get_master_session() as master_db:
                    user = master_db.query(User).filter(getattr(User, 'firebase_uid') == firebase_uid).first()
                    if not user:
                        raise Exception(f"User with firebase_uid {firebase_uid} not found")
                    user_id = getattr(user, 'id')
                
                engine = multi_tenant_db_service.get_user_database_engine(user_id)
                self._user_engines[firebase_uid] = engine
                logger.debug(f"Created new engine for user {firebase_uid} (user_id: {user_id})")
            
            engine = self._user_engines[firebase_uid]
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            return SessionLocal()
            
        except Exception as e:
            logger.error(f"Failed to get user session for {firebase_uid}: {e}")
            raise
    
    async def get_session_for_user(self, user: User) -> Session:
        """
        Get the appropriate database session for a user based on B2B2C context.
        
        Args:
            user: User object with organization context
            
        Returns:
            SQLAlchemy session (either organization or user-specific)
        """
        try:
            # Get user attributes safely
            user_role = getattr(user, 'role', None)
            user_org_id = getattr(user, 'organization_id', None)
            user_firebase_uid = getattr(user, 'firebase_uid', None)
            user_email = getattr(user, 'email', 'unknown')
            
            # Super admins always use master database
            if user_role == UserRole.SUPER_ADMIN:
                logger.debug(f"Super admin {user_email} using master database")
                return self.get_master_session()
            
            # Organization users use organization database
            if user_org_id:
                org_id = str(user_org_id)
                logger.debug(f"User {user_email} using organization database: {org_id}")
                return self.get_organization_session(org_id)
            
            # Fallback to user-specific database for legacy support
            if user_firebase_uid:
                logger.debug(f"User {user_email} using legacy user database: {user_firebase_uid}")
                return self.get_user_session_legacy(user_firebase_uid)
            
            # Last resort: master database
            logger.warning(f"User {user_email} has no organization or firebase_uid, using master database")
            return self.get_master_session()
            
        except Exception as e:
            logger.error(f"Failed to get session for user: {e}")
            raise
    
    async def get_session_for_organization(self, org_id: str, ensure_exists: bool = True) -> Session:
        """
        Get database session for an organization, optionally creating the database.
        
        Args:
            org_id: Organization ID
            ensure_exists: If True, create the organization database if it doesn't exist
            
        Returns:
            SQLAlchemy session for the organization's database
        """
        try:
            if ensure_exists:
                # Check if organization database exists, create if needed
                with self.get_master_session() as master_db:
                    org = master_db.query(Organization).filter(Organization.id == org_id).first()
                    if org and not getattr(org, 'database_created', False):
                        logger.info(f"Creating database for organization {org.name}")
                        success = await organization_db_service.create_organization_database(org)
                        if not success:
                            raise Exception(f"Failed to create database for organization {org_id}")
            
            return self.get_organization_session(org_id)
            
        except Exception as e:
            logger.error(f"Failed to get session for organization {org_id}: {e}")
            raise
    
    @asynccontextmanager
    async def get_contextual_session(self, user: User) -> AsyncGenerator[Session, None]:
        """
        Context manager for getting the appropriate database session for a user.
        
        Args:
            user: User object with organization context
            
        Yields:
            SQLAlchemy session
        """
        session = None
        try:
            session = await self.get_session_for_user(user)
            yield session
        finally:
            if session:
                session.close()
    
    @asynccontextmanager
    async def get_organization_context(self, org_id: str, ensure_exists: bool = True) -> AsyncGenerator[Session, None]:
        """
        Context manager for organization database sessions.
        
        Args:
            org_id: Organization ID
            ensure_exists: If True, create the organization database if it doesn't exist
            
        Yields:
            SQLAlchemy session for the organization's database
        """
        session = None
        try:
            session = await self.get_session_for_organization(org_id, ensure_exists)
            yield session
        finally:
            if session:
                session.close()
    
    def clear_engine_cache(self, org_id: Optional[str] = None, firebase_uid: Optional[str] = None):
        """
        Clear cached engines for organizations or users.
        
        Args:
            org_id: If provided, clear cache for this organization
            firebase_uid: If provided, clear cache for this user
        """
        if org_id and org_id in self._org_engines:
            engine = self._org_engines.pop(org_id)
            engine.dispose()
            logger.debug(f"Cleared engine cache for organization {org_id}")
        
        if firebase_uid and firebase_uid in self._user_engines:
            engine = self._user_engines.pop(firebase_uid)
            engine.dispose()
            logger.debug(f"Cleared engine cache for user {firebase_uid}")
        
        if not org_id and not firebase_uid:
            # Clear all caches
            for engine in self._org_engines.values():
                engine.dispose()
            for engine in self._user_engines.values():
                engine.dispose()
            self._org_engines.clear()
            self._user_engines.clear()
            logger.debug("Cleared all engine caches")
    
    def get_database_routing_info(self, user: User) -> dict:
        """
        Get information about which database would be used for a user.
        
        Args:
            user: User object
            
        Returns:
            Dict with routing information
        """
        routing_info = {
            "user_email": getattr(user, 'email', 'unknown'),
            "user_role": "unknown",
            "database_type": "unknown",
            "database_identifier": None,
            "routing_reason": "unknown"
        }
        
        try:
            # Get user attributes safely
            user_role = getattr(user, 'role', None)
            user_org_id = getattr(user, 'organization_id', None)
            user_firebase_uid = getattr(user, 'firebase_uid', None)
            
            # Set role string
            if user_role:
                routing_info["user_role"] = user_role.value if hasattr(user_role, 'value') else str(user_role)
            
            if user_role == UserRole.SUPER_ADMIN:
                routing_info.update({
                    "database_type": "master",
                    "database_identifier": "master",
                    "routing_reason": "super_admin_access"
                })
            elif user_org_id:
                routing_info.update({
                    "database_type": "organization",
                    "database_identifier": str(user_org_id),
                    "routing_reason": "organization_member"
                })
            elif user_firebase_uid:
                routing_info.update({
                    "database_type": "user_legacy",
                    "database_identifier": user_firebase_uid,
                    "routing_reason": "legacy_user_database"
                })
            else:
                routing_info.update({
                    "database_type": "master",
                    "database_identifier": "master",
                    "routing_reason": "fallback_no_context"
                })
                
        except Exception as e:
            routing_info["error"] = str(e)
        
        return routing_info

# Import authentication dependencies
from app.core.auth_dependencies import get_current_user_compatible

# Global session manager instance
b2b2c_session_manager = B2B2CSessionManager()

# Dependency function for FastAPI
async def get_contextual_db_session(current_user: User = Depends(get_current_user_compatible)):
    """
    FastAPI dependency to get the appropriate database session for the current user.
    
    Args:
        current_user: Current authenticated user from Authentik OIDC
        
    Yields:
        Database session appropriate for the user's context
    """
    async with b2b2c_session_manager.get_contextual_session(current_user) as session:
        yield session

# Convenience functions for backward compatibility
def get_db_for_user(user: User) -> Session:
    """Synchronous version - get database session for a user."""
    import asyncio
    return asyncio.run(b2b2c_session_manager.get_session_for_user(user))

def get_db_for_organization(org_id: str) -> Session:
    """Synchronous version - get database session for an organization."""
    return b2b2c_session_manager.get_organization_session(org_id)
