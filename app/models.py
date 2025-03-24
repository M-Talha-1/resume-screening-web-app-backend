from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base  

class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    skills = Column(JSON, nullable=True)  # Store skills as a list of strings instead of comma-separated
    designation = Column(String, nullable=True)
    total_experience = Column(Float, nullable=True)  # Store experience in years

    resumes = relationship("Resume", back_populates="applicant", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id", ondelete="CASCADE"))
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"))
    file_url = Column(String, nullable=False)
    text_content = Column(Text, nullable=True)

    applicant = relationship("Applicant", back_populates="resumes")
    job = relationship("JobDescription", back_populates="resumes")
    evaluation = relationship("CandidateEvaluation", back_populates="resume", cascade="all, delete-orphan") 

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="Open")  # Example statuses: "Open", "Closed", "Draft"
    skills = Column(JSON, nullable=True)  # Store required skills as a list
    location = Column(String, nullable=True)  # Job location
    date_created = Column(DateTime, server_default=func.now())

    resumes = relationship("Resume", back_populates="job", cascade="all, delete-orphan")
    evaluations = relationship("CandidateEvaluation", back_populates="job", cascade="all, delete-orphan")

class CandidateEvaluation(Base):
    __tablename__ = "candidate_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"))
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"))  
    score = Column(Float, nullable=False)  # Use Float instead of Integer for more precise scoring
    status = Column(String, nullable=False, default="Pending")  # e.g., "Accepted", "Rejected", "Pending"

    resume = relationship("Resume", back_populates="evaluation")
    job = relationship("JobDescription", back_populates="evaluations")
