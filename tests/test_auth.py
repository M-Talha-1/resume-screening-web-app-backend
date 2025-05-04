import pytest
from fastapi import HTTPException
from datetime import timedelta
import uuid
from app.auth import (
    verify_password,
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user
)
from app.models import User
from app.schemas import TokenData

def test_verify_password():
    password = "testpassword123!"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False

def test_get_password_hash():
    password = "testpassword123!"
    hashed_password = get_password_hash(password)
    assert hashed_password is not None
    assert hashed_password != password
    assert len(hashed_password) > 0

def test_authenticate_user_success(db_session, test_user):
    authenticated_user = authenticate_user(
        db_session,
        email=test_user.email,
        password="testpassword"
    )
    assert authenticated_user is not None
    assert authenticated_user.id == test_user.id
    assert authenticated_user.email == test_user.email

def test_authenticate_user_wrong_password(db_session, test_user):
    authenticated_user = authenticate_user(
        db_session,
        email=test_user.email,
        password="wrongpassword"
    )
    assert authenticated_user is None

def test_authenticate_user_nonexistent(db_session):
    unique_id = str(uuid.uuid4())
    authenticated_user = authenticate_user(
        db_session,
        email=f"nonexistent{unique_id}@example.com",
        password="testpassword"
    )
    assert authenticated_user is None

def test_create_access_token():
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    assert token is not None
    assert len(token) > 0

def test_create_access_token_with_expiry():
    data = {"sub": "test@example.com"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta)
    assert token is not None
    assert len(token) > 0

@pytest.mark.asyncio
async def test_get_current_user_valid_token(db_session, test_user):
    token = create_access_token({"sub": test_user.email})
    user = await get_current_user(token, db_session)
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db_session):
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("invalid_token", db_session)
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_expired_token(db_session, test_user):
    # Create an expired token
    data = {"sub": test_user.email}
    expires_delta = timedelta(minutes=-1)  # Negative delta to create expired token
    token = create_access_token(data, expires_delta)
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token, db_session)
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_inactive_user(db_session, test_user):
    # Make user inactive
    test_user.is_active = False
    db_session.commit()
    
    token = create_access_token({"sub": test_user.email})
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token, db_session)
    assert exc_info.value.status_code == 401
    
    # Reset user state
    test_user.is_active = True
    db_session.commit() 