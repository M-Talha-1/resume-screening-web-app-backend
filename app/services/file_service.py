import os
from pathlib import Path
from fastapi import UploadFile
from datetime import datetime

# Define the upload directory
UPLOAD_DIR = Path("app/uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_resume(file: UploadFile) -> str:
    """Save the uploaded resume file locally and return the file path."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_extension = Path(file.filename).suffix
    filename = f"{timestamp}{file_extension}"  # Unique filename
    file_path = UPLOAD_DIR / filename

    with file_path.open("wb") as buffer:
        buffer.write(file.file.read())  # Save file locally

    return str(file_path)
