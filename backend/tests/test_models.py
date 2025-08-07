import os
import sys
import pytest
from datetime import datetime, timedelta

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.user import User
from app.models.therapy_sound import TherapySound
from app.models.subscription import Subscription
from app.models.invoice import Invoice

def test_user_model(db):
    """Test creating and retrieving a User model"""
    user = User(
        email="model_test@example.com",
        hashed_password="hashed_test_password",
        is_active=True
    )
    db.add(user)
    db.commit()
    
    # Verify user was created properly
    retrieved_user = db.query(User).filter(User.email == "model_test@example.com").first()
    assert retrieved_user is not None
    assert retrieved_user.email == "model_test@example.com"
    assert retrieved_user.hashed_password == "hashed_test_password"
    assert retrieved_user.is_active is True
    assert retrieved_user.is_superuser is False  # Default value

def test_therapy_sound_model(db):
    """Test creating and retrieving a TherapySound model"""
    sound = TherapySound(
        title="Model Test Sound",
        description="Sound for model testing",
        category="test",
        duration=120.5,
        secure_storage_path="/test/path/sound.mp3"
    )
    db.add(sound)
    db.commit()
    
    # Verify sound was created properly
    retrieved_sound = db.query(TherapySound).filter(TherapySound.title == "Model Test Sound").first()
    assert retrieved_sound is not None
    assert retrieved_sound.title == "Model Test Sound"
    assert retrieved_sound.description == "Sound for model testing"
    assert retrieved_sound.category == "test"
    assert retrieved_sound.duration == 120.5
    assert retrieved_sound.secure_storage_path == "/test/path/sound.mp3"

def test_subscription_model(db):
    """Test creating and retrieving a Subscription model with relationships"""
    # Create related models
    user = User(email="sub_test@example.com", hashed_password="test_hash")
    sound = TherapySound(
        title="Subscription Test Sound",
        description="Test subscription",
        duration=60.0,
        secure_storage_path="/test/path/sub.mp3"
    )
    
    db.add(user)
    db.add(sound)
    db.commit()
    
    # Create subscription
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)
    
    subscription = Subscription(
        user_id=user.id,
        sound_id=sound.id,
        start_date=start_date,
        end_date=end_date,
        status="active"
    )
    
    db.add(subscription)
    db.commit()
    
    # Test retrieval and relationships
    retrieved_sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.sound_id == sound.id
    ).first()
    
    assert retrieved_sub is not None
    assert retrieved_sub.status == "active"
    assert retrieved_sub.user.email == "sub_test@example.com"
    assert retrieved_sub.sound.title == "Subscription Test Sound"

def test_invoice_model(db):
    """Test creating and retrieving an Invoice model with relationships"""
    # Create related models
    user = User(email="invoice_test@example.com", hashed_password="test_hash")
    sound = TherapySound(
        title="Invoice Test Sound",
        description="Test invoice",
        duration=90.0,
        secure_storage_path="/test/path/invoice.mp3"
    )
    
    db.add(user)
    db.add(sound)
    db.commit()
    
    # Create subscription
    subscription = Subscription(
        user_id=user.id,
        sound_id=sound.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        status="active"
    )
    
    db.add(subscription)
    db.commit()
    
    # Create invoice
    invoice = Invoice(
        user_id=user.id,
        subscription_id=subscription.id,
        amount=9.99,
        issue_date=datetime.utcnow(),
        status="pending"
    )
    
    db.add(invoice)
    db.commit()
    
    # Test retrieval and relationships
    retrieved_invoice = db.query(Invoice).filter(
        Invoice.user_id == user.id,
        Invoice.subscription_id == subscription.id
    ).first()
    
    assert retrieved_invoice is not None
    assert retrieved_invoice.amount == 9.99
    assert retrieved_invoice.status == "pending"
    assert retrieved_invoice.user.email == "invoice_test@example.com"
    assert retrieved_invoice.subscription.status == "active"
