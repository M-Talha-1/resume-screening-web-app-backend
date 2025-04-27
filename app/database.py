from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from typing import Generator

# Load environment variables
load_dotenv()

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create engine with connection pooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define Base
Base = declarative_base()

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
