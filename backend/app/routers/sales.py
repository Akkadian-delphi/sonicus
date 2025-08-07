from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Response
from sqlalchemy.orm import Session
from typing import List

from app.models.user import User
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.therapy_sound import TherapySound
from app.schemas.subscription import SubscriptionCreateSchema, SubscriptionReadSchema
from app.schemas.invoice import InvoiceReadSchema
from app.core.security import get_current_user
from app.db.b2b2c_session import get_contextual_db_session
from app.services.email import send_invoice_email

router = APIRouter()

@router.post("/subscriptions", response_model=SubscriptionReadSchema)
def create_subscription(
    subscription_data: SubscriptionCreateSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_contextual_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new subscription to a therapeutic sound.
    
    Creates a subscription for the authenticated user to access a specific sound,
    generates an invoice, and sends a confirmation email.
    """
    # Check if the sound exists
    sound = db.query(TherapySound).filter(TherapySound.id == subscription_data.sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")
    
    # Check if user already has an active subscription for this sound
    existing_sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.sound_id == subscription_data.sound_id,
        Subscription.status == "active"
    ).first()
    
    if existing_sub:
        raise HTTPException(status_code=400, detail="You already have an active subscription for this sound")
    
    # Create subscription
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)  # 30-day subscription
    
    new_subscription = Subscription(
        user_id=current_user.id,
        sound_id=subscription_data.sound_id,
        start_date=start_date,
        end_date=end_date,
        status="active"
    )
    
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)
    
    # Create invoice for the subscription
    invoice_amount = 9.99  # Example price
    new_invoice = Invoice(
        user_id=current_user.id,
        subscription_id=new_subscription.id,
        amount=invoice_amount,
        issue_date=datetime.utcnow(),
        status="pending"
    )
    
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    
    # Send invoice email
    user_email = getattr(current_user, 'email')
    invoice_id = getattr(new_invoice, 'id')
    send_invoice_email(background_tasks, user_email, invoice_id)
    
    return new_subscription

@router.get("/subscriptions", response_model=List[SubscriptionReadSchema])
def get_user_subscriptions(
    response: Response,
    skip: int = Query(0, description="Skip items"),
    limit: int = Query(20, le=50, description="Limit items per page"),
    status: str = Query(None, description="Filter by status (active, expired, etc.)"),
    db: Session = Depends(get_contextual_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    List user's subscriptions.
    
    Returns a paginated list of the user's subscriptions, optionally filtered by status.
    """
    query = db.query(Subscription).filter(Subscription.user_id == current_user.id)
    
    if status:
        query = query.filter(Subscription.status == status)
    
    # Cache results for 5 minutes unless it's dynamic or changing frequently
    response.headers["Cache-Control"] = "private, max-age=300"
    
    # Apply pagination
    subscriptions = query.offset(skip).limit(limit).all()
    
    return subscriptions

@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionReadSchema)
def get_subscription(
    subscription_id: int,
    response: Response,
    db: Session = Depends(get_contextual_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get details about a specific subscription.
    
    Returns information about a specific subscription by ID.
    """
    # Enable client caching for 2 minutes
    response.headers["Cache-Control"] = "private, max-age=120"
    
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return subscription

@router.get("/invoices", response_model=List[InvoiceReadSchema])
def get_user_invoices(
    response: Response,
    skip: int = Query(0, description="Skip items"),
    limit: int = Query(20, le=50, description="Limit items per page"),
    status: str = Query(None, description="Filter by status (pending, paid, etc.)"),
    db: Session = Depends(get_contextual_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    List user's invoices.
    
    Returns a paginated list of the user's invoices, optionally filtered by status.
    """
    query = db.query(Invoice).filter(Invoice.user_id == current_user.id)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    # Cache results for 5 minutes
    response.headers["Cache-Control"] = "private, max-age=300"
    
    # Apply pagination
    invoices = query.offset(skip).limit(limit).all()
    
    return invoices

@router.get("/invoices/{invoice_id}", response_model=InvoiceReadSchema)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_contextual_db_session),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice