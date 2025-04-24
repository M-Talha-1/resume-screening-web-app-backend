from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.analytics_service import (
    get_dashboard_analytics, get_job_analytics,
    get_skill_trends, get_hiring_trends,
    get_department_analytics
)
from app.schemas import (
    AnalyticsResponse, JobAnalyticsResponse,
    SkillTrendsResponse, HiringTrendsResponse,
    DepartmentAnalyticsResponse
)
from app.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

@router.get("/dashboard")
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get overall analytics for the dashboard
    """
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to view analytics")
    
    return get_dashboard_analytics(db)

@router.get("/jobs/{job_id}")
async def get_job_analytics_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get detailed analytics for a specific job
    """
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to view job analytics")
    
    return get_job_analytics(db, job_id)

@router.get("/skills")
async def get_skill_trends_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get trending skills
    """
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to view skill trends")
    
    return get_skill_trends(db)

@router.get("/hiring")
async def get_hiring_trends_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get hiring trends
    """
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to view hiring trends")
    
    return get_hiring_trends(db)

@router.get("/departments")
async def get_department_analytics_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get analytics by department
    """
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to view department analytics")
    
    return get_department_analytics(db) 