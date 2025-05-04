from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text, case
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException
from app.models import Job, Resume, CandidateEvaluation, Applicant, JobStatus, EvaluationStatus
from app.schemas import JobDescriptionCreate, JobDescriptionResponse, JobSearchParams, JobAnalyticsResponse
from app.cache import get_cache, set_cache
from sqlalchemy.types import String

def get_all_jobs(db: Session) -> List[Job]:
    """Get all job descriptions"""
    jobs = db.query(Job).all()
    return jobs

def get_job_by_id(db: Session, job_id: int) -> Job:
    """Get a specific job description by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

def create_job(db: Session, job: JobDescriptionCreate) -> JobDescriptionResponse:
    """Create a new job posting"""
    db_job = Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_job(db: Session, job_id: int) -> JobDescriptionResponse:
    """Get a specific job by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    department: Optional[str] = None,
    location: Optional[str] = None
) -> List[JobDescriptionResponse]:
    """Get all jobs with optional filters"""
    query = db.query(Job)
    
    if status:
        query = query.filter(Job.status == status)
    if department:
        query = query.filter(Job.department == department)
    if location:
        query = query.filter(Job.location == location)
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs

def update_job(db: Session, job_id: int, job: JobDescriptionCreate) -> JobDescriptionResponse:
    """Update an existing job posting"""
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update job fields
    job_data = job.dict(exclude_unset=True)
    for key, value in job_data.items():
        if hasattr(db_job, key):
            setattr(db_job, key, value)
    
    try:
        db.commit()
        db.refresh(db_job)
        
        # Update cache
        cache_key = f"job_{job_id}"
        set_cache(cache_key, db_job)
        
        return db_job
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

def delete_job(db: Session, job_id: int):
    """Delete a job posting"""
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job:
        db.delete(db_job)
        db.commit()
        
        # Remove from cache
        cache_key = f"job_{job_id}"
        set_cache(cache_key, None)

def close_job(db: Session, job_id: int) -> JobDescriptionResponse:
    """Close a job posting"""
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        return None
    
    db_job.status = JobStatus.CLOSED
    db.commit()
    db.refresh(db_job)
    
    # Update cache
    cache_key = f"job_{job_id}"
    set_cache(cache_key, db_job)
    
    return db_job

def get_jobs_by_admin(admin_id: int, db: Session) -> List[Job]:
    """Get all jobs posted by a specific admin"""
    jobs = db.query(Job).filter(Job.admin_id == admin_id).all()
    return jobs

def update_job_status(job_id: int, status: JobStatus, db: Session) -> Job:
    """Update the status of a job"""
    job = get_job_by_id(db, job_id)
    if status not in JobStatus:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    job.status = status
    db.commit()
    db.refresh(job)
    return job

def get_job_applicants(
    db: Session,
    job_id: int,
    status: Optional[EvaluationStatus] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None
) -> List[CandidateEvaluation]:
    """Get all applicants for a specific job with optional filters"""
    query = db.query(CandidateEvaluation).filter(CandidateEvaluation.job_id == job_id)
    
    if status:
        query = query.filter(CandidateEvaluation.status == status)
    if min_score is not None:
        query = query.filter(CandidateEvaluation.overall_score >= min_score)
    if max_score is not None:
        query = query.filter(CandidateEvaluation.overall_score <= max_score)
    
    return query.all()

def update_applicant_status(
    db: Session,
    job_id: int,
    applicant_id: int,
    status: EvaluationStatus,
    notes: Optional[str] = None
) -> CandidateEvaluation:
    """Update the status of an applicant for a specific job"""
    evaluation = db.query(CandidateEvaluation).filter(
        CandidateEvaluation.job_id == job_id,
        CandidateEvaluation.resume_id == applicant_id
    ).first()
    
    if not evaluation:
        return None
    
    evaluation.status = status
    if notes:
        evaluation.comments = notes
    evaluation.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(evaluation)
    return evaluation

