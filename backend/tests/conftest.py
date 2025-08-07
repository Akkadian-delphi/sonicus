import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from passlib.context import CryptContext

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.therapy_sound import TherapySound
from app.core.security import create_access_token
from run import app

# Define pwd_context for testing if it's not importable from security module
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create an in-memory SQLite database for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Fixture that creates clean database tables for each test function"""
    # Create the test database and tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session for the test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up the database after the test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """
    Create a FastAPI TestClient with a dependency override for the database
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    
    # Remove the override after the test
    app.dependency_overrides = {}

@pytest.fixture(scope="function")
def test_user(db):
    """Fixture to create a test user"""
    hashed_password = pwd_context.hash("testpassword")
    user = User(
        email="test@example.com",
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_admin(db):
    """Fixture to create a test admin user"""
    hashed_password = pwd_context.hash("adminpassword")
    admin = User(
        email="admin@example.com",
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def test_sound(db):
    """Fixture to create a test therapy sound"""
    sound = TherapySound(
        title="Test Meditation",
        description="A calming meditation for tests",
        category="meditation",
        duration=300.0,  # 5 minutes
        secure_storage_path="/fake/path/test_meditation.mp3"
    )
    db.add(sound)
    db.commit()
    db.refresh(sound)
    return sound

@pytest.fixture(scope="function")
def user_token(test_user):
    """Fixture to create a valid JWT token for the test user"""
    return create_access_token(data={"sub": str(test_user.id)})

@pytest.fixture(scope="function")
def admin_token(test_admin):
    """Fixture to create a valid JWT token for the test admin"""
    return create_access_token(data={"sub": str(test_admin.id)})

@pytest.fixture(scope="function")
def auth_headers(user_token):
    """Fixture to create authorization headers with the test user token"""
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture(scope="function")
def admin_headers(admin_token):
    """Fixture to create authorization headers with the test admin token"""
    return {"Authorization": f"Bearer {admin_token}"}
