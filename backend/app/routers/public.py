"""
Public routes that don't require authentication
Used for platform mode detection and public information
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.organization import Organization
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/platform/organization-count")
async def get_organization_count(db: Session = Depends(get_db)):
    """
    Get the count of organizations in the platform.
    Used to determine if the platform should operate in B2B2C or B2C mode.
    """
    try:
        count = db.query(func.count(Organization.id)).scalar() or 0
        return {"count": count}
    except Exception as e:
        logger.error(f"Failed to get organization count: {e}")
        # Return 1 to default to B2B2C mode if there's an error
        return {"count": 1}
