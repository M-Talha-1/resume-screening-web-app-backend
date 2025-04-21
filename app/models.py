from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)  # "admin", "hr", etc.
    hashed_password = Column(String, nullable=False)
    date_created = Column(DateTime, server_default=func.now())

    job_descriptions = relationship("JobDescription", back_populates="admin")
    evaluations = relationship("CandidateEvaluation", back_populates="hr_user")


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

    applicant = relationship("Applicant", back_populates="resumes")
    job = relationship("JobDescription", back_populates="resumes")
    evaluation = relationship("CandidateEvaluation", back_populates="resume", cascade="all, delete-orphan")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))  # FK now points to User
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True)
    posted_date = Column(DateTime, server_default=func.now())
    status = Column(String, nullable=False, default="Open")

    admin = relationship("User", back_populates="job_descriptions")
    resumes = relationship("Resume", back_populates="job", cascade="all, delete-orphan")
    evaluations = relationship("CandidateEvaluation", back_populates="job", cascade="all, delete-orphan")


class CandidateEvaluation(Base):
    __tablename__ = "candidate_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"))
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"))
    hr_manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    suitability_score = Column(Float, nullable=False)
    comments = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="Pending")

    resume = relationship("Resume", back_populates="evaluation")
    job = relationship("JobDescription", back_populates="evaluations")
    hr_user = relationship("User", back_populates="evaluations")

