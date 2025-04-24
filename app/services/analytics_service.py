from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract, case
from datetime import datetime, timedelta
from app.models import JobDescription, Resume, Applicant, JobStatus, EvaluationStatus
from app.schemas import (
    AnalyticsResponse, JobAnalyticsResponse,
    SkillTrendsResponse, HiringTrendsResponse,
    DepartmentAnalyticsResponse
)
from typing import List, Dict, Any, Optional
from app.cache import get_cache, set_cache
from fastapi import HTTPException

def get_dashboard_analytics(db: Session) -> Dict[str, Any]:
    """Get overall analytics for the dashboard"""
    # Job statistics
    total_jobs = db.query(JobDescription).count()
    active_jobs = db.query(JobDescription).filter(JobDescription.status == JobStatus.OPEN).count()
    closed_jobs = db.query(JobDescription).filter(JobDescription.status == JobStatus.CLOSED).count()
    
    # Applicant statistics
    total_applicants = db.query(Resume).count()
    shortlisted = db.query(Resume).filter(Resume.status == "Shortlisted").count()
    rejected = db.query(Resume).filter(Resume.status == "Rejected").count()
    
    # Average processing time (in days)
    average_processing_time = 0.0
    
    # Top skills (using text_content for now)
    top_skills = []
    
    # Job status distribution
    job_status_dist = {
        JobStatus.OPEN.value: active_jobs,
        JobStatus.CLOSED.value: closed_jobs,
        JobStatus.FILLED.value: db.query(JobDescription).filter(JobDescription.status == JobStatus.FILLED).count(),
        JobStatus.DRAFT.value: db.query(JobDescription).filter(JobDescription.status == JobStatus.DRAFT).count()
    }
    
    # Applicant status distribution
    applicant_status_dist = {
        "Pending": db.query(Resume).filter(Resume.status == "Pending").count(),
        "Shortlisted": shortlisted,
        "Rejected": rejected
    }
    
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "closed_jobs": closed_jobs,
        "total_applicants": total_applicants,
        "shortlisted_applicants": shortlisted,
        "rejected_applicants": rejected,
        "average_processing_time": average_processing_time,
        "top_skills": top_skills,
        "job_status_distribution": job_status_dist,
        "applicant_status_distribution": applicant_status_dist
    }

def get_job_analytics(db: Session, job_id: int) -> Dict[str, Any]:
    """Get detailed analytics for a specific job"""
    job = db.query(JobDescription).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Basic statistics
    total_applicants = db.query(Resume).filter_by(job_description_id=job_id).count()
    shortlisted = db.query(Resume).filter_by(
        job_description_id=job_id,
        status="Shortlisted"
    ).count()
    rejected = db.query(Resume).filter_by(
        job_description_id=job_id,
        status="Rejected"
    ).count()
    
    return {
        "job_id": job_id,
        "title": job.title,
        "total_applicants": total_applicants,
        "shortlisted": shortlisted,
        "rejected": rejected,
        "average_score": 0.0,  # Placeholder
        "status_distribution": {
            "Pending": total_applicants - shortlisted - rejected,
            "Shortlisted": shortlisted,
            "Rejected": rejected
        },
        "skill_match_distribution": {},  # Placeholder
        "experience_distribution": {}  # Placeholder
    }

def get_skill_trends(db: Session) -> List[Dict[str, Any]]:
    """Get trending skills"""
    return [{
        "timeframe": "Last 30 days",
        "skills": []  # Placeholder
    }]

def get_hiring_trends(db: Session) -> List[Dict[str, Any]]:
    """Get hiring trends"""
    now = datetime.utcnow()
    return [{
        "start_date": now - timedelta(days=30),
        "end_date": now,
        "department": None,
        "trends": []  # Placeholder
    }]

def get_department_analytics(db: Session) -> List[Dict[str, Any]]:
    """Get analytics by department"""
    departments = db.query(JobDescription.department).distinct().all()
    analytics = []
    
    for dept in departments:
        if dept[0]:  # Skip null departments
            dept_jobs = db.query(JobDescription).filter_by(department=dept[0])
            analytics.append({
                "department": dept[0],
                "total_jobs": dept_jobs.count(),
                "open_jobs": dept_jobs.filter(JobDescription.status == JobStatus.OPEN).count(),
                "filled_jobs": dept_jobs.filter(JobDescription.status == JobStatus.FILLED).count(),
                "total_applicants": db.query(Resume).join(
                    JobDescription
                ).filter(JobDescription.department == dept[0]).count(),
                "avg_time_to_fill": 0.0  # Placeholder
            })
    
    return analytics

def get_applicant_metrics(
    db: Session,
    applicant_id: int
) -> dict:
    """
    Get detailed metrics for a specific applicant
    """
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    # Get all applications
    applications = db.query(Resume).filter(Resume.applicant_id == applicant_id).all()
    
    metrics = {
        "total_applications": len(applications),
        "shortlisted": sum(1 for app in applications if app.status == "Shortlisted"),
        "rejected": sum(1 for app in applications if app.status == "Rejected"),
        "average_score": sum(app.suitability_score for app in applications) / len(applications) if applications else 0,
        "application_timeline": [
            {
                "job_id": app.job_description_id,
                "date": app.upload_date,
                "status": app.status,
                "score": app.suitability_score
            }
            for app in applications
        ]
    }
    
    return metrics 