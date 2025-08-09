"""
Stripe Payment Service for payment processing and subscription management
Handles customer creation, subscription management, and payment processing
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class StripePaymentService:
    """Service for managing payments and subscriptions via Stripe API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        self.publishable_key = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', None)
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        self.enabled = getattr(settings, 'STRIPE_ENABLED', True)
        
        # Import stripe library if available
        try:
            import stripe
            self.stripe = stripe
            if self.api_key:
                stripe.api_key = self.api_key
        except ImportError:
            logger.error("Stripe library not installed. Install with: pip install stripe")
            self.enabled = False
            self.stripe = None
        
        if not self.api_key and self.enabled:
            logger.warning("Stripe API key not configured - payment processing disabled")
            self.enabled = False
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new customer in Stripe"""
        if not self.enabled:
            logger.info(f"Stripe disabled - would create customer: {customer_data.get('name')}")
            return {
                "id": f"cus_mock_{int(datetime.utcnow().timestamp())}",
                "name": customer_data.get("name"),
                "email": customer_data.get("email"),
                "object": "customer"
            }
        
        try:
            # Prepare customer payload for Stripe API
            stripe_customer_data = {
                "name": customer_data["name"],
                "email": customer_data["email"],
                "metadata": {
                    "organization_id": customer_data.get("organization_id", ""),
                    "business_type": customer_data.get("business_type", ""),
                    "source": "sonicus_platform"
                }
            }
            
            # Add address if provided
            if "address" in customer_data and customer_data["address"]:
                address = customer_data["address"]
                stripe_customer_data["address"] = {
                    "line1": address.get("line1", ""),
                    "line2": address.get("line2", ""),
                    "city": address.get("city", ""),
                    "state": address.get("state", ""),
                    "postal_code": address.get("postal_code", ""),
                    "country": address.get("country", "")
                }
            
            # Add phone if provided
            if customer_data.get("phone"):
                stripe_customer_data["phone"] = customer_data["phone"]
            
            customer = self.stripe.Customer.create(**stripe_customer_data)
            logger.info(f"Stripe customer created: {customer.id} for {customer_data['email']}")
            return customer
                
        except Exception as e:
            logger.error(f"Error creating Stripe customer: {e}")
            return None
    
    async def create_subscription(self, subscription_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a subscription for a customer"""
        if not self.enabled:
            logger.info(f"Stripe disabled - would create subscription: {subscription_data}")
            return {
                "id": f"sub_mock_{int(datetime.utcnow().timestamp())}",
                "customer": subscription_data.get("customer_id"),
                "status": "active",
                "object": "subscription",
                "current_period_start": int(datetime.utcnow().timestamp()),
                "current_period_end": int(datetime.utcnow().timestamp()) + 2592000  # 30 days
            }
        
        try:
            # Prepare subscription payload
            subscription_params = {
                "customer": subscription_data["customer_id"],
                "items": [{"price": subscription_data["price_id"]}],
                "metadata": subscription_data.get("metadata", {}),
            }
            
            # Add trial period if specified
            trial_days = subscription_data.get("trial_days")
            if trial_days and trial_days > 0:
                subscription_params["trial_period_days"] = trial_days
            
            # Add payment behavior settings
            subscription_params["payment_behavior"] = "default_incomplete"
            subscription_params["payment_settings"] = {
                "save_default_payment_method": "on_subscription"
            }
            subscription_params["expand"] = ["latest_invoice.payment_intent"]
            
            subscription = self.stripe.Subscription.create(**subscription_params)
            logger.info(f"Stripe subscription created: {subscription.id}")
            return subscription
                
        except Exception as e:
            logger.error(f"Error creating Stripe subscription: {e}")
            return None
    
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer details by ID"""
        if not self.enabled:
            return {
                "id": customer_id,
                "name": "Mock Customer",
                "email": "mock@example.com",
                "object": "customer"
            }
        
        try:
            customer = self.stripe.Customer.retrieve(customer_id)
            return customer
                
        except Exception as e:
            logger.error(f"Error getting Stripe customer {customer_id}: {e}")
            return None
    
    async def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details by ID"""
        if not self.enabled:
            return {
                "id": subscription_id,
                "status": "active",
                "object": "subscription",
                "current_period_start": int(datetime.utcnow().timestamp()),
                "current_period_end": int(datetime.utcnow().timestamp()) + 2592000
            }
        
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            return subscription
                
        except Exception as e:
            logger.error(f"Error getting Stripe subscription {subscription_id}: {e}")
            return None
    
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        if not self.enabled:
            logger.info(f"Stripe disabled - would cancel subscription: {subscription_id}")
            return True
        
        try:
            subscription = self.stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            logger.info(f"Stripe subscription cancelled: {subscription_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error cancelling Stripe subscription {subscription_id}: {e}")
            return False
    
    async def update_subscription(self, subscription_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update subscription details"""
        if not self.enabled:
            logger.info(f"Stripe disabled - would update subscription: {subscription_id}")
            return {"id": subscription_id, **updates}
        
        try:
            subscription = self.stripe.Subscription.modify(subscription_id, **updates)
            logger.info(f"Stripe subscription updated: {subscription_id}")
            return subscription
                
        except Exception as e:
            logger.error(f"Error updating Stripe subscription {subscription_id}: {e}")
            return None
    
    async def list_subscription_plans(self) -> List[Dict[str, Any]]:
        """List available subscription plans (prices in Stripe)"""
        if not self.enabled:
            return [
                {
                    "id": "price_starter",
                    "object": "price",
                    "nickname": "Starter Plan",
                    "unit_amount": 2900,  # $29.00 in cents
                    "currency": "usd",
                    "recurring": {"interval": "month"},
                    "metadata": {
                        "features": "10 users, 3 sound libraries, Basic analytics"
                    }
                },
                {
                    "id": "price_professional", 
                    "object": "price",
                    "nickname": "Professional Plan",
                    "unit_amount": 5900,  # $59.00 in cents
                    "currency": "usd",
                    "recurring": {"interval": "month"},
                    "metadata": {
                        "features": "50 users, Unlimited libraries, Advanced analytics, Custom branding"
                    }
                },
                {
                    "id": "price_enterprise",
                    "object": "price",
                    "nickname": "Enterprise Plan", 
                    "unit_amount": 9900,  # $99.00 in cents
                    "currency": "usd",
                    "recurring": {"interval": "month"},
                    "metadata": {
                        "features": "Unlimited users, White labeling, API access, Priority support"
                    }
                }
            ]
        
        try:
            prices = self.stripe.Price.list(
                active=True,
                type="recurring",
                expand=["data.product"]
            )
            return prices.data
                
        except Exception as e:
            logger.error(f"Error listing Stripe prices: {e}")
            return []
    
    async def create_payment_intent(self, payment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a payment intent for one-time payments"""
        if not self.enabled:
            logger.info(f"Stripe disabled - would create payment intent: {payment_data}")
            return {
                "id": f"pi_mock_{int(datetime.utcnow().timestamp())}",
                "client_secret": "pi_mock_secret_123",
                "status": "requires_payment_method"
            }
        
        try:
            payment_intent = self.stripe.PaymentIntent.create(
                amount=payment_data["amount"],
                currency=payment_data.get("currency", "usd"),
                customer=payment_data.get("customer_id"),
                metadata=payment_data.get("metadata", {}),
                automatic_payment_methods={"enabled": True}
            )
            logger.info(f"Stripe payment intent created: {payment_intent.id}")
            return payment_intent
                
        except Exception as e:
            logger.error(f"Error creating Stripe payment intent: {e}")
            return None
    
    async def process_webhook(self, webhook_data: Dict[str, Any], signature: str = None) -> Dict[str, Any]:
        """Process incoming webhook from Stripe"""
        try:
            # Verify webhook signature if enabled and signature provided
            if self.webhook_secret and signature:
                try:
                    event = self.stripe.Webhook.construct_event(
                        webhook_data, signature, self.webhook_secret
                    )
                except ValueError as e:
                    logger.error(f"Invalid Stripe webhook payload: {e}")
                    return {"status": "error", "message": "Invalid payload"}
                except self.stripe.error.SignatureVerificationError as e:
                    logger.error(f"Invalid Stripe webhook signature: {e}")
                    return {"status": "error", "message": "Invalid signature"}
            else:
                event = webhook_data
            
            event_type = event.get("type")
            data = event.get("data", {}).get("object", {})
            
            logger.info(f"Processing Stripe webhook: {event_type}")
            
            # Handle different webhook events
            if event_type == "customer.subscription.created":
                return await self._handle_subscription_created(data)
            elif event_type == "customer.subscription.deleted":
                return await self._handle_subscription_deleted(data)
            elif event_type == "invoice.payment_succeeded":
                return await self._handle_payment_succeeded(data)
            elif event_type == "invoice.payment_failed":
                return await self._handle_payment_failed(data)
            elif event_type == "customer.subscription.updated":
                return await self._handle_subscription_updated(data)
            else:
                logger.warning(f"Unhandled Stripe webhook event: {event_type}")
                return {"status": "ignored", "message": f"Unhandled event type: {event_type}"}
                
        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _handle_subscription_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription created webhook"""
        subscription_id = data.get("id")
        customer_id = data.get("customer")
        organization_id = data.get("metadata", {}).get("organization_id")
        
        if organization_id:
            logger.info(f"Subscription {subscription_id} created for organization {organization_id}")
            # TODO: Update organization model with subscription details
        
        return {"status": "processed", "action": "subscription_created"}
    
    async def _handle_subscription_deleted(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription deleted webhook"""
        subscription_id = data.get("id")
        organization_id = data.get("metadata", {}).get("organization_id")
        
        if organization_id:
            logger.info(f"Subscription {subscription_id} deleted for organization {organization_id}")
            # TODO: Update organization model and suspend access
        
        return {"status": "processed", "action": "subscription_deleted"}
    
    async def _handle_subscription_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updated webhook"""
        subscription_id = data.get("id")
        organization_id = data.get("metadata", {}).get("organization_id")
        
        if organization_id:
            logger.info(f"Subscription {subscription_id} updated for organization {organization_id}")
            # TODO: Update organization model with new subscription details
        
        return {"status": "processed", "action": "subscription_updated"}
    
    async def _handle_payment_succeeded(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment webhook"""
        invoice_id = data.get("id")
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")
        
        logger.info(f"Payment succeeded for invoice {invoice_id}, subscription {subscription_id}")
        # TODO: Update payment records and extend service
        
        return {"status": "processed", "action": "payment_succeeded"}
    
    async def _handle_payment_failed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment webhook"""
        invoice_id = data.get("id")
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")
        
        logger.warning(f"Payment failed for invoice {invoice_id}, subscription {subscription_id}")
        # TODO: Handle payment failure, notify customer, suspend if needed
        
        return {"status": "processed", "action": "payment_failed"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get Stripe service status and configuration"""
        return {
            "enabled": self.enabled,
            "api_configured": bool(self.api_key),
            "webhook_configured": bool(self.webhook_secret),
            "publishable_key_configured": bool(self.publishable_key),
            "library_installed": bool(self.stripe)
        }


# Global Stripe service instance
stripe_service = StripePaymentService()
