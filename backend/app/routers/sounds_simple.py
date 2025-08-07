"""
Simple Sounds API Router
Temporary working router for sounds endpoints while fixing the main one
"""

from fastapi import APIRouter
from typing import Dict, Any, List

router = APIRouter()

@router.get("/sounds/health")
def sounds_health():
    """Health check for sounds service"""
    return {"status": "Sounds service is running", "service": "sounds"}

@router.get("/sounds/info")
def sounds_info():
    """Get information about the sounds service"""
    return {
        "service": "sounds",
        "description": "Browse and stream therapeutic sound content",
        "endpoints": [
            "GET /sounds/health - Health check",
            "GET /sounds/info - Service information", 
            "GET /sounds/catalog - Browse sound catalog (coming soon)",
            "GET /sounds/{sound_id} - Get specific sound (coming soon)",
            "POST /sounds/{sound_id}/play - Play sound (coming soon)"
        ],
        "status": "Active"
    }

@router.get("/sounds/catalog")
def get_sounds_catalog():
    """Get therapeutic sounds catalog"""
    return {
        "message": "Sounds catalog endpoint is being updated",
        "status": "coming_soon",
        "catalog": [
            {
                "id": 1,
                "name": "Ocean Waves",
                "category": "Nature",
                "duration": "10:00",
                "description": "Calming ocean waves for relaxation"
            },
            {
                "id": 2, 
                "name": "Forest Birds",
                "category": "Nature",
                "duration": "15:00",
                "description": "Peaceful forest birds chirping"
            },
            {
                "id": 3,
                "name": "Rain Sounds",
                "category": "Weather", 
                "duration": "12:00",
                "description": "Gentle rain for sleep and focus"
            }
        ]
    }

@router.get("/sounds/{sound_id}")
def get_sound_details(sound_id: int):
    """Get details for a specific sound"""
    return {
        "id": sound_id,
        "message": "Sound details endpoint is being updated",
        "status": "coming_soon",
        "sound": {
            "id": sound_id,
            "name": f"Sound {sound_id}",
            "status": "available"
        }
    }

@router.post("/sounds/{sound_id}/play")
def play_sound(sound_id: int):
    """Play a therapeutic sound"""
    return {
        "message": f"Playing sound {sound_id}",
        "status": "coming_soon",
        "sound_id": sound_id,
        "action": "play_requested"
    }
