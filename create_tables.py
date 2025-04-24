from app.database import Base, engine
from app.models import User, JobDescription, Applicant, Resume, CandidateEvaluation

def create_tables():
    # Create all tables
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("Tables created successfully!") 