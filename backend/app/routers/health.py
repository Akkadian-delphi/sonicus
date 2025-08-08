"""
Simple Health Check Endpoint

This router provides a basic health check endpoint that can be used to verify
the backend service is running without requiring authentication.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging
from typing import Dict, Any

from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])

@router.get("/health")
async def basic_health_check():
    """
    Basic health check without authentication.
    Returns simple status to verify the service is running.
    """
    return {
        "status": "healthy",
        "service": "Sonicus Backend API",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Service is operational"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    More detailed health check with database connection test.
    Does not require authentication but tests core system components.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        db_message = "Database connection successful"
    except Exception as e:
        db_status = "unhealthy"
        db_message = f"Database connection failed: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    # Overall status
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "service": "Sonicus Backend API",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": {
                "status": db_status,
                "message": db_message
            },
            "authentication": {
                "status": "configured",
                "message": "OIDC and JWT authentication configured"
            }
        },
        "version": "1.0.0"
    }

@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for load balancers and monitoring.
    """
    return {"ping": "pong", "timestamp": datetime.utcnow().isoformat()}
