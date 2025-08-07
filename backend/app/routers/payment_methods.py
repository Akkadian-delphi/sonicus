from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Dict, Any

from app.services.payment_methods_service import PaymentMethodsService
from app.models.user import PaymentMethod

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])

@router.get("/available", response_model=List[Dict[str, Any]])
async def get_available_payment_methods(
    currency: str = Query("USD", description="Currency code (USD, EUR, GBP, etc.)"),
    platform: Optional[str] = Query(None, description="Platform (ios, android, web)"),
    amount: Optional[float] = Query(None, description="Transaction amount to check limits", ge=0)
):
    """Get list of available payment methods based on criteria."""
    return PaymentMethodsService.get_available_payment_methods(
        currency=currency,
        platform=platform,
        amount=amount
    )

@router.get("/recommended", response_model=List[Dict[str, Any]])
async def get_recommended_payment_methods(
    currency: str = Query("USD", description="Currency code"),
    platform: Optional[str] = Query(None, description="Platform (ios, android, web)"),
    amount: Optional[float] = Query(None, description="Transaction amount", ge=0)
):
    """Get recommended payment methods sorted by best options."""
    return PaymentMethodsService.get_recommended_payment_methods(
        currency=currency,
        amount=amount,
        platform=platform
    )

@router.get("/{method}/info", response_model=Dict[str, Any])
async def get_payment_method_info(method: PaymentMethod):
    """Get detailed information about a specific payment method."""
    return PaymentMethodsService.get_payment_method_info(method)

@router.post("/{method}/validate", response_model=Dict[str, Any])
async def validate_payment_method(
    method: PaymentMethod,
    currency: str = Query("USD", description="Currency code"),
    amount: Optional[float] = Query(None, description="Transaction amount", ge=0)
):
    """Validate if a payment method can be used for a transaction."""
    return PaymentMethodsService.validate_payment_method(
        method=method,
        currency=currency,
        amount=amount
    )

@router.get("/{method}/fee", response_model=Dict[str, float])
async def calculate_processing_fee(
    method: PaymentMethod,
    amount: float = Query(..., description="Transaction amount", ge=0)
):
    """Calculate processing fee for a payment method and amount."""
    fee = PaymentMethodsService.calculate_processing_fee(method, amount)
    return {
        "amount": amount,
        "processing_fee": fee,
        "total": amount + fee
    }
