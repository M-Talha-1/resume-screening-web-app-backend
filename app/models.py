from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.database import Base  # Import Base to define models

class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)

    resumes = relationship("Resume", back_populates="applicant")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"))
    file_url = Column(String, nullable=False)
    text_content = Column(Text, nullable=True)  # Parsed text from resume

    applicant = relationship("Applicant", back_populates="resumes")

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

class CandidateEvaluation(Base):
    __tablename__ = "candidate_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"))
    score = Column(Integer, nullable=False)  # Score based on NLP matching
    status = Column(String, nullable=False)  # e.g., "Accepted", "Rejected"

    resume = relationship("Resume")
    job_description = relationship("JobDescription")
