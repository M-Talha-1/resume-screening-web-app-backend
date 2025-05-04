from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract, case
from datetime import datetime, timedelta
from app.models import Job, Resume, Applicant, JobStatus, EvaluationStatus, CandidateEvaluation
from app.schemas import (
    AnalyticsResponse, JobAnalyticsResponse,
    SkillTrendsResponse, HiringTrendsResponse,
    DepartmentAnalyticsResponse
)
from typing import List, Dict, Any, Optional
from app.cache import get_cache, set_cache
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def get_dashboard_analytics(db: Session) -> Dict[str, Any]:
    """Get dashboard analytics"""
    # Get total jobs count
    total_jobs = db.query(Job).count()
    
    # Get job status distribution - only use valid statuses
    valid_statuses = [JobStatus.DRAFT, JobStatus.OPEN, JobStatus.CLOSED]
    job_status_dist = {
        status.value: db.query(Job).filter(Job.status == status).count()
        for status in valid_statuses
    }
    
    # Get department analytics
    department_analytics = get_department_analytics(db)
    
    # Get skills analytics
    skills_analytics = get_skills_analytics(db)
    
    return {
        "total_jobs": total_jobs,
        "job_status_distribution": job_status_dist,
        "department_analytics": department_analytics,
        "skills_analytics": skills_analytics
    }

def get_job_analytics(job_id: int, db: Session) -> Dict:
    """Get analytics for a specific job"""
    try:
        # Get job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get evaluations
        evaluations = db.query(CandidateEvaluation).filter(
            CandidateEvaluation.job_id == job_id
        ).all()
        
        if not evaluations:
            return {
                "job_id": job_id,
                "total_evaluations": 0,
                "average_score": 0,
                "score_distribution": [],
                "skill_match_distribution": [],
                "experience_match_distribution": []
            }
        
        # Calculate statistics
        total_evaluations = len(evaluations)
        average_score = sum(e.overall_score for e in evaluations) / total_evaluations
        
        # Score distribution
        score_ranges = [(0, 20), (21, 40), (41, 60), (61, 80), (81, 100)]
        score_distribution = []
        for min_score, max_score in score_ranges:
            count = sum(1 for e in evaluations if min_score <= e.overall_score <= max_score)
            score_distribution.append({
                "range": f"{min_score}-{max_score}",
                "count": count,
                "percentage": (count / total_evaluations) * 100
            })
        
        # Skill match distribution
        skill_match_ranges = [(0, 0.2), (0.21, 0.4), (0.41, 0.6), (0.61, 0.8), (0.81, 1.0)]
        skill_match_distribution = []
        for min_match, max_match in skill_match_ranges:
            count = sum(1 for e in evaluations if min_match <= e.skill_match <= max_match)
            skill_match_distribution.append({
                "range": f"{min_match}-{max_match}",
                "count": count,
                "percentage": (count / total_evaluations) * 100
            })
        
        # Experience match distribution
        experience_match_ranges = [(0, 0.2), (0.21, 0.4), (0.41, 0.6), (0.61, 0.8), (0.81, 1.0)]
        experience_match_distribution = []
        for min_match, max_match in experience_match_ranges:
            count = sum(1 for e in evaluations if min_match <= e.experience_match <= max_match)
            experience_match_distribution.append({
                "range": f"{min_match}-{max_match}",
                "count": count,
                "percentage": (count / total_evaluations) * 100
            })
        
        return {
            "job_id": job_id,
            "total_evaluations": total_evaluations,
            "average_score": average_score,
            "score_distribution": score_distribution,
            "skill_match_distribution": skill_match_distribution,
            "experience_match_distribution": experience_match_distribution
        }
    except Exception as e:
        logger.error(f"Error getting job analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting job analytics")

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
    departments = db.query(Job.department).distinct().all()
    analytics = []
    
    for dept in departments:
        if dept[0]:  # Skip null departments
            dept_jobs = db.query(Job).filter(Job.department == dept[0])
            analytics.append({
                "department": dept[0],
                "total_jobs": dept_jobs.count(),
                "open_jobs": dept_jobs.filter(Job.status == JobStatus.OPEN).count(),
                "closed_jobs": dept_jobs.filter(Job.status == JobStatus.CLOSED).count(),
                "total_applicants": db.query(Resume).join(
                    Job
                ).filter(Job.department == dept[0]).count(),
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
        "shortlisted": sum(1 for app in applications if any(e.status == EvaluationStatus.SHORTLISTED for e in app.evaluations)),
        "rejected": sum(1 for app in applications if any(e.status == EvaluationStatus.REJECTED for e in app.evaluations)),
        "average_score": sum(e.suitability_score for app in applications for e in app.evaluations) / len(applications) if applications else 0,
        "application_timeline": [
            {
                "job_id": app.job_id,
                "date": app.created_at,
                "status": app.evaluations[0].status if app.evaluations else None,
                "score": app.evaluations[0].suitability_score if app.evaluations else None
            }
            for app in applications
        ]
    }
    
    return metrics

def get_skills_analytics(db: Session) -> Dict[str, Any]:
    """Get skills analytics"""
    try:
        # Get all skills from jobs
        job_skills = []
        for job in db.query(Job).all():
            if job.skills_required:
                job_skills.extend(job.skills_required)
        
        # Get all skills from resumes
        resume_skills = []
        for resume in db.query(Resume).all():
            if resume.extracted_skills:
                resume_skills.extend(resume.extracted_skills)
        
        # Count skill occurrences
        job_skill_counts = {}
        for skill in job_skills:
            job_skill_counts[skill] = job_skill_counts.get(skill, 0) + 1
        
        resume_skill_counts = {}
        for skill in resume_skills:
            resume_skill_counts[skill] = resume_skill_counts.get(skill, 0) + 1
        
        # Get top skills
        top_job_skills = sorted(job_skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_resume_skills = sorted(resume_skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "top_job_skills": [{"skill": skill, "count": count} for skill, count in top_job_skills],
            "top_resume_skills": [{"skill": skill, "count": count} for skill, count in top_resume_skills],
            "total_unique_skills": len(set(job_skills + resume_skills))
        }
    except Exception as e:
        logger.error(f"Error getting skills analytics: {str(e)}")
        return {
            "top_job_skills": [],
            "top_resume_skills": [],
            "total_unique_skills": 0
        } 