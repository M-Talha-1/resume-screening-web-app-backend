import pytest
from fastapi.testclient import TestClient
import uuid
import os
import tempfile
from app.models import User, Job, Applicant, Resume, CandidateEvaluation
from app.auth import get_password_hash

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "response_time" in data

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Resume Web Backend API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"

def test_user_registration(client):
    unique_id = str(uuid.uuid4())
    response = client.post(
        "/auth/register",
        json={
            "email": f"newuser{unique_id}@example.com",
            "password": "TestPassword123!",
            "name": "New User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == f"newuser{unique_id}@example.com"
    assert data["name"] == "New User"
    assert "hashed_password" not in data

def test_user_login(client, test_user):
    response = client.post(
        "/auth/token",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

def test_protected_endpoint(client, test_user):
    # Get token
    response = client.post(
        "/auth/token",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    token = response.json()["access_token"]

    # Access protected endpoint
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name

def test_job_creation(client, test_user):
    # Get token
    response = client.post(
        "/auth/token",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    token = response.json()["access_token"]

    # Create job
    job_data = {
        "title": "New Job Position",
        "description": "Job description",
        "requirements": ["Python", "FastAPI"],
        "department": "Engineering",
        "location": "Remote",
        "salary_range": {"min": 50000, "max": 100000},
        "job_type": "Full-time",
        "experience_required": 3.0,
        "skills_required": ["Python", "FastAPI"],
        "status": "Open"
    }
    response = client.post(
        "/jobs/",
        json=job_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == job_data["title"]
    assert data["department"] == job_data["department"]
    assert "id" in data

def test_job_search(client, test_job):
    response = client.get("/jobs/", params={
        "department": "Engineering",
        "location": "Remote",
        "skip": 0,
        "limit": 10
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:  # If there are results
        assert "title" in data[0]
        assert "department" in data[0]
        assert "location" in data[0]

def test_resume_upload(client, test_user, test_job):
    # Get token
    response = client.post(
        "/auth/token",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    token = response.json()["access_token"]

    # Create a temporary test PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
        temp_pdf.write(b"Test PDF content")
        temp_pdf_path = temp_pdf.name

    try:
        # Upload resume
        with open(temp_pdf_path, "rb") as pdf_file:
            files = {
                "file": ("resume.pdf", pdf_file, "application/pdf")
            }
            response = client.post(
                "/resumes/",
                files=files,
                data={
                    "job_id": test_job.id,
                    "name": "Test Applicant",
                    "email": f"applicant{uuid.uuid4()}@example.com",
                    "phone": "1234567890"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["file_type"] == "application/pdf"
    finally:
        # Clean up the temporary file
        os.unlink(temp_pdf_path)

def test_resume_evaluation(client, test_user, test_resume, test_job):
    # Get token
    response = client.post(
        "/auth/token",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    token = response.json()["access_token"]

    # Create evaluation using the matching endpoint
    response = client.post(
        f"/matching/evaluate/{test_job.id}/{test_resume.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201  # Changed to 201 since it's a creation endpoint
    data = response.json()
    assert data["resume_id"] == test_resume.id
    assert data["job_id"] == test_job.id
    assert 0 <= data["overall_score"] <= 1
    assert 0 <= data["skill_match"] <= 1
    assert 0 <= data["experience_match"] <= 1
    assert isinstance(data["matching_skills"], list)

def test_analytics_endpoint(client, test_user, test_job, test_applicant, test_evaluation):
    # Get token
    response = client.post(
        "/auth/token",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    token = response.json()["access_token"]

    # Get analytics
    response = client.get(
        "/analytics/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0  # Should have some data 