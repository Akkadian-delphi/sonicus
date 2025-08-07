"""
Migration Schemas for B2B2C to B2C Migration

Pydantic schemas for migration API responses.
"""

from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime


class MigrationStatusResponse(BaseModel):
    """Response model for migration status."""
    migration_complete: bool
    tables_created: Dict[str, bool]
    total_users: int
    migrated_users: int
    organization_dependent_tables: List[str]
    last_updated: datetime


class MigrationStepResponse(BaseModel):
    """Response model for individual migration step."""
    step: str
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class UserMigrationSummary(BaseModel):
    """Summary of user migration status."""
    user_id: int
    email: str
    subscription_tier: Optional[str]
    subscription_status: Optional[str]
    has_organization: bool
    has_b2c_subscription: bool
    created_at: datetime
