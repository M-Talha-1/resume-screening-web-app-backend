from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, JSON, DateTime, func, Enum, Boolean, Interval, Index
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime

class JobStatus(str, enum.Enum):
    DRAFT = "Draft"
    OPEN = "Open"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"

class EvaluationStatus(str, enum.Enum):
    PENDING = "Pending"
    SHORTLISTED = "Shortlisted"
    REJECTED = "Rejected"
    INTERVIEW_SCHEDULED = "Interview Scheduled"
    OFFER_EXTENDED = "Offer Extended"
    HIRED = "Hired"

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HR = "hr"
    USER = "user"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, nullable=False, default=UserRole.USER)
    date_created = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("Job", back_populates="admin", cascade="all, delete-orphan")
    evaluations = relationship("CandidateEvaluation", back_populates="admin", cascade="all, delete-orphan")

class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    skills = Column(JSON, nullable=False)
    designation = Column(String(100), nullable=True)
    total_experience = Column(Float, nullable=False)
    current_company = Column(String(100), nullable=True)
    current_location = Column(String(100), nullable=True)
    notice_period = Column(String(50), nullable=True)
    expected_salary = Column(Float, nullable=True)
    source = Column(String(100), nullable=True)
    linkedin = Column(String(255), nullable=True)
    github = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    education = Column(JSON, nullable=True)
    experience = Column(JSON, nullable=True)
    date_created = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    resumes = relationship("Resume", back_populates="applicant")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, nullable=False, default=list)
    department = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False, index=True)
    salary_range = Column(JSON, nullable=False)
    job_type = Column(String, nullable=False)
    experience_required = Column(Float, nullable=False)
    skills_required = Column(JSON, nullable=False, default=list)
    status = Column(String, nullable=False, default=JobStatus.DRAFT)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    admin = relationship("User", back_populates="jobs")
    evaluations = relationship("CandidateEvaluation", back_populates="job")
    resumes = relationship("Resume", back_populates="job")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.requirements:
            self.requirements = []
        if not self.skills_required:
            self.skills_required = []
        self.updated_at = datetime.utcnow()

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_content = Column(JSON, nullable=True)
    extracted_skills = Column(JSON, nullable=True)
    total_experience = Column(Float, nullable=True)
    education = Column(JSON, nullable=True)
    work_experience = Column(JSON, nullable=True)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    applicant = relationship("Applicant", back_populates="resumes")
    job = relationship("Job", back_populates="resumes")
    evaluations = relationship("CandidateEvaluation", back_populates="resume")

    __table_args__ = (
        Index('idx_resumes_applicant_job', 'applicant_id', 'job_id'),
    )

class CandidateEvaluation(Base):
    __tablename__ = "candidate_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, nullable=False)
    skill_match = Column(Float, nullable=False)
    experience_match = Column(Float, nullable=False)
    matching_skills = Column(JSON, nullable=False, default=list)
    comments = Column(Text, nullable=True)
    status = Column(String, nullable=False, default=EvaluationStatus.PENDING)
    evaluation_date = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    evaluation_duration = Column(Interval, nullable=True)
    evaluation_start_time = Column(DateTime(timezone=True), nullable=True)

    resume = relationship("Resume", back_populates="evaluations")
    job = relationship("Job", back_populates="evaluations")
    admin = relationship("User", back_populates="evaluations")

    __table_args__ = (
        Index('idx_evaluations_resume_job', 'resume_id', 'job_id'),
        Index('idx_evaluations_status', 'status'),
    )

