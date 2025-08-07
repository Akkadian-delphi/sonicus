"""
Webhook Service for Sonicus

Handles sending webhooks for various events like organization creation,
user registration, subscription changes, etc.
"""

import httpx
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import asyncio
from enum import Enum

from app.db.base import Base

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_SUSPENDED = "organization.suspended"
    ORGANIZATION_REACTIVATED = "organization.reactivated"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    SUBSCRIPTION_CHANGED = "subscription.changed"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"


class WebhookStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookEndpoint(Base):
    """Model for storing webhook endpoint configurations"""
    __tablename__ = "webhook_endpoints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(500), nullable=False)
    secret_key = Column(String(255), nullable=True)  # For webhook signature verification
    
    # Event filtering
    events = Column(Text, nullable=False)  # JSON array of event types to send
    is_active = Column(Boolean, default=True)
    
    # Organization-specific webhooks (None = global)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Configuration
    timeout_seconds = Column(Integer, default=10)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<WebhookEndpoint(id={self.id}, url='{self.url}', active={self.is_active})>"


class WebhookDelivery(Base):
    """Model for tracking webhook delivery attempts"""
    __tablename__ = "webhook_deliveries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Event details
    event_type = Column(String(100), nullable=False)
    event_id = Column(String(255), nullable=False)  # Unique identifier for this event
    payload = Column(Text, nullable=False)  # JSON payload sent
    
    # Delivery tracking
    status = Column(String(50), nullable=False, default=WebhookStatus.PENDING)
    http_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    response_headers = Column(Text, nullable=True)  # JSON
    error_message = Column(Text, nullable=True)
    
    # Retry logic
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, event='{self.event_type}', status='{self.status}')>"


