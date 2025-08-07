"""
Payment methods service for managing available payment options.
"""

from typing import List, Dict, Any, Optional
from app.models.user import PaymentMethod
import logging

logger = logging.getLogger(__name__)

class PaymentMethodsService:
    """Service class for managing payment methods and their availability."""
    
    # Configuration for available payment methods
    PAYMENT_METHODS_CONFIG = {
        PaymentMethod.CREDIT_CARD: {
            "name": "Credit Card",
            "description": "Visa, MasterCard, American Express",
            "icon": "credit-card",
            "enabled": True,
            "processing_fee": 2.9,  # percentage
            "currencies": ["USD", "EUR", "GBP"],
            "min_amount": 1.00,
            "max_amount": 10000.00
        },
        PaymentMethod.DEBIT_CARD: {
            "name": "Debit Card",
            "description": "Direct debit from your bank account",
            "icon": "debit-card",
            "enabled": True,
            "processing_fee": 1.5,  # percentage
            "currencies": ["USD", "EUR", "GBP"],
            "min_amount": 1.00,
            "max_amount": 5000.00
        },
        PaymentMethod.PAYPAL: {
            "name": "PayPal",
            "description": "Pay with your PayPal account",
            "icon": "paypal",
            "enabled": True,
            "processing_fee": 3.4,  # percentage
            "currencies": ["USD", "EUR", "GBP", "CAD", "AUD"],
            "min_amount": 1.00,
            "max_amount": 10000.00
        },
        PaymentMethod.APPLE_PAY: {
            "name": "Apple Pay",
            "description": "Quick and secure payment with Touch ID or Face ID",
            "icon": "apple-pay",
            "enabled": True,
            "processing_fee": 2.9,  # percentage
            "currencies": ["USD", "EUR", "GBP"],
            "min_amount": 1.00,
            "max_amount": 3000.00,
            "platform_required": "ios"
        },
        PaymentMethod.GOOGLE_PAY: {
            "name": "Google Pay",
            "description": "Fast and easy payment with Google Pay",
            "icon": "google-pay",
            "enabled": True,
            "processing_fee": 2.9,  # percentage
            "currencies": ["USD", "EUR", "GBP"],
            "min_amount": 1.00,
            "max_amount": 3000.00,
            "platform_required": "android"
        },
        PaymentMethod.BANK_TRANSFER: {
            "name": "Bank Transfer",
            "description": "Direct transfer from your bank account",
            "icon": "bank-transfer",
            "enabled": True,
            "processing_fee": 0.5,  # percentage
            "currencies": ["USD", "EUR", "GBP"],
            "min_amount": 10.00,
            "max_amount": 50000.00,
            "processing_time": "2-3 business days"
        },
        PaymentMethod.CRYPTO: {
            "name": "Cryptocurrency",
            "description": "Bitcoin, Ethereum, and other cryptocurrencies",
            "icon": "crypto",
            "enabled": False,  # Disabled by default - enable when crypto integration is ready
            "processing_fee": 1.0,  # percentage
            "currencies": ["BTC", "ETH", "USDC"],
            "min_amount": 5.00,
            "max_amount": 25000.00,
            "note": "Coming soon"
        }
    }
    
    @staticmethod
    def get_available_payment_methods(
        currency: str = "USD",
        platform: Optional[str] = None,
        amount: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of available payment methods based on criteria.
        
        Args:
            currency: Currency code (USD, EUR, etc.)
            platform: Platform (ios, android, web)
            amount: Transaction amount to check limits
        
        Returns:
            List of available payment methods with their details
        """
        available_methods = []
        
        for method, config in PaymentMethodsService.PAYMENT_METHODS_CONFIG.items():
            # Skip disabled methods
            if not config.get("enabled", False):
                continue
            
            # Check currency support
            if currency and currency not in config.get("currencies", []):
                continue
            
            # Check platform requirements
            platform_required = config.get("platform_required")
            if platform_required and platform != platform_required:
                continue
            
            # Check amount limits
            if amount is not None:
                min_amount = config.get("min_amount", 0)
                max_amount = config.get("max_amount", float('inf'))
                if amount < min_amount or amount > max_amount:
                    continue
            
            # Build method info
            method_info = {
                "value": method.value,
                "name": config["name"],
                "description": config["description"],
                "icon": config["icon"],
                "processing_fee": config["processing_fee"],
                "currencies": config["currencies"],
                "min_amount": config.get("min_amount"),
                "max_amount": config.get("max_amount"),
                "processing_time": config.get("processing_time", "Instant"),
                "note": config.get("note")
            }
            
            available_methods.append(method_info)
        
        return available_methods
    
    @staticmethod
    def get_payment_method_info(method: PaymentMethod) -> Dict[str, Any]:
        """Get detailed information about a specific payment method."""
        config = PaymentMethodsService.PAYMENT_METHODS_CONFIG.get(method)
        if not config:
            return {}
        
        return {
            "value": method.value,
            "name": config["name"],
            "description": config["description"],
            "icon": config["icon"],
            "enabled": config["enabled"],
            "processing_fee": config["processing_fee"],
            "currencies": config["currencies"],
            "min_amount": config.get("min_amount"),
            "max_amount": config.get("max_amount"),
            "processing_time": config.get("processing_time", "Instant"),
            "platform_required": config.get("platform_required"),
            "note": config.get("note")
        }
    
    @staticmethod
    def validate_payment_method(
        method: PaymentMethod,
        currency: str = "USD",
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validate if a payment method can be used for a transaction.
        
        Returns:
            Dict with 'valid' boolean and 'reason' if invalid
        """
        config = PaymentMethodsService.PAYMENT_METHODS_CONFIG.get(method)
        if not config:
            return {"valid": False, "reason": "Payment method not supported"}
        
        if not config.get("enabled", False):
            return {"valid": False, "reason": "Payment method is currently disabled"}
        
        if currency not in config.get("currencies", []):
            return {"valid": False, "reason": f"Currency {currency} not supported for this payment method"}
        
        if amount is not None:
            min_amount = config.get("min_amount", 0)
            max_amount = config.get("max_amount", float('inf'))
            
            if amount < min_amount:
                return {"valid": False, "reason": f"Minimum amount is ${min_amount:.2f}"}
            
            if amount > max_amount:
                return {"valid": False, "reason": f"Maximum amount is ${max_amount:.2f}"}
        
        return {"valid": True, "reason": None}
    
    @staticmethod
    def calculate_processing_fee(method: PaymentMethod, amount: float) -> float:
        """Calculate processing fee for a payment method and amount."""
        config = PaymentMethodsService.PAYMENT_METHODS_CONFIG.get(method)
        if not config:
            return 0.0
        
        fee_percentage = config.get("processing_fee", 0.0)
        return round(amount * (fee_percentage / 100), 2)
    
    @staticmethod
    def get_recommended_payment_methods(
        currency: str = "USD",
        amount: Optional[float] = None,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recommended payment methods sorted by best options."""
        available_methods = PaymentMethodsService.get_available_payment_methods(
            currency=currency,
            platform=platform,
            amount=amount
        )
        
        # Sort by processing fee (lowest first) and popularity
        priority_order = [
            PaymentMethod.APPLE_PAY.value,
            PaymentMethod.GOOGLE_PAY.value,
            PaymentMethod.PAYPAL.value,
            PaymentMethod.CREDIT_CARD.value,
            PaymentMethod.DEBIT_CARD.value,
            PaymentMethod.BANK_TRANSFER.value,
            PaymentMethod.CRYPTO.value
        ]
        
        def sort_key(method):
            try:
                priority = priority_order.index(method["value"])
            except ValueError:
                priority = len(priority_order)
            return (priority, method["processing_fee"])
        
        return sorted(available_methods, key=sort_key)
