"""
Webhook Management API endpoints for testing and configuration.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl

from app.core.auth_middleware import require_super_admin
from app.db.session import get_db
from app.services.webhook_service import webhook_service, WebhookEventType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


class WebhookEndpointCreate(BaseModel):
    url: HttpUrl
    events: List[str] = ["organization.created"]
    organization_id: Optional[str] = None
    secret_key: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    timeout_seconds: int = 10
    max_retries: int = 3


class WebhookTestRequest(BaseModel):
    url: HttpUrl
    test_data: Optional[dict] = None


class WebhookTestResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


@router.post("/endpoints")
@require_super_admin
async def create_webhook_endpoint(
    request: WebhookEndpointCreate,
    db: Session = Depends(get_db)
):
    """Create a new webhook endpoint"""
    try:
        # Convert string events to WebhookEventType enums
        event_types = []
        for event_str in request.events:
            try:
                event_types.append(WebhookEventType(event_str))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type: {event_str}. Valid types: {[e.value for e in WebhookEventType]}"
                )
        
        endpoint = await webhook_service.register_webhook_endpoint(
            url=str(request.url),
            events=event_types,
            db=db,
            organization_id=request.organization_id,
            secret_key=request.secret_key,
            name=request.name,
            description=request.description,
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries
        )
        
        return {
            "id": str(endpoint.id),
            "url": endpoint.url,
            "message": "Webhook endpoint created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create webhook endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create webhook endpoint"
        )


@router.post("/test", response_model=WebhookTestResponse)
@require_super_admin
async def test_webhook_endpoint(
    request: WebhookTestRequest,
    db: Session = Depends(get_db)
):
    """Test a webhook endpoint by sending a test payload"""
    import httpx
    import time
    
    try:
        test_payload = request.test_data or {
            "event_type": "test.webhook",
            "timestamp": "2025-08-07T12:00:00Z",
            "data": {"message": "This is a test webhook"}
        }
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                str(request.url),
                json=test_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Sonicus-Webhooks-Test/1.0"
                }
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return WebhookTestResponse(
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                response_time_ms=round(response_time, 2),
                error_message=None if 200 <= response.status_code < 300 else f"HTTP {response.status_code}: {response.text[:200]}"
            )
            
    except httpx.TimeoutException:
        return WebhookTestResponse(
            success=False,
            status_code=None,
            response_time_ms=None,
            error_message="Request timeout"
        )
    except httpx.RequestError as e:
        return WebhookTestResponse(
            success=False,
            status_code=None,
            response_time_ms=None,
            error_message=f"Request error: {str(e)}"
        )
    except Exception as e:
        return WebhookTestResponse(
            success=False,
            status_code=None,
            response_time_ms=None,
            error_message=f"Unexpected error: {str(e)}"
        )


@router.post("/trigger-test")
@require_super_admin  
async def trigger_test_webhook(
    db: Session = Depends(get_db)
):
    """Trigger a test organization creation webhook to all registered endpoints"""
    try:
        # Create test organization data
        test_org_data = {
            "id": "test-org-12345",
            "name": "Test Organization",
            "display_name": "Test Organization Inc.",
            "domain": "test.com",
            "primary_contact_email": "admin@test.com",
            "subscription_tier": "premium",
            "subscription_status": "active", 
            "max_users": 100,
            "industry": "Technology",
            "company_size": "50-100",
            "created_at": "2025-08-07T12:00:00Z",
            "trial_end_date": None
        }
        
        # Send test webhook
        await webhook_service.send_organization_created_webhook(test_org_data, db)
        
        return {
            "message": "Test webhook triggered successfully",
            "test_organization_id": "test-org-12345"
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger test webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger test webhook: {str(e)}"
        )
