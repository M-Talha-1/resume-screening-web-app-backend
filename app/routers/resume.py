from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Resume, Applicant, JobDescription
from app.services.resume_parser import extract_resume_data
from app.services.save_file import save_resume
from app.schemas import ResumeResponse
import os

router = APIRouter(
    prefix="/resumes",
    tags=["resumes"]
)

@router.post("/", response_model=ResumeResponse, status_code=201)
def upload_resume(
    file: UploadFile = File(...),
    job_description_id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        job = db.query(JobDescription).filter_by(id=job_description_id).first()
        if not job:
            raise HTTPException(status_code=400, detail="Invalid job ID")

        file_path = save_resume(file)
        parsed_data = extract_resume_data(file_path)

        if not parsed_data:
            raise HTTPException(status_code=400, detail="Resume parsing failed")

        applicant = db.query(Applicant).filter_by(email=parsed_data["email"]).first()
        if not applicant:
            applicant = Applicant(
                name=parsed_data["name"],
                email=parsed_data["email"],
                phone=parsed_data.get("mobile_number"),
                skills=parsed_data.get("skills", []),
                designation=parsed_data.get("designation"),
                total_experience=parsed_data.get("total_experience", 0.0)
            )
            db.add(applicant)
            db.commit()
            db.refresh(applicant)

        existing_resume = db.query(Resume).filter_by(applicant_id=applicant.id, job_description_id=job_description_id).first()
        if existing_resume:
            # Clean up the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail="Resume already submitted for this job")

        db_resume = Resume(
            applicant_id=applicant.id,
            job_description_id=job_description_id,
            file_path=file_path,
            text_content=parsed_data["raw_text"],
            parsed_status="Parsed",
            file_type=file.filename.split(".")[-1],
            file_size=os.path.getsize(file_path)
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)

        return db_resume

    except HTTPException:
        raise
    except Exception as e:
        # Clean up the uploaded file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
