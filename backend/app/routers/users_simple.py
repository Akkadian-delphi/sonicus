"""
Simple Users API Router
Temporary working router for users endpoints while fixing the main one
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

router = APIRouter()

@router.get("/users/health")
def users_health():
    """Health check for users service"""
    return {"status": "Users service is running", "service": "users"}

@router.get("/users/info")
def users_info():
    """Get information about the users service"""
    return {
        "service": "users",
        "description": "User registration, authentication, and profile management",
        "endpoints": [
            "GET /users/health - Health check",
            "GET /users/info - Service information", 
            "GET /users/profile - Get user profile (coming soon)",
            "PUT /users/profile - Update user profile (coming soon)"
        ],
        "status": "Active"
    }

# Authentication endpoints moved to /api/v1/auth/ to avoid duplication
# Users router focuses on profile management only

@router.get("/users/profile")
def get_profile_placeholder():
    """Placeholder for user profile"""
    return {
        "message": "User profile endpoint is being updated",
        "status": "coming_soon",
        "use_instead": "/api/v1/auth/user-info"
    }

@router.put("/users/profile")
def update_profile_placeholder():
    """Placeholder for updating user profile"""
    return {
        "message": "User profile update endpoint is being updated",
        "status": "coming_soon",
        "description": "Update user profile information"
    }
