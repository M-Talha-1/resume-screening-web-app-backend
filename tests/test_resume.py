import os
import pytest
from fastapi import UploadFile
from pathlib import Path
from fastapi import status

def test_upload_resume(client, auth_headers):
    # First create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test job"
    }
    create_response = client.post("/jobs/", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Create a test resume file
    resume_content = """John Doe
Software Engineer
test@example.com
+1234567890

Skills:
- Python
- FastAPI
- PostgreSQL
"""
    resume_path = Path("test_resume.txt")
    resume_path.write_text(resume_content)
    
    try:
        # Upload resume
        with open(resume_path, "rb") as f:
            response = client.post(
                "/resumes/",
                files={"file": ("resume.txt", f, "text/plain")},
                data={"job_description_id": job_id}
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["job_description_id"] == job_id
        assert data["parsed_status"] == "Parsed"
        assert data["file_type"] == "txt"
        assert "id" in data
        assert "upload_date" in data
        
        # Verify the file was saved
        assert os.path.exists(data["file_path"])
        
    finally:
        # Clean up test file
        if resume_path.exists():
            resume_path.unlink()
        if "file_path" in data and os.path.exists(data["file_path"]):
            os.remove(data["file_path"])

def test_upload_resume_invalid_job(client):
    # Create a test resume file in the tests directory
    resume_content = """John Doe
Software Engineer
test@example.com
+1234567890
"""
    resume_path = Path("tests/test_resume.txt")
    resume_path.write_text(resume_content)
    
    try:
        # Try to upload resume for non-existent job
        with open(resume_path, "rb") as f:
            response = client.post(
                "/resumes/",
                files={"file": ("resume.txt", f, "text/plain")},
                data={"job_description_id": 999}  # Non-existent job ID
            )
        
        assert response.status_code == 400
        assert "Invalid job ID" in response.json()["detail"]
    finally:
        # Clean up test file
        if resume_path.exists():
            resume_path.unlink()

def test_upload_resume_duplicate(client, auth_headers):
    # First create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test job"
    }
    create_response = client.post("/jobs/", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Create a test resume file
    resume_content = """John Doe
Software Engineer
test@example.com
+1234567890
"""
    resume_path = Path("test_resume.txt")
    resume_path.write_text(resume_content)
    
    try:
        # Upload resume first time
        with open(resume_path, "rb") as f:
            response1 = client.post(
                "/resumes/",
                files={"file": ("resume.txt", f, "text/plain")},
                data={"job_description_id": job_id}
            )
        assert response1.status_code == 201
        
        # Try to upload the same resume again
        with open(resume_path, "rb") as f:
            response2 = client.post(
                "/resumes/",
                files={"file": ("resume.txt", f, "text/plain")},
                data={"job_description_id": job_id}
            )
        assert response2.status_code == 400
        assert "Resume already submitted" in response2.json()["detail"]
        
    finally:
        # Clean up test file
        if resume_path.exists():
            resume_path.unlink()
        if "file_path" in response1.json() and os.path.exists(response1.json()["file_path"]):
            os.remove(response1.json()["file_path"]) 