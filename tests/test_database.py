import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid
from app.models import User, Job, Applicant, Resume, CandidateEvaluation

def test_user_creation(db_session):
    unique_id = str(uuid.uuid4())
    user = User(
        email=f"newuser{unique_id}@example.com",
        name="New User",
        hashed_password="hashed_password",
        is_active=True,
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    retrieved_user = db_session.query(User).filter_by(email=user.email).first()
    assert retrieved_user is not None
    assert retrieved_user.name == "New User"
    assert retrieved_user.is_active is True
    assert retrieved_user.role == "user"

def test_user_unique_email_constraint(db_session, test_user):
    with pytest.raises(IntegrityError):
        duplicate_user = User(
            email=test_user.email,  # Same email as test_user
            name="Duplicate User",
            hashed_password="hashed_password",
            is_active=True,
            role="user"
        )
        db_session.add(duplicate_user)
        db_session.commit()

def test_job_creation(db_session, test_user):
    job = Job(
        admin_id=test_user.id,
        title="New Job",
        description="New Job Description",
        requirements=["Python", "FastAPI"],
        department="Engineering",
        location="Remote",
        salary_range={"min": 50000, "max": 100000},
        job_type="Full-time",
        experience_required=3.0,
        skills_required=["Python", "FastAPI"],
        status="Open"
    )
    db_session.add(job)
    db_session.commit()
    
    retrieved_job = db_session.query(Job).filter_by(title="New Job").first()
    assert retrieved_job is not None
    assert retrieved_job.admin_id == test_user.id
    assert retrieved_job.department == "Engineering"
    assert retrieved_job.status == "Open"

def test_applicant_creation(db_session):
    unique_id = str(uuid.uuid4())
    applicant = Applicant(
        name="New Applicant",
        email=f"newapplicant{unique_id}@example.com",
        phone="1234567890",
        skills=["Python", "FastAPI"],
        total_experience=3.0
    )
    db_session.add(applicant)
    db_session.commit()
    
    retrieved_applicant = db_session.query(Applicant).filter_by(email=applicant.email).first()
    assert retrieved_applicant is not None
    assert retrieved_applicant.name == "New Applicant"
    assert retrieved_applicant.total_experience == 3.0
    assert "Python" in retrieved_applicant.skills

def test_resume_creation(db_session, test_applicant, test_job):
    resume = Resume(
        applicant_id=test_applicant.id,
        job_id=test_job.id,
        raw_text="New resume content",
        file_path="new.pdf",
        file_type="pdf",
        file_size=2048
    )
    db_session.add(resume)
    db_session.commit()
    
    retrieved_resume = db_session.query(Resume).filter_by(file_path="new.pdf").first()
    assert retrieved_resume is not None
    assert retrieved_resume.applicant_id == test_applicant.id
    assert retrieved_resume.job_id == test_job.id
    assert retrieved_resume.file_size == 2048

def test_evaluation_creation(db_session, test_resume, test_job, test_user):
    evaluation = CandidateEvaluation(
        resume_id=test_resume.id,
        job_id=test_job.id,
        admin_id=test_user.id,
        overall_score=90.0,
        skill_match=95.0,
        experience_match=85.0,
        matching_skills=["Python", "FastAPI"],
        status="Shortlisted"
    )
    db_session.add(evaluation)
    db_session.commit()
    
    retrieved_evaluation = db_session.query(CandidateEvaluation).filter_by(resume_id=test_resume.id).first()
    assert retrieved_evaluation is not None
    assert retrieved_evaluation.overall_score == 90.0
    assert retrieved_evaluation.status == "Shortlisted"
    assert "Python" in retrieved_evaluation.matching_skills

def test_cascade_delete(db_session, test_user):
    # Create a job for the user
    job = Job(
        admin_id=test_user.id,
        title="Test Job for Cascade",
        description="Test Description",
        requirements=["Python"],
        department="Engineering",
        location="Remote",
        salary_range={"min": 50000, "max": 100000},
        job_type="Full-time",
        experience_required=3.0,
        skills_required=["Python"],
        status="Open"
    )
    db_session.add(job)
    db_session.commit()
    
    # Delete the user
    db_session.delete(test_user)
    db_session.commit()
    
    # Verify job is also deleted
    deleted_job = db_session.query(Job).filter_by(title="Test Job for Cascade").first()
    assert deleted_job is None

def test_foreign_key_constraint(db_session):
    with pytest.raises(IntegrityError):
        # Try to create a resume with non-existent applicant and job IDs
        resume = Resume(
            applicant_id=999999,  # Non-existent ID
            job_id=999999,        # Non-existent ID
            raw_text="Test content",
            file_path="test.pdf",
            file_type="pdf",
            file_size=1024
        )
        db_session.add(resume)
        db_session.commit() 