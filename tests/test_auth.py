from fastapi import status
from app.models import User
from app.auth import get_password_hash

def test_create_user(client, db_session):
    # Test data
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword",
        "role": "admin"
    }
    
    # Create user
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["name"] == user_data["name"]
    assert data["role"] == user_data["role"]
    assert "id" in data

def test_login_user(client, db_session):
    # Create test user
    user = User(
        name="Test User",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    
    # Test login
    login_data = {
        "username": "test@example.com",
        "password": "testpassword"
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client, db_session):
    # Test login with invalid credentials
    login_data = {
        "username": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user(client, db_session):
    # Create test user
    user = User(
        name="Test User",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    
    # Get token
    login_data = {
        "username": "test@example.com",
        "password": "testpassword"
    }
    response = client.post("/auth/token", data=login_data)
    token = response.json()["access_token"]
    
    # Test getting current user
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["role"] == "admin"

def test_register_user(client):
    user_data = {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "newpassword",
        "role": "admin"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["name"] == user_data["name"]
    assert data["role"] == user_data["role"]
    assert "id" in data

def test_register_duplicate_user(client, test_user):
    user_data = {
        "name": "Test User",
        "email": "test@example.com",  # Same email as test_user
        "password": "testpassword",
        "role": "admin"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_user(client, test_user):
    login_data = {
        "username": test_user["email"],
        "password": "testpassword"
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    login_data = {
        "username": "wrong@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_get_current_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "admin"

def test_get_current_user_invalid_token(client):
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"] 