def get_job_statistics(db: Session, job_id: int) -> dict:
    """Get statistics for a specific job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return None
    
    total_applicants = db.query(func.count(Resume.id)).filter(Resume.job_id == job_id).scalar()
    total_shortlisted = db.query(func.count(CandidateEvaluation.id)).filter(
        CandidateEvaluation.job_id == job_id,
        CandidateEvaluation.status == EvaluationStatus.SHORTLISTED
    ).scalar()
    total_rejected = db.query(func.count(CandidateEvaluation.id)).filter(
        CandidateEvaluation.job_id == job_id,
        CandidateEvaluation.status == EvaluationStatus.REJECTED
    ).scalar()
    
    stats = {
        "total_applicants": total_applicants,
        "total_shortlisted": total_shortlisted,
        "total_rejected": total_rejected,
        "average_score": db.query(func.avg(CandidateEvaluation.overall_score))
            .filter(CandidateEvaluation.job_id == job_id)
            .scalar() or 0,
        "status_distribution": dict(
            db.query(CandidateEvaluation.status, func.count(CandidateEvaluation.id))
            .filter(CandidateEvaluation.job_id == job_id)
            .group_by(CandidateEvaluation.status)
            .all()
        )
    }
    
    return stats

def search_jobs(
    db: Session,
    search_params: JobSearchParams,
    skip: int = 0,
    limit: int = 100
) -> List[Job]:
    """
    Advanced search for jobs with multiple filters
    """
    query = db.query(Job)
    
    # Full-text search
    if search_params.query:
        query = query.filter(
            or_(
                Job.title.ilike(f"%{search_params.query}%"),
                Job.description.ilike(f"%{search_params.query}%"),
                Job.required_skills.cast(String).ilike(f"%{search_params.query}%")
            )
        )
    
    # Skills filter
    if search_params.skills:
        for skill in search_params.skills:
            query = query.filter(
                Job.required_skills.cast(String).ilike(f"%{skill}%")
            )
    
    # Experience range
    if search_params.min_experience is not None:
        query = query.filter(Job.experience_required >= search_params.min_experience)
    if search_params.max_experience is not None:
        query = query.filter(Job.experience_required <= search_params.max_experience)
    
    # Salary range
    if search_params.min_salary is not None:
        query = query.filter(Job.salary_range_min >= search_params.min_salary)
    if search_params.max_salary is not None:
        query = query.filter(Job.salary_range_max <= search_params.max_salary)
    
    # Additional filters
    if search_params.job_type:
        query = query.filter(Job.job_type == search_params.job_type)
    if search_params.location:
        query = query.filter(Job.location == search_params.location)
    if search_params.department:
        query = query.filter(Job.department == search_params.department)
    if search_params.status:
        query = query.filter(Job.status == search_params.status)
    
    # Sort by most recent first
    query = query.order_by(Job.posted_date.desc())
    
    return query.offset(skip).limit(limit).all()

def get_job_recommendations(
    db: Session,
    applicant_id: int,
    limit: int = 5
) -> List[Job]:
    """
    Get job recommendations based on applicant's profile
    """
    # Get applicant's skills and experience
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    # Base query
    query = db.query(Job)
    
    # Match skills
    if applicant.skills:
        for skill in applicant.skills:
            query = query.filter(
                func.jsonb_array_elements(Job.required_skills).cast(text).ilike(f"%{skill}%")
            )
    
    # Match experience
    if applicant.total_experience:
        query = query.filter(
            Job.experience_required <= applicant.total_experience
        )
    
    # Match location if available
    if applicant.current_location:
        query = query.filter(
            Job.location == applicant.current_location
        )
    
    # Only show open jobs
    query = query.filter(Job.status == JobStatus.OPEN)
    
    # Sort by relevance (number of matching skills)
    query = query.order_by(
        func.array_length(Job.required_skills, 1).desc()
    )
    
    return query.limit(limit).all()

def get_job_metrics(
    db: Session,
    job_id: int
) -> dict:
    """
    Get detailed metrics for a specific job
    """
    job = get_job(db, job_id)
    
    # Basic metrics
    metrics = {
        "total_applicants": job.total_applicants,
        "shortlisted": job.total_shortlisted,
        "rejected": job.total_rejected,
        "average_score": db.query(func.avg(CandidateEvaluation.overall_score))
            .filter(CandidateEvaluation.job_id == job_id)
            .scalar() or 0,
        "status": job.status,
        "days_open": None,
        "avg_time_to_first_review": None,
        "skill_match_distribution": {}
    }
    
    # Time-based metrics
    if job.posted_date:
        metrics["days_open"] = (datetime.utcnow() - job.posted_date).days
        
        # Average time to first review
        first_reviews = db.query(
            func.min(CandidateEvaluation.evaluation_date) - Resume.upload_date
        ).join(
            Resume, CandidateEvaluation.resume_id == Resume.id
        ).filter(
            CandidateEvaluation.job_id == job_id
        ).scalar()
        
        if first_reviews:
            metrics["avg_time_to_first_review"] = first_reviews.days
    
    # Skill match distribution
    skill_matches = db.query(
        func.floor(CandidateEvaluation.overall_score / 20) * 20,
        func.count(CandidateEvaluation.id)
    ).filter(
        CandidateEvaluation.job_id == job_id
    ).group_by(
        func.floor(CandidateEvaluation.overall_score / 20)
    ).all()
    
    metrics["skill_match_distribution"] = {
        f"{int(score)}-{int(score+20)}": count
        for score, count in skill_matches
    }
    
    return metrics

def get_job_analytics(db: Session, job_id: int) -> JobAnalyticsResponse:
    """Get detailed analytics for a specific job"""
    cache_key = f"job_analytics_{job_id}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data

    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        return None
    
    # Basic statistics
    total_applicants = db.query(CandidateEvaluation).filter_by(job_id=job_id).count()
    shortlisted = db.query(CandidateEvaluation).filter_by(
        job_id=job_id,
        status=EvaluationStatus.SHORTLISTED
    ).count()
    rejected = db.query(CandidateEvaluation).filter_by(
        job_id=job_id,
        status=EvaluationStatus.REJECTED
    ).count()
    
    # Average overall score
    avg_score = db.query(
        func.avg(CandidateEvaluation.overall_score)
    ).filter_by(job_id=job_id).scalar() or 0
    
    # Status distribution
    status_dist = dict(
        db.query(CandidateEvaluation.status, func.count(CandidateEvaluation.id))
        .filter_by(job_id=job_id)
        .group_by(CandidateEvaluation.status)
        .all()
    )
    
    # Skill match distribution
    score_ranges = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    skill_match_dist = {}
    for low, high in score_ranges:
        count = db.query(CandidateEvaluation).filter(
            CandidateEvaluation.job_id == job_id,
            CandidateEvaluation.overall_score >= low,
            CandidateEvaluation.overall_score < high
        ).count()
        skill_match_dist[f"{low}-{high}"] = count
    
    # Experience distribution
    exp_ranges = [(0, 2), (2, 5), (5, 10), (10, float('inf'))]
    exp_dist = {}
    for low, high in exp_ranges:
        count = db.query(Applicant).join(Resume).join(CandidateEvaluation).filter(
            CandidateEvaluation.job_id == job_id,
            Applicant.total_experience >= low,
            Applicant.total_experience < high
        ).count()
        exp_dist[f"{low}-{high if high != float('inf') else '+'} years"] = count
    
    analytics = {
        "job_id": job_id,
        "title": job.title,
        "description": job.description,
        "required_skills": job.required_skills,
        "posted_date": job.posted_date,
        "status": job.status,
        "location": job.location,
        "department": job.department,
        "experience_required": job.experience_required,
        "salary_range_min": job.salary_range_min,
        "salary_range_max": job.salary_range_max,
        "job_type": job.job_type,
        "total_applicants": total_applicants,
        "shortlisted": shortlisted,
        "rejected": rejected,
        "average_score": avg_score,
        "status_distribution": status_dist,
        "skill_match_distribution": skill_match_dist,
        "experience_distribution": exp_dist
    }

    # Cache for 5 minutes
    set_cache(cache_key, analytics, ttl=300)
    return analytics