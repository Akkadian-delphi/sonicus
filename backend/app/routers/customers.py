"""
Customer registration and management for B2C mode
When no organizations exist, users register as individual customers
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserReadSchema
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CustomerRegisterSchema(BaseModel):
    """Schema for customer registration in B2C mode"""
    email: EmailStr
    password: str
    name: str

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserReadSchema)
async def register_customer(
    customer_data: CustomerRegisterSchema, 
    db: Session = Depends(get_db)
):
    """
    Register a new customer in B2C mode (when no organizations exist).
    
    Creates an individual customer account without organization association.
    
    Parameters:
    - **customer_data**: Required customer information including email, password, and name
    
    Returns:
    - Customer information (excluding password)
    
    Raises:
    - 400: Email already registered
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == customer_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = pwd_context.hash(customer_data.password)
        
        # Create customer user (no organization)
        new_customer = User(
            email=customer_data.email,
            hashed_password=hashed_password,
            company_name=customer_data.name,  # Use name as company_name for compatibility
            role=UserRole.USER,  # Regular customer role
            organization_id=None,  # No organization in B2C mode
            is_active=True
        )
        
        # Start trial for new customer
        new_customer.start_trial()
        
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        
        logger.info(f"Customer registered successfully: {new_customer.email}")
        
        # Return user data without password using proper attribute access
        return UserReadSchema(
            id=getattr(new_customer, 'id'),
            email=getattr(new_customer, 'email'),
            role=getattr(new_customer, 'role'),
            is_active=getattr(new_customer, 'is_active', True),
            organization_id=getattr(new_customer, 'organization_id', None)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Customer registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )
