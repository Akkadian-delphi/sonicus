#!/usr/bin/env python3

import sys
sys.path.append('.')

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreateSchema, UserReadSchema
from app.core.security import get_current_user
from app.db.b2b2c_session import get_contextual_db_session
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserReadSchema)
def register_user(
    user_data: UserCreateSchema, 
    db: Session = Depends(get_contextual_db_session)
):
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        hashed_password = pwd_context.hash(user_data.password)
        new_user = User(email=user_data.email, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Return as dict to avoid serialization issues
        return {
            "id": new_user.id,
            "email": new_user.email,
            "is_active": getattr(new_user, 'is_active', True)
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

@router.get("/users/me", response_model=UserReadSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": getattr(current_user, 'is_active', True)
    }

if __name__ == "__main__":
    print("Testing minimal user router...")
    try:
        print(f"✅ Router created successfully with {len(router.routes)} routes")
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = getattr(route, 'methods', 'UNKNOWN')
                path = getattr(route, 'path', 'UNKNOWN')
                print(f"  - {methods} {path}")
            else:
                print(f"  - {type(route).__name__}")
    except Exception as e:
        print(f"❌ Router creation failed: {e}")
        import traceback
        traceback.print_exc()
