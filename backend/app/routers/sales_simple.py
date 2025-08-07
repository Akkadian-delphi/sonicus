"""
Simple Sales API Router  
Temporary working router for sales endpoints while fixing the main one
"""

from fastapi import APIRouter
from typing import Dict, Any, List

router = APIRouter()

@router.get("/sales/health")
def sales_health():
    """Health check for sales service"""
    return {"status": "Sales service is running", "service": "sales"}

@router.get("/sales/info")
def sales_info():
    """Get information about the sales service"""
    return {
        "service": "sales",
        "description": "Subscription and invoice management for premium content",
        "endpoints": [
            "GET /sales/health - Health check",
            "GET /sales/info - Service information",
            "GET /sales/subscriptions - List subscriptions (coming soon)",
            "POST /sales/subscribe - Create subscription (coming soon)",
            "GET /sales/invoices - List invoices (coming soon)"
        ],
        "status": "Active"
    }

@router.get("/sales/subscriptions")
def get_subscriptions():
    """Get user subscriptions"""
    return {
        "message": "Subscriptions endpoint is being updated",
        "status": "coming_soon",
        "subscriptions": [
            {
                "id": 1,
                "plan": "Premium",
                "status": "active",
                "price": "$9.99/month",
                "features": ["Unlimited sounds", "Offline access", "Premium content"]
            },
            {
                "id": 2,
                "plan": "Basic", 
                "status": "trial",
                "price": "Free trial",
                "features": ["Limited sounds", "Online only"]
            }
        ]
    }

@router.post("/sales/subscribe")
def create_subscription():
    """Create a new subscription"""
    return {
        "message": "Subscription creation endpoint is being updated",
        "status": "coming_soon",
        "action": "subscribe_requested"
    }

@router.get("/sales/invoices")
def get_invoices():
    """Get user invoices"""
    return {
        "message": "Invoices endpoint is being updated", 
        "status": "coming_soon",
        "invoices": [
            {
                "id": 1,
                "date": "2025-08-01",
                "amount": "$9.99",
                "status": "paid",
                "plan": "Premium"
            },
            {
                "id": 2,
                "date": "2025-07-01", 
                "amount": "$9.99",
                "status": "paid",
                "plan": "Premium"
            }
        ]
    }

@router.get("/sales/plans")
def get_plans():
    """Get available subscription plans"""
    return {
        "plans": [
            {
                "id": "basic",
                "name": "Basic",
                "price": "Free",
                "features": ["5 sounds per day", "Basic categories"],
                "popular": False
            },
            {
                "id": "premium", 
                "name": "Premium",
                "price": "$9.99/month",
                "features": ["Unlimited sounds", "All categories", "Offline access", "Premium sounds"],
                "popular": True
            },
            {
                "id": "enterprise",
                "name": "Enterprise", 
                "price": "Contact us",
                "features": ["Everything in Premium", "Multi-user access", "Analytics", "Custom sounds"],
                "popular": False
            }
        ]
    }
