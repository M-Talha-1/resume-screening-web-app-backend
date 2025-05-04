from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import re
from collections import Counter
from fastapi import status
import logging

from app.database import get_db
from app.models import CandidateEvaluation, Resume, Job, User
from app.schemas import (
    CandidateEvaluationCreate,
    CandidateEvaluationUpdate,
    CandidateEvaluationResponse,
    EvaluateRequest
)
from app.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/screening",
    tags=["screening"]
)

def calculate_suitability_score(resume_text: str, job_requirements: dict) -> float:
    """
    Calculate suitability score based on resume text and job requirements
    """
    score = 0
    total_weight = 0
    
    # Extract skills from resume text (simple keyword matching)
    resume_skills = set(re.findall(r'\b\w+\b', resume_text.lower()))
    
    # Compare required skills
    if job_requirements.get('required_skills'):
        required_skills = set(skill.lower() for skill in job_requirements['required_skills'])
        matching_skills = resume_skills.intersection(required_skills)
        skill_score = len(matching_skills) / len(required_skills) if required_skills else 0
        score += skill_score * 0.4  # 40% weight for skills
        total_weight += 0.4
    
    # Compare experience
    if job_requirements.get('experience_required'):
        # Extract experience from resume (simple pattern matching)
        experience_pattern = r'(\d+)\s*(?:years|yrs|year)'
        experience_matches = re.findall(experience_pattern, resume_text.lower())
        resume_experience = max([float(exp) for exp in experience_matches]) if experience_matches else 0
        
        required_experience = job_requirements['experience_required']
        if resume_experience >= required_experience:
            exp_score = 1.0
        else:
            exp_score = resume_experience / required_experience
        score += exp_score * 0.3  # 30% weight for experience
        total_weight += 0.3
    
    # Compare location
    if job_requirements.get('location'):
        job_location = job_requirements['location'].lower()
        if job_location in resume_text.lower():
            score += 0.2  # 20% weight for location
            total_weight += 0.2
    
    # Normalize score
    if total_weight > 0:
        score = (score / total_weight) * 100
    else:
        score = 0
    
    return round(score, 2)

@router.post("/", response_model=CandidateEvaluationResponse, status_code=status.HTTP_201_CREATED)
def create_screening_result(
    screening: CandidateEvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if resume exists
    resume = db.query(Resume).filter(Resume.id == screening.resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Check if job exists
    job = db.query(Job).filter(Job.id == screening.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check if screening result already exists
    existing_screening = db.query(CandidateEvaluation).filter(
        CandidateEvaluation.resume_id == screening.resume_id,
        CandidateEvaluation.job_id == screening.job_id
    ).first()
    if existing_screening:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Screening result already exists for this resume and job")

    # Create new screening result with evaluation timing
    evaluation_start = datetime.utcnow()
    db_screening = CandidateEvaluation(
        **screening.dict(),
        admin_id=current_user.id,
        evaluation_date=datetime.utcnow(),
        evaluation_start_time=evaluation_start
    )
    db.add(db_screening)
    db.commit()
    db.refresh(db_screening)
    
    # Calculate and update evaluation duration
    evaluation_end = datetime.utcnow()
    duration_minutes = (evaluation_end - evaluation_start).total_seconds() / 60
    db_screening.evaluation_duration = duration_minutes
    db.commit()
    db.refresh(db_screening)
    
    return db_screening

@router.get("/{screening_id}", response_model=CandidateEvaluationResponse)
def get_screening_result(
    screening_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    screening = db.query(CandidateEvaluation).filter(CandidateEvaluation.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening result not found")
    return screening

@router.put("/{screening_id}", response_model=CandidateEvaluationResponse)
def update_screening_result(
    screening_id: int,
    screening_update: CandidateEvaluationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    screening = db.query(CandidateEvaluation).filter(CandidateEvaluation.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening result not found")

    # Update screening result
    for field, value in screening_update.dict(exclude_unset=True).items():
        setattr(screening, field, value)
    screening.last_updated = datetime.utcnow()

    # Update evaluation duration if it's a new evaluation
    if screening.evaluation_start_time:
        evaluation_end = datetime.utcnow()
        duration_minutes = (evaluation_end - screening.evaluation_start_time).total_seconds() / 60
        screening.evaluation_duration = duration_minutes

    db.commit()
    db.refresh(screening)
    return screening

@router.get("/resume/{resume_id}", response_model=List[CandidateEvaluationResponse])
def get_screening_results_by_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if resume exists
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Get all screening results for the resume
    screenings = db.query(CandidateEvaluation).filter(
        CandidateEvaluation.resume_id == resume_id
    ).all()
    return screenings

@router.get("/job/{job_id}", response_model=List[CandidateEvaluationResponse])
def get_screening_results_by_job(
    job_id: int,
    status: Optional[str] = None,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Build query
    query = db.query(CandidateEvaluation).filter(CandidateEvaluation.job_id == job_id)

    # Apply filters
    if status:
        query = query.filter(CandidateEvaluation.status == status)
    if min_score is not None:
        query = query.filter(CandidateEvaluation.overall_score >= min_score)
    if max_score is not None:
        query = query.filter(CandidateEvaluation.overall_score <= max_score)

    return query.all()

@router.post("/evaluate", response_model=CandidateEvaluationResponse, status_code=status.HTTP_201_CREATED)
def evaluate_resume(
    request: EvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get resume and job
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Calculate scores
    result = evaluate_candidate(job, resume)

    # Create evaluation
    evaluation = CandidateEvaluation(
        resume_id=request.resume_id,
        job_id=request.job_id,
        admin_id=current_user.id,
        overall_score=result.overall_score,
        skill_match=result.skill_match,
        experience_match=result.experience_match,
        matching_skills=result.matching_skills,
        comments=f"Automated evaluation based on skill match ({result.overall_score:.2f})",
        status="Rejected" if result.overall_score < 0.5 else "Shortlisted",
        evaluation_date=datetime.utcnow()
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return evaluation

@router.delete("/{screening_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_screening_result(
    screening_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    screening = db.query(CandidateEvaluation).filter(CandidateEvaluation.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening result not found")

    db.delete(screening)
    db.commit() 