import os
import pytest
from fastapi import status
from pathlib import Path
from datetime import datetime, timedelta

def test_authentication_flow(client, db_session):
    """Test complete authentication flow"""
    # Test registration
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword",
        "role": "admin"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    user = response.json()
    assert user["email"] == user_data["email"]
    assert user["name"] == user_data["name"]
    assert user["role"] == user_data["role"]

    # Test login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test get current user
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == user_data["email"]

def test_job_management(client, auth_headers):
    """Test complete job management flow"""
    # Create a job
    job_data = {
        "title": "Senior Software Engineer",
        "description": "Looking for an experienced software engineer",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "location": "Remote",
        "department": "Engineering",
        "experience_required": 5.0,
        "salary_range_min": 100000,
        "salary_range_max": 150000,
        "job_type": "Full-time"
    }
    response = client.post("/jobs/", json=job_data, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    job = response.json()
    job_id = job["id"]

    # Get the created job
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == job_data["title"]

    # Update the job
    update_data = {
        "title": "Lead Software Engineer",
        "description": "Updated job description",
        "salary_range_max": 180000
    }
    response = client.put(f"/jobs/{job_id}", json=update_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == update_data["title"]

    # Close the job
    response = client.post(f"/jobs/{job_id}/close", headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["status"] == "Closed"

    # Search jobs
    response = client.get("/jobs/search?skills=Python&location=Remote")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) > 0

def test_resume_management(client, auth_headers):
    """Test complete resume management flow"""
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
- Docker
- AWS

Experience:
- Senior Software Engineer at Tech Corp (2020-Present)
- Software Engineer at Dev Inc (2018-2020)

Education:
- B.S. Computer Science, University of Tech (2014-2018)
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
        resume = response.json()
        assert resume["job_description_id"] == job_id
        assert resume["parsed_status"] == "Parsed"
        assert resume["file_type"] == "txt"
        
        # Try to upload duplicate resume
        with open(resume_path, "rb") as f:
            response = client.post(
                "/resumes/",
                files={"file": ("resume.txt", f, "text/plain")},
                data={"job_description_id": job_id}
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Resume already submitted" in response.json()["detail"]
        
    finally:
        # Clean up test file
        if resume_path.exists():
            resume_path.unlink()
        if "file_path" in resume and os.path.exists(resume["file_path"]):
            os.remove(resume["file_path"])

def test_analytics(client, auth_headers):
    """Test analytics functionality"""
    # Create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test job for analytics"
    }
    create_response = client.post("/jobs/", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]

    # Get job analytics
    response = client.get(f"/jobs/{job_id}/analytics", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    analytics = response.json()
    assert "total_applicants" in analytics
    assert "shortlisted" in analytics
    assert "rejected" in analytics
    assert "average_score" in analytics

    # Get dashboard analytics
    response = client.get("/analytics/dashboard", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    dashboard = response.json()
    assert "total_jobs" in dashboard
    assert "active_jobs" in dashboard
    assert "total_applicants" in dashboard

    # Get skill trends
    response = client.get("/analytics/skills", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

    # Get hiring trends
    response = client.get("/analytics/hiring", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

def test_error_handling(client, auth_headers):
    """Test error handling scenarios"""
    # Test invalid job ID
    response = client.get("/jobs/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Test unauthorized access
    response = client.post("/jobs/", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Test invalid resume upload
    # Create a test file first
    test_file = Path("test_error.txt")
    test_file.write_text("test content")
    try:
        with open(test_file, "rb") as f:
            response = client.post(
                "/resumes/",
                files={"file": ("resume.txt", f, "text/plain")},
                data={"job_description_id": 999}
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    finally:
        if test_file.exists():
            test_file.unlink()

    # Test invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 