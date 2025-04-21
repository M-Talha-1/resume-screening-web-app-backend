from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import JobDescription

def get_all_jobs(db: Session):
    try:
        return db.query(JobDescription).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

def create_job(job_data, db: Session):
    try:
        new_job = JobDescription(
            title=job_data.title,
            description=job_data.description,
            status=job_data.status,
            admin_id=job_data.admin_id  # added this line
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        return new_job
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")

def update_job(job_id: int, job_data, db: Session):
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.title = job_data.title
        job.description = job_data.description
        job.status = job_data.status
        db.commit()
        db.refresh(job)
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating job: {str(e)}")

def delete_job(job_id: int, db: Session):
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        db.delete(job)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")
