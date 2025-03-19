from fastapi import APIRouter, File, UploadFile
import shutil
import os
from datetime import datetime
from app.services.resume_parser import extract_resume_info

router = APIRouter()

UPLOAD_FOLDER = "app/uploads/resumes/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    """Uploads a resume and extracts detailed information."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_extension = os.path.splitext(file.filename)[-1]
    file_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}{file_extension}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract key information
    resume_info = extract_resume_info(file_path)
    
    return {"resume_path": file_path, "parsed_info": resume_info}
