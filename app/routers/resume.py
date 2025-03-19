from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Resume, Applicant, JobDescription
from app.services.resume_parser import extract_resume_data  # Your custom parser
from app.services.file_service import save_resume  # Import file handling function

router = APIRouter()

@router.post("/upload-resume/")
def upload_resume(
    file: UploadFile = File(...),
    job_id: int = Form(...),  # Get job_id from form data
    db: Session = Depends(get_db)
):
    try:
        # Validate job_id
        job = db.query(JobDescription).filter_by(id=job_id).first()
        if not job:
            raise HTTPException(status_code=400, detail="Invalid job ID")

        # Save the file using file_service.py
        file_path = save_resume(file)

        # Extract resume data
        parsed_data = extract_resume_data(file_path)

        if not parsed_data:
            raise HTTPException(status_code=400, detail="Failed to extract resume data")

        # Check if applicant exists
        applicant = db.query(Applicant).filter_by(email=parsed_data["email"]).first()
        if not applicant:
            applicant = Applicant(
                name=parsed_data["name"],
                email=parsed_data["email"],
                phone=parsed_data["mobile_number"],
                skills=",".join(parsed_data.get("skills", [])),  # Store as comma-separated string
                designation=parsed_data.get("designation"),
                total_experience=parsed_data.get("total_experience", 0),
            )
            db.add(applicant)
            db.commit()
            db.refresh(applicant)

        # Insert resume data linked to the job
        db_resume = Resume(
            applicant_id=applicant.id,
            job_id=job_id,  # Associate with job
            file_url=file_path,
            text_content=parsed_data["raw_text"],
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)

        return {"message": "Resume uploaded successfully!", "resume_id": db_resume.id, "job_id": job_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
