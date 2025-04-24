from app.database import engine, Base, test_connection
from app.models import User, JobDescription, Resume, Applicant, CandidateEvaluation
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    # Test database connection
    logger.info("Testing database connection...")
    if test_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
        return

    # Create tables
    logger.info("Creating database tables...")
    try:
        Base.metadata.drop_all(bind=engine)  # Drop existing tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        return

if __name__ == "__main__":
    main() 