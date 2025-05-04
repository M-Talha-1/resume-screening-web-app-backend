from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from typing import Generator
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import contextlib

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./resume.db"

# Create engine with SQLite configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Define Base
Base = declarative_base()

@contextlib.contextmanager
def get_db_context():
    """Database context manager"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error in context manager: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def get_db():
    """
    Database session dependency for FastAPI
    """
    with get_db_context() as db:
        try:
            db.execute("SELECT 1")  # Test the connection
            yield db
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            db.rollback()
            raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def test_connection():
    """
    Test database connection with retry mechanism
    """
    with get_db_context() as db:
        try:
            db.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            return False

def init_db():
    """
    Initialize database with proper error handling
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise
