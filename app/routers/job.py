from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import JobDescription
from pydantic import BaseModel
from typing import List
from datetime import datetime


router = APIRouter()

class JobDescriptionRequest(BaseModel):
    title: str
    description: str
    status: str  # "Open" or "Closed"
    
class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    date_created: datetime

# ✅ Fetch all jobs
@router.get("/job/", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(JobDescription).all()
    return jobs

# ✅ Create a new job
@router.post("/job/")
def create_job(job: JobDescriptionRequest, db: Session = Depends(get_db)):
    new_job = JobDescription(
        title=job.title,
        description=job.description,
        status=job.status
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return {"message": "Job added successfully!", "job_id": new_job.id}

# ✅ Update a job
@router.put("/job/{job_id}")
def update_job(job_id: int, job: JobDescriptionRequest, db: Session = Depends(get_db)):
    job_entry = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job_entry:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_entry.title = job.title
    job_entry.description = job.description
    job_entry.status = job.status
    db.commit()
    return {"message": "Job updated successfully!"}

# ✅ Delete a job
@router.delete("/job/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job_entry = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job_entry:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job_entry)
    db.commit()
    return {"message": "Job deleted successfully!"}
