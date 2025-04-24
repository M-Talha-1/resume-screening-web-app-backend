from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas import JobDescriptionCreate, JobResponse
from app.database import get_db
from app.services import job_service
from typing import List

router = APIRouter()

@router.get("/job/", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    return job_service.get_all_jobs(db)

@router.post("/job/", response_model=JobResponse, status_code=201)
def create_job(job: JobDescriptionCreate, db: Session = Depends(get_db)):
    return job_service.create_job(job, db)

@router.put("/job/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job: JobDescriptionCreate, db: Session = Depends(get_db)):
    return job_service.update_job(job_id, job, db)

@router.delete("/job/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job_service.delete_job(job_id, db)
    return {"message": "Job deleted successfully!"}
