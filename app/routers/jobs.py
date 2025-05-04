from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import logging

from app.database import get_db
from app.models import Job, User, Resume, CandidateEvaluation, JobStatus, EvaluationStatus, UserRole
from app.schemas import (
    JobCreate, JobResponse, JobSearchParams, JobAnalytics,
    CandidateEvaluationResponse, JobUpdate, CandidateEvaluationCreate
)
from app.auth import get_current_user
from app.services.matcher import JobMatcher

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])
matcher = JobMatcher()

@router.post("/", response_model=JobResponse)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate salary range
    if 'min' not in job.salary_range or 'max' not in job.salary_range:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Salary range must include 'min' and 'max' values"
        )
    if job.salary_range['min'] > job.salary_range['max']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum salary cannot be greater than maximum salary"
        )
    
    db_job = Job(
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        department=job.department,
        location=job.location,
        salary_range=job.salary_range,
        job_type=job.job_type,
        experience_required=job.experience_required,
        skills_required=job.skills_required,
        status=job.status,
        admin_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.get("/", response_model=List[JobResponse])
def get_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[JobStatus] = None,
    department: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    min_experience: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Job)
    
    if status:
        query = query.filter(Job.status == status)
    if department:
        query = query.filter(Job.department.ilike(f"%{department}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if job_type:
        query = query.filter(Job.job_type.ilike(f"%{job_type}%"))
    if min_experience is not None:
        query = query.filter(Job.experience_required >= min_experience)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job

@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Validate salary range if provided
    if job.salary_range:
        if 'min' not in job.salary_range or 'max' not in job.salary_range:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Salary range must include 'min' and 'max' values"
            )
        if job.salary_range['min'] > job.salary_range['max']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum salary cannot be greater than maximum salary"
            )
    
    update_data = job.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db_job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_job)
    return db_job

@router.patch("/{job_id}/status", response_model=JobResponse)
def update_job_status(
    job_id: int,
    status: JobStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job.status = status
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job

@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job posting"""
    try:
        # Check if job exists and belongs to current user
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.admin_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this job")
        
        # First delete all resumes associated with this job
        db.query(Resume).filter(Resume.job_id == job_id).delete()
        
        # Then delete the job
        db.delete(job)
        db.commit()
        
        return {"message": "Job deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting job: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting job")

@router.get("/{job_id}/analytics", response_model=JobAnalytics)
def get_job_analytics(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    evaluations = db.query(CandidateEvaluation).filter(
        CandidateEvaluation.job_id == job_id
    ).all()
    
    total_applicants = len(evaluations)
    if total_applicants == 0:
        return JobAnalytics(
            total_applicants=0,
            average_score=0.0,
            matching_skills_frequency={},
            status_distribution={status.value: 0 for status in EvaluationStatus},
            daily_applications={}
        )
    
    # Calculate average score
    average_score = sum(e.overall_score for e in evaluations) / total_applicants
    
    # Calculate matching skills frequency
    matching_skills_freq = {}
    for evaluation in evaluations:
        for skill in evaluation.matching_skills:
            matching_skills_freq[skill] = matching_skills_freq.get(skill, 0) + 1
    
    # Calculate status distribution
    status_dist = {status.value: 0 for status in EvaluationStatus}
    for evaluation in evaluations:
        status_dist[evaluation.status.value] += 1
    
    # Calculate daily applications
    daily_applications = {}
    for evaluation in evaluations:
        date = evaluation.evaluation_date.date().isoformat()
        daily_applications[date] = daily_applications.get(date, 0) + 1
    
    return JobAnalytics(
        total_applicants=total_applicants,
        average_score=average_score,
        matching_skills_frequency=matching_skills_freq,
        status_distribution=status_dist,
        daily_applications=daily_applications
    )

@router.get("/{job_id}/evaluations", response_model=List[CandidateEvaluationResponse])
def get_job_evaluations(
    job_id: int,
    status: Optional[EvaluationStatus] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    query = db.query(CandidateEvaluation).filter(
        CandidateEvaluation.job_id == job_id
    )
    
    if status:
        query = query.filter(CandidateEvaluation.status == status)
    if min_score is not None:
        query = query.filter(CandidateEvaluation.overall_score >= min_score)
    if max_score is not None:
        query = query.filter(CandidateEvaluation.overall_score <= max_score)
    
    return query.all()

@router.post("/{job_id}/evaluations", response_model=CandidateEvaluationResponse)
def create_evaluation(
    job_id: int,
    evaluation: CandidateEvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new evaluation for a resume"""
    try:
        # Validate job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Validate resume exists
        resume = db.query(Resume).filter(Resume.id == evaluation.resume_id).first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Create evaluation
        db_evaluation = CandidateEvaluation(
            resume_id=evaluation.resume_id,
            job_id=job_id,
            admin_id=current_user.id,
            overall_score=evaluation.overall_score,
            skill_match=evaluation.skill_match,
            experience_match=evaluation.experience_match,
            matching_skills=evaluation.matching_skills,
            comments=evaluation.comments,
            status=evaluation.status,
            evaluation_date=datetime.utcnow()
        )
        
        db.add(db_evaluation)
        db.commit()
        db.refresh(db_evaluation)
        
        return db_evaluation
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating evaluation"
        ) 