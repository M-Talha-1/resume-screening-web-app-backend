from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False, default="Applicant")
    date_created = Column(DateTime, server_default=func.now())

    resumes = relationship("Resume", back_populates="applicant", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id", ondelete="CASCADE"))
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"))  # ✅ Correct FK
    file_path = Column(String, nullable=False)
    upload_date = Column(DateTime, server_default=func.now())
    parsed_status = Column(String, default="Pending")

    applicant = relationship("Applicant", back_populates="resumes")
    job = relationship("JobDescription", back_populates="resumes")  # ✅ Linked correctly
    evaluation = relationship("CandidateEvaluation", back_populates="resume", cascade="all, delete-orphan")

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id", ondelete="SET NULL"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True)
    posted_date = Column(DateTime, server_default=func.now())
    status = Column(String, nullable=False, default="Open")

    admin = relationship("Admin", back_populates="job_descriptions")
    resumes = relationship("Resume", back_populates="job", cascade="all, delete-orphan")  # ✅ Matches Resume.job
    evaluations = relationship("CandidateEvaluation", back_populates="job", cascade="all, delete-orphan")


class CandidateEvaluation(Base):
    __tablename__ = "candidate_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"))
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"))
    hr_manager_id = Column(Integer, ForeignKey("hr_managers.id", ondelete="SET NULL"), nullable=True)
    suitability_score = Column(Float, nullable=False)
    comments = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="Pending")

    resume = relationship("Resume", back_populates="evaluation")
    job = relationship("JobDescription", back_populates="evaluations")
    hr_manager = relationship("HRManager")

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False, default="Admin")

    jobs = relationship("JobDescription", backref="admin")

class HRManager(Base):
    __tablename__ = "hr_managers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False, default="HR Manager")

    evaluations = relationship("CandidateEvaluation", backref="hr_manager")
