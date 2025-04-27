from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, JSON, DateTime, func, Enum, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime

class JobStatus(str, enum.Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    FILLED = "Filled"
    DRAFT = "Draft"

class EvaluationStatus(str, enum.Enum):
    PENDING = "Pending"
    SHORTLISTED = "Shortlisted"
    REJECTED = "Rejected"
    INTERVIEW_SCHEDULED = "Interview Scheduled"
    OFFER_EXTENDED = "Offer Extended"
    HIRED = "Hired"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)  # "admin", "hr", etc.
    hashed_password = Column(String, nullable=False)
    date_created = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    job_descriptions = relationship("JobDescription", back_populates="admin")
    evaluations = relationship("CandidateEvaluation", back_populates="hr_manager")


class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False, default="Applicant")
    date_created = Column(DateTime, server_default=func.now())
    phone = Column(String, nullable=True)
    skills = Column(JSON, nullable=True)
    designation = Column(String, nullable=True)
    total_experience = Column(Float, nullable=True)
    current_company = Column(String, nullable=True)
    current_location = Column(String, nullable=True)
    notice_period = Column(Integer, nullable=True)  # in days
    expected_salary = Column(Float, nullable=True)
    source = Column(String, nullable=True)  # where did they come from (referral, job portal, etc.)

    resumes = relationship("Resume", back_populates="applicant", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id", ondelete="CASCADE"))
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"))
    file_path = Column(String, nullable=False)
    upload_date = Column(DateTime, server_default=func.now())
    parsed_status = Column(String, nullable=False, default="Pending")
    text_content = Column(Text, nullable=True)
    file_type = Column(String, nullable=False)  # pdf, docx, etc.
    file_size = Column(Integer, nullable=False)  # in bytes
    status = Column(String, nullable=True, default="Pending")

    applicant = relationship("Applicant", back_populates="resumes")
    job = relationship("JobDescription", back_populates="resumes")
    evaluations = relationship("CandidateEvaluation", back_populates="resume", cascade="all, delete-orphan")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True)
    posted_date = Column(DateTime, server_default=func.now())
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.DRAFT)
    location = Column(String, nullable=True)
    department = Column(String, nullable=True)
    experience_required = Column(Float, nullable=True)  # in years
    salary_range_min = Column(Float, nullable=True)
    salary_range_max = Column(Float, nullable=True)
    job_type = Column(String, nullable=True)  # Full-time, Part-time, Contract, etc.
    closing_date = Column(DateTime, nullable=True)
    total_applicants = Column(Integer, default=0)
    total_shortlisted = Column(Integer, default=0)
    total_rejected = Column(Integer, default=0)

    admin = relationship("User", back_populates="job_descriptions")
    resumes = relationship("Resume", back_populates="job", cascade="all, delete-orphan")
    evaluations = relationship("CandidateEvaluation", back_populates="job", cascade="all, delete-orphan")


class CandidateEvaluation(Base):
    __tablename__ = "candidate_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    hr_manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    suitability_score = Column(Float, nullable=False)
    comments = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    evaluation_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, onupdate=datetime.utcnow)
    evaluation_duration = Column(Float, nullable=True)  # Duration in minutes
    evaluation_start_time = Column(DateTime, nullable=True)  # When evaluation started

    resume = relationship("Resume", back_populates="evaluations")
    job = relationship("JobDescription", back_populates="evaluations")
    hr_manager = relationship("User", back_populates="evaluations")

