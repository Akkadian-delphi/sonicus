import pytest
from fastapi.testclient import TestClient

# Authentication tests
def test_register_user(client):
    """Test user registration endpoint"""
    response = client.post(
        "/api/v1/users",
        json={"email": "newuser@example.com", "password": "SecurePass123!"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "is_active" in data
    assert "password" not in data  # Ensure password is not returned

def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_password(client, test_user):
    """Test login with incorrect password"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "testpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_get_current_user(client, auth_headers):
    """Test getting current user profile"""
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"

def test_unauthorized_access(client):
    """Test accessing protected endpoint without authentication"""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

def test_password_reset_request(client, test_user):
    """Test password reset request"""
    response = client.post(
        "/api/v1/auth/password-reset",
        params={"email": "test@example.com"}
    )
    assert response.status_code == 202
    assert "message" in response.json()

# Sound endpoints tests
def test_list_sounds(client, test_sound):
    """Test listing sounds endpoint"""
    response = client.get("/api/v1/sounds")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Test Meditation"
    assert data[0]["category"] == "meditation"

def test_get_sound_categories(client, test_sound):
    """Test getting sound categories"""
    response = client.get("/api/v1/sounds/categories")
    assert response.status_code == 200
    data = response.json()
    assert "meditation" in data

def test_get_sound_by_id(client, test_sound):
    """Test getting a specific sound by ID"""
    response = client.get(f"/api/v1/sounds/{test_sound.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Meditation"
    assert data["description"] == "A calming meditation for tests"

def test_get_nonexistent_sound(client):
    """Test getting a non-existent sound"""
    response = client.get("/api/v1/sounds/999")
    assert response.status_code == 404
    assert "Sound not found" in response.json()["detail"]

def test_search_sounds(client, test_sound):
    """Test searching sounds"""
    # Search by title
    response = client.get("/api/v1/sounds?q=Meditation")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Test Meditation" in [s["title"] for s in data]
    
    # Search by category
    response = client.get("/api/v1/sounds?category=meditation")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "meditation" in [s["category"] for s in data]

# Subscription endpoint tests
def test_create_subscription(client, auth_headers, test_sound, db):
    """Test creating a subscription"""
    response = client.post(
        "/api/v1/subscriptions",
        json={"sound_id": test_sound.id},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert "id" in data

def test_create_duplicate_subscription(client, auth_headers, test_sound, test_user, db):
    """Test creating a duplicate subscription"""
    # First subscription
    client.post(
        "/api/v1/subscriptions",
        json={"sound_id": test_sound.id},
        headers=auth_headers
    )
    
    # Attempt to create duplicate subscription
    response = client.post(
        "/api/v1/subscriptions",
        json={"sound_id": test_sound.id},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "already have an active subscription" in response.json()["detail"]

def test_get_user_subscriptions(client, auth_headers, test_sound, test_user, db):
    """Test getting user subscriptions"""
    # Create a subscription first
    client.post(
        "/api/v1/subscriptions",
        json={"sound_id": test_sound.id},
        headers=auth_headers
    )
    
    # Get subscriptions
    response = client.get("/api/v1/subscriptions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "active"

def test_get_invoices(client, auth_headers, test_sound, test_user, db):
    """Test getting user invoices"""
    # Create a subscription to generate an invoice
    client.post(
        "/api/v1/subscriptions",
        json={"sound_id": test_sound.id},
        headers=auth_headers
    )
    
    # Get invoices
    response = client.get("/api/v1/invoices", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "pending"

# Health check test
def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

# API docs test
def test_swagger_ui_accessible(client):
    """Test that Swagger UI is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()

def test_redoc_accessible(client):
    """Test that ReDoc is accessible"""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()
