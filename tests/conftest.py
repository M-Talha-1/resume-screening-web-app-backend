import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys
from pathlib import Path
import uuid
from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
import asyncio

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.main import app
from app.database import Base, get_db
from app.config import settings, Settings, get_settings
from app.models import User, Job, Applicant, Resume, CandidateEvaluation
from app.auth import get_password_hash

# Configure pytest-asyncio to use "auto" mode
def pytest_configure(config):
    config.option.asyncio_mode = "auto"

# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Enable foreign key constraints in SQLite
def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')

event.listen(engine, 'connect', _fk_pragma_on_connect)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test Redis configuration
TEST_REDIS_URL = "redis://localhost:6379/1"

@pytest_asyncio.fixture(scope="function")
async def test_redis():
    """Create a Redis client for testing"""
    client = redis.from_url(TEST_REDIS_URL, encoding="utf-8", decode_responses=True)
    await client.flushdb()  # Clear database before each test
    yield client
    await client.flushdb()  # Clean up after test
    await client.close()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def initialize_rate_limiter(test_redis):
    """Initialize FastAPILimiter with Redis for testing"""
    await FastAPILimiter.init(test_redis)
    yield
    # Clean up by closing the Redis connection
    await test_redis.flushdb()

# Mock rate limiter for testing
class MockRateLimiter:
    async def __call__(self, request: Request, response: Response):
        return True

def override_rate_limiter():
    return MockRateLimiter()

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def create_test_tables():
    """Create all tables in the test database"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="session")
def test_app():
    # Create test settings
    test_settings = Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        SECRET_KEY="test_secret_key"
    )
    
    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[RateLimiter] = override_rate_limiter
    
    return app

@pytest_asyncio.fixture(scope="function")
async def event_loop():
    """Create an event loop for each test case."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def client(test_app):
    return TestClient(test_app)

@pytest.fixture(autouse=True)
def setup_db():
    """Automatically create tables before each test"""
    create_test_tables()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user for each test"""
    unique_id = str(uuid.uuid4())
    user = User(
        email=f"test{unique_id}@example.com",
        name="Test User",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_job(db_session, test_user):
    """Create a test job for each test"""
    job = Job(
        admin_id=test_user.id,
        title="Test Job",
        description="Test Description",
        requirements=["Python", "FastAPI"],
        department="Engineering",
        location="Remote",
        salary_range={"min": 50000, "max": 100000},
        job_type="Full-time",
        experience_required=3.0,
        skills_required=["Python", "FastAPI", "SQL"],
        status="Open"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job

@pytest.fixture(scope="function")
def test_applicant(db_session):
    """Create a test applicant for each test"""
    unique_id = str(uuid.uuid4())
    applicant = Applicant(
        name="Test Applicant",
        email=f"applicant{unique_id}@example.com",
        phone="1234567890",
        skills=["Python", "FastAPI"],
        total_experience=3.0
    )
    db_session.add(applicant)
    db_session.commit()
    db_session.refresh(applicant)
    return applicant

@pytest.fixture(scope="function")
def test_resume(db_session, test_applicant, test_job):
    """Create a test resume for each test"""
    resume = Resume(
        applicant_id=test_applicant.id,
        job_id=test_job.id,
        raw_text="""John Doe
Software Engineer
john.doe@example.com
(123) 456-7890

EDUCATION
Bachelor of Science in Computer Science
University of Technology
2018 - 2022

EXPERIENCE
Software Engineer at Tech Corp
2022 - Present
- Developed and maintained web applications using Python and FastAPI
- Implemented RESTful APIs and microservices architecture
- Collaborated with cross-functional teams to deliver high-quality software

SKILLS
Python, FastAPI, SQL, Docker, AWS, Git, REST APIs, Microservices""",
        file_path="test.pdf",
        file_type="application/pdf",
        file_size=1024,
        parsed_content={
            "name": "John Doe",
            "email": "john.doe@example.com",
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "school": "University of Technology",
                    "years": "2018 - 2022"
                }
            ],
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Tech Corp",
                    "duration": "2022 - Present",
                    "description": [
                        "Developed and maintained web applications using Python and FastAPI",
                        "Implemented RESTful APIs and microservices architecture",
                        "Collaborated with cross-functional teams to deliver high-quality software"
                    ]
                }
            ]
        },
        extracted_skills=["Python", "FastAPI", "SQL", "Docker", "AWS", "Git", "REST APIs", "Microservices"],
        total_experience=2.0
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    return resume

@pytest.fixture(scope="function")
def test_evaluation(db_session, test_resume, test_job, test_user):
    """Create a test evaluation for each test"""
    evaluation = CandidateEvaluation(
        resume_id=test_resume.id,
        job_id=test_job.id,
        admin_id=test_user.id,
        overall_score=85.0,
        skill_match=90.0,
        experience_match=80.0,
        matching_skills=["Python", "FastAPI"],
        status="Pending"
    )
    db_session.add(evaluation)
    db_session.commit()
    db_session.refresh(evaluation)
    return evaluation

@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup_test_redis():
    """Clean up Redis after each test"""
    yield
    test_redis_client = redis.from_url(TEST_REDIS_URL, encoding="utf-8", decode_responses=True)
    await test_redis_client.flushdb()
    await test_redis_client.close() 