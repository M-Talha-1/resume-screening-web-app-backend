from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import JobDescription
from pydantic import BaseModel

router = APIRouter()

class JobDescriptionRequest(BaseModel):
    title: str
    description: str

@router.post("/create-job/")
def create_job(job: JobDescriptionRequest, db: Session = Depends(get_db)):
    new_job = JobDescription(
        title=job.title,
        description=job.description
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    return {"message": "Job added successfully!", "job_id": new_job.id}
