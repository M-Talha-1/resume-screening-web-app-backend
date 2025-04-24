from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv
from typing import Generator

# Load environment variables
load_dotenv()

# Use peer authentication with current system user
DATABASE_URL = "postgresql://backenddev:root%40123@localhost/resume_db"

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    echo=True  # Enable SQL query logging for debugging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent detached instance errors
)

# Define Base
Base = declarative_base()
metadata = MetaData()

def get_db() -> Generator:
    """
    Database session dependency for FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test database connection
def test_connection():
    db = SessionLocal()
    try:
        db.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return False
    finally:
        db.close()
