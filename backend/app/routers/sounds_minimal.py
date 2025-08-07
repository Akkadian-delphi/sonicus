"""
Minimal Sounds Router - FastAPI Compatibility Test

This is a minimal version to test if we can get FastAPI working by completely
avoiding all complex authentication dependencies and SQLAlchemy User models.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.therapy_sound import TherapySound
from app.schemas.therapy_sound import SoundReadSchema
from typing import List, Optional
import logging

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/sounds", response_model=List[SoundReadSchema])
async def get_sounds_minimal(
    skip: int = Query(0, description="Skip items (for pagination)"),
    limit: int = Query(100, le=100, description="Limit items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """
    Minimal sounds endpoint without authentication dependencies.
    This tests if the FastAPI issue is in our auth system or elsewhere.
    """
    try:
        # Build base query
        query = db.query(TherapySound)
        
        # Apply category filter if provided
        if category:
            query = query.filter(TherapySound.category == category)
        
        # Apply pagination
        sounds = query.offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(sounds)} sounds (minimal endpoint)")
        return sounds
        
    except Exception as e:
        logger.error(f"Error getting sounds: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check_minimal():
    """
    Minimal health check without any dependencies.
    """
    return {"status": "healthy", "message": "Minimal sounds router working"}