class WebhookService:
    """Service for managing and sending webhooks"""
    
    def __init__(self):
        self.client_timeout = 10  # seconds
        self.max_retries = 3
    
    async def send_organization_created_webhook(
        self,
        organization_data: Dict[str, Any],
        db: Session
    ) -> None:
        """Send webhook for organization creation event"""
        event_data = {
            "event_type": WebhookEventType.ORGANIZATION_CREATED,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "organization": {
                    "id": str(organization_data["id"]),
                    "name": organization_data["name"],
                    "display_name": organization_data.get("display_name"),
                    "domain": organization_data.get("domain"),
                    "primary_contact_email": organization_data["primary_contact_email"],
                    "subscription_tier": organization_data.get("subscription_tier"),
                    "subscription_status": organization_data.get("subscription_status"),
                    "max_users": organization_data.get("max_users"),
                    "industry": organization_data.get("industry"),
                    "company_size": organization_data.get("company_size"),
                    "created_at": organization_data.get("created_at"),
                    "trial_end_date": organization_data.get("trial_end_date")
                }
            }
        }
        
        await self._send_webhooks(
            event_type=WebhookEventType.ORGANIZATION_CREATED,
            event_data=event_data,
            organization_id=organization_data["id"],
            db=db
        )
    
    async def send_organization_updated_webhook(
        self,
        organization_data: Dict[str, Any],
        changes: Dict[str, Any],
        db: Session
    ) -> None:
        """Send webhook for organization update event"""
        event_data = {
            "event_type": WebhookEventType.ORGANIZATION_UPDATED,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "organization": organization_data,
                "changes": changes
            }
        }
        
        await self._send_webhooks(
            event_type=WebhookEventType.ORGANIZATION_UPDATED,
            event_data=event_data,
            organization_id=organization_data["id"],
            db=db
        )
    
    async def _send_webhooks(
        self,
        event_type: WebhookEventType,
        event_data: Dict[str, Any],
        organization_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> None:
        """Send webhooks to all registered endpoints for this event type"""
        if db is None:
            logger.error("Database session is required for webhook sending")
            return
            
        try:
            # Get all active webhook endpoints that want this event type
            endpoints = self._get_webhook_endpoints(
                event_type=event_type,
                organization_id=organization_id,
                db=db
            )
            
            if not endpoints:
                logger.info(f"No webhook endpoints configured for event: {event_type}")
                return
            
            # Send webhooks in parallel
            tasks = []
            for endpoint in endpoints:
                task = self._send_single_webhook(endpoint, event_data, db)
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Error sending webhooks for event {event_type}: {e}")
    
    def _get_webhook_endpoints(
        self,
        event_type: WebhookEventType,
        organization_id: Optional[str],
        db: Session
    ) -> List[WebhookEndpoint]:
        """Get all webhook endpoints that should receive this event"""
        try:
            query = db.query(WebhookEndpoint).filter(
                WebhookEndpoint.is_active == True
            )
            
            # Filter by organization (include global webhooks too)
            if organization_id:
                query = query.filter(
                    (WebhookEndpoint.organization_id == organization_id) |
                    (WebhookEndpoint.organization_id.is_(None))
                )
            else:
                query = query.filter(WebhookEndpoint.organization_id.is_(None))
            
            endpoints = query.all()
            
            # Filter by event type
            filtered_endpoints = []
            for endpoint in endpoints:
                try:
                    events = json.loads(getattr(endpoint, 'events'))
                    if event_type.value in events:
                        filtered_endpoints.append(endpoint)
                except (json.JSONDecodeError, AttributeError):
                    logger.warning(f"Invalid events configuration for webhook endpoint {getattr(endpoint, 'id')}")
                    continue
            
            return filtered_endpoints
            
        except Exception as e:
            logger.error(f"Error querying webhook endpoints: {e}")
            return []
    
    async def _send_single_webhook(
        self,
        endpoint: WebhookEndpoint,
        event_data: Dict[str, Any],
        db: Session
    ) -> None:
        """Send webhook to a single endpoint"""
        delivery_record = None
        try:
            # Create delivery record
            delivery_record = WebhookDelivery(
                id=uuid.uuid4(),
                endpoint_id=getattr(endpoint, 'id'),
                event_type=event_data["event_type"],
                event_id=event_data["event_id"],
                payload=json.dumps(event_data),
                status=WebhookStatus.PENDING,
                max_attempts=getattr(endpoint, 'max_retries') or self.max_retries
            )
            db.add(delivery_record)
            db.commit()
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Sonicus-Webhooks/1.0",
                "X-Sonicus-Event": event_data["event_type"],
                "X-Sonicus-Event-ID": event_data["event_id"],
                "X-Sonicus-Timestamp": event_data["timestamp"]
            }
            
            # Add signature if secret key is configured
            endpoint_secret_key = getattr(endpoint, 'secret_key')
            if endpoint_secret_key:
                signature = self._generate_signature(
                    json.dumps(event_data),
                    endpoint_secret_key
                )
                headers["X-Sonicus-Signature"] = signature
            
            # Send webhook
            timeout = getattr(endpoint, 'timeout_seconds') or self.client_timeout
            async with httpx.AsyncClient(timeout=timeout) as client:
                setattr(delivery_record, 'attempt_count', getattr(delivery_record, 'attempt_count', 0) + 1)
                setattr(delivery_record, 'last_attempt_at', datetime.utcnow())
                
                response = await client.post(
                    getattr(endpoint, 'url'),
                    json=event_data,
                    headers=headers
                )
                
                # Update delivery record
                setattr(delivery_record, 'http_status_code', response.status_code)
                setattr(delivery_record, 'response_body', response.text[:1000])  # Limit size
                setattr(delivery_record, 'response_headers', json.dumps(dict(response.headers))[:1000])
                
                if 200 <= response.status_code < 300:
                    setattr(delivery_record, 'status', WebhookStatus.SENT)
                    setattr(delivery_record, 'delivered_at', datetime.utcnow())
                    
                    # Update endpoint last success
                    setattr(endpoint, 'last_success_at', datetime.utcnow())
                    
                    logger.info(f"Webhook sent successfully to {getattr(endpoint, 'url')} for event {event_data['event_type']}")
                else:
                    setattr(delivery_record, 'status', WebhookStatus.FAILED)
                    setattr(delivery_record, 'error_message', f"HTTP {response.status_code}: {response.text[:500]}")
                    
                    # Update endpoint last failure
                    setattr(endpoint, 'last_failure_at', datetime.utcnow())
                    
                    logger.warning(f"Webhook failed to {getattr(endpoint, 'url')}: HTTP {response.status_code}")
                
                db.commit()
                
        except httpx.TimeoutException:
            if delivery_record:
                setattr(delivery_record, 'status', WebhookStatus.FAILED)
                setattr(delivery_record, 'error_message', "Request timeout")
                setattr(endpoint, 'last_failure_at', datetime.utcnow())
                db.commit()
            logger.error(f"Webhook timeout to {getattr(endpoint, 'url')}")
            
        except httpx.RequestError as e:
            if delivery_record:
                setattr(delivery_record, 'status', WebhookStatus.FAILED)
                setattr(delivery_record, 'error_message', f"Request error: {str(e)[:500]}")
                setattr(endpoint, 'last_failure_at', datetime.utcnow())
                db.commit()
            logger.error(f"Webhook request error to {getattr(endpoint, 'url')}: {e}")
            
        except Exception as e:
            if delivery_record:
                setattr(delivery_record, 'status', WebhookStatus.FAILED)
                setattr(delivery_record, 'error_message', f"Unexpected error: {str(e)[:500]}")
                setattr(endpoint, 'last_failure_at', datetime.utcnow())
                db.commit()
            logger.error(f"Unexpected webhook error to {getattr(endpoint, 'url')}: {e}")
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook verification"""
        import hmac
        import hashlib
        
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    async def register_webhook_endpoint(
        self,
        url: str,
        events: List[WebhookEventType],
        db: Session,
        organization_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        timeout_seconds: int = 10,
        max_retries: int = 3
    ) -> WebhookEndpoint:
        """Register a new webhook endpoint"""
        try:
            endpoint = WebhookEndpoint(
                id=uuid.uuid4(),
                url=url,
                secret_key=secret_key,
                events=json.dumps([event.value for event in events]),
                organization_id=organization_id,
                name=name,
                description=description,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                is_active=True
            )
            
            db.add(endpoint)
            db.commit()
            db.refresh(endpoint)
            
            logger.info(f"Registered webhook endpoint: {url} for events: {[e.value for e in events]}")
            return endpoint
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to register webhook endpoint: {e}")
            raise


# Global webhook service instance
webhook_service = WebhookService()
