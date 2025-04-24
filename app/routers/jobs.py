from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.job_service import (
    create_job, get_job, get_jobs, update_job, delete_job,
    close_job, get_job_applicants, update_applicant_status,
    get_job_statistics, search_jobs, get_job_analytics
)
from app.schemas import (
    JobDescriptionCreate, JobDescriptionResponse, JobStatus,
    CandidateEvaluationResponse, JobAnalyticsResponse, JobSearchParams
)
from app.auth import get_current_user

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.post("/", response_model=JobDescriptionResponse, status_code=201)
async def create_job_endpoint(
    job: JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new job posting
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create jobs")
    
    # Add the current user's ID to the job data
    job_data = job.dict()
    job_data["admin_id"] = current_user.id
    
    return create_job(db, JobDescriptionCreate(**job_data))

@router.get("/", response_model=List[JobDescriptionResponse])
async def get_jobs_endpoint(
    skip: int = 0,
    limit: int = 100,
    status: Optional[JobStatus] = None,
    department: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all jobs with optional filters
    """
    return get_jobs(db, skip, limit, status, department, location)

@router.get("/search", response_model=List[JobDescriptionResponse])
async def search_jobs_endpoint(
    query: Optional[str] = None,
    skills: Optional[str] = None,
    min_experience: Optional[float] = None,
    max_experience: Optional[float] = None,
    min_salary: Optional[float] = None,
    max_salary: Optional[float] = None,
    job_type: Optional[str] = None,
    location: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[JobStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Search jobs with various filters
    """
    search_params = JobSearchParams(
        query=query,
        skills=skills.split(',') if skills else None,
        min_experience=min_experience,
        max_experience=max_experience,
        min_salary=min_salary,
        max_salary=max_salary,
        job_type=job_type,
        location=location,
        department=department,
        status=status
    )
    return search_jobs(db, search_params, skip, limit)

@router.get("/{job_id}", response_model=JobDescriptionResponse)
async def get_job_endpoint(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific job by ID
    """
    return get_job(db, job_id)

@router.put("/{job_id}", response_model=JobDescriptionResponse)
async def update_job_endpoint(
    job_id: int,
    job: JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update an existing job posting
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update jobs")
    
    return update_job(db, job_id, job)

@router.delete("/{job_id}")
async def delete_job_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a job posting
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete jobs")
    
    delete_job(db, job_id)
    return {"message": "Job deleted successfully"}

@router.post("/{job_id}/close", response_model=JobDescriptionResponse, status_code=201)
async def close_job_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Close a job posting
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can close jobs")
    
    return close_job(db, job_id)

@router.get("/{job_id}/applicants", response_model=List[CandidateEvaluationResponse])
async def get_job_applicants_endpoint(
    job_id: int,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all applicants for a specific job with optional filters
    """
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to view applicants")
    
    return get_job_applicants(db, job_id, status, min_score, max_score)

@router.put("/{job_id}/applicants/{applicant_id}")
async def update_applicant_status_endpoint(
    job_id: int,
    applicant_id: int,
    status: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update the status of an applicant for a specific job
    """
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to update applicant status")
    
    return update_applicant_status(db, job_id, applicant_id, status, notes)

@router.get("/{job_id}/analytics", response_model=JobAnalyticsResponse)
async def get_job_analytics_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get analytics for a specific job
    """
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to view job analytics")
    
    return get_job_analytics(db, job_id) 