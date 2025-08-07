from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.b2b2c_session import get_contextual_db_session
from app.models.subscription import Subscription
from app.models.therapy_sound import TherapySound
from app.schemas.therapy_sound import SoundReadSchema
from app.models.user import User
from typing import List, Optional
import os
import logging
import json

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/sounds", response_model=List[SoundReadSchema])
async def get_sounds(
    request: Request,
    response: Response,
    skip: int = Query(0, description="Skip items (for pagination)"),
    limit: int = Query(100, le=100, description="Limit items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    q: Optional[str] = Query(None, description="Search in title and description"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_contextual_db_session)
):
    """
    List available therapeutic sounds for the user's organization.
    """
    try:
        query = db.query(TherapySound)
        
        # Apply filters
        if category:
            query = query.filter(TherapySound.category == category)
        
        if q:
            search_pattern = f"%{q}%"
            query = query.filter(
                (TherapySound.title.ilike(search_pattern)) |
                (TherapySound.description.ilike(search_pattern))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        sounds = query.offset(skip).limit(limit).all()
        
        # Convert to schema
        result = [SoundReadSchema.from_orm(sound) for sound in sounds]
        
        response.headers["X-Total-Count"] = str(total)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting sounds: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sounds/categories")
async def get_sound_categories(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_contextual_db_session)
):
    """
    Get available sound categories for the user's organization.
    """
    try:
        # Get unique categories from database
        categories = db.query(TherapySound.category).distinct().all()
        result = [cat[0] for cat in categories if cat[0]]
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting sound categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sounds/{sound_id}", response_model=SoundReadSchema)
async def get_sound(
    sound_id: int,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_contextual_db_session)
):
    """
    Get a specific therapeutic sound by ID from the user's organization.
    """
    try:
        sound = db.query(TherapySound).filter(TherapySound.id == sound_id).first()
        
        if not sound:
            raise HTTPException(status_code=404, detail="Sound not found")
        
        # Convert to schema
        result = SoundReadSchema.from_orm(sound)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sound {sound_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sounds/{sound_id}/stream")
async def stream_sound(
    sound_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_contextual_db_session)
):
    """
    Stream a therapeutic sound file from the user's organization.
    """
    try:
        # Get the sound from database
        sound = db.query(TherapySound).filter(TherapySound.id == sound_id).first()
        
        if not sound:
            raise HTTPException(status_code=404, detail="Sound not found")
        
        # Check if file exists
        if not sound.file_path or not os.path.exists(sound.file_path):
            raise HTTPException(status_code=404, detail="Sound file not found")
        
        # Determine content type based on file extension
        file_extension = os.path.splitext(sound.file_path)[1].lower()
        content_type_map = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac'
        }
        content_type = content_type_map.get(file_extension, 'audio/mpeg')
        
        # Create file streaming response
        def iterfile():
            with open(sound.file_path, mode="rb") as file_like:
                yield from file_like
        
        return StreamingResponse(
            iterfile(),
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={sound.title}.{file_extension[1:]}",
                "Accept-Ranges": "bytes"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming sound {sound_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
