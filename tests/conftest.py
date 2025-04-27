import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app.auth import create_access_token
from app.models import User, JobDescription, Resume, CandidateEvaluation, Applicant
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)  # Ensure clean state
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()  # Rollback any pending transactions
        db.close()
        Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client():
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture(scope="function")
def test_hr_manager(db):
    user = User(
        name="HR Manager",
        email="hr@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfJAAcxgpK.Dvie",  # Test password
        role="hr_manager",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_token(test_hr_manager):
    access_token = create_access_token(
        data={"sub": test_hr_manager.email},
        expires_delta=timedelta(minutes=30)
    )
    return access_token 