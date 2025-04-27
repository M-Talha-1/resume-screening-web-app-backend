from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import re
from collections import Counter
from fastapi import status
import logging

from app.database import get_db
from app.models import CandidateEvaluation, Resume, JobDescription, User
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
    # Check if user is authorized
    if current_user.role != "hr_manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only HR managers can create screening results")

    # Check if resume exists
    resume = db.query(Resume).filter(Resume.id == screening.resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Check if job exists
    job = db.query(JobDescription).filter(JobDescription.id == screening.job_id).first()
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
        hr_manager_id=current_user.id,
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
    # Check if user is authorized
    if current_user.role != "hr_manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only HR managers can update screening results")

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
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Build query
    query = db.query(CandidateEvaluation).filter(CandidateEvaluation.job_id == job_id)

    # Apply filters
    if status:
        query = query.filter(CandidateEvaluation.status == status)
    if min_score is not None:
        query = query.filter(CandidateEvaluation.suitability_score >= min_score)
    if max_score is not None:
        query = query.filter(CandidateEvaluation.suitability_score <= max_score)

    screenings = query.all()
    return screenings

@router.post("/evaluate", response_model=CandidateEvaluationResponse, status_code=status.HTTP_201_CREATED)
def evaluate_resume(
    request: EvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Automatically evaluate a resume against job requirements and store the result
    """
    try:
        logger.info(f"Starting evaluation for resume {request.resume_id} and job {request.job_id}")
        
        # Check if user is authorized
        if current_user.role != "hr_manager":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only HR managers can evaluate resumes")

        # Get resume and job data
        resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
        if not resume:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
        
        job = db.query(JobDescription).filter(JobDescription.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        logger.info(f"Found resume and job. Resume text: {resume.text_content}")
        logger.info(f"Job requirements: {job.required_skills}, {job.experience_required}, {job.location}")

        # Check if evaluation already exists
        existing_evaluation = db.query(CandidateEvaluation).filter(
            CandidateEvaluation.resume_id == request.resume_id,
            CandidateEvaluation.job_id == request.job_id
        ).first()
        if existing_evaluation:
            logger.warning(f"Evaluation already exists for resume {request.resume_id} and job {request.job_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Evaluation already exists for this resume and job"
            )

        # Calculate suitability score
        job_requirements = {
            'required_skills': job.required_skills,
            'experience_required': job.experience_required,
            'location': job.location
        }
        
        suitability_score = calculate_suitability_score(resume.text_content or "", job_requirements)
        logger.info(f"Calculated suitability score: {suitability_score}")
        
        # Determine status based on score
        if suitability_score >= 80:
            status_val = "Shortlisted"
        elif suitability_score >= 60:
            status_val = "Pending Review"
        else:
            status_val = "Rejected"

        logger.info(f"Determined status: {status_val}")

        # Create evaluation record
        evaluation = CandidateEvaluation(
            resume_id=request.resume_id,
            job_id=request.job_id,
            hr_manager_id=current_user.id,
            suitability_score=suitability_score,
            comments=f"Automated evaluation based on skill match ({suitability_score}%)",
            status=status_val,
            evaluation_date=datetime.utcnow()
        )
        
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        logger.info("Successfully created evaluation")
        return evaluation
        
    except HTTPException as he:
        logger.warning(f"HTTP exception during evaluation: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during evaluation: {str(e)}"
        )

@router.delete("/{screening_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_screening_result(
    screening_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is authorized
    if current_user.role != "hr_manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only HR managers can delete screening results")

    screening = db.query(CandidateEvaluation).filter(CandidateEvaluation.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening result not found")

    db.delete(screening)
    db.commit()
    return None 