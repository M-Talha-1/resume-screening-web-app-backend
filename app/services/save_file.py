import os
from pathlib import Path
from fastapi import UploadFile
from datetime import datetime

UPLOAD_DIR = Path("app/uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_resume(file: UploadFile) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_extension = Path(file.filename).suffix
    filename = f"{timestamp}{file_extension}"
    file_path = UPLOAD_DIR / filename

    with file_path.open("wb") as buffer:
        buffer.write(file.file.read())

    return str(file_path)