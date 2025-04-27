import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from app.main import app
from app.models import User, JobDescription, Resume, CandidateEvaluation, Applicant
from app.database import get_db
from app.auth import create_access_token

client = TestClient(app)

# Test data
TEST_HR_MANAGER = {
    "name": "Test HR Manager",
    "email": "hr@test.com",
    "password": "testpass123",
    "role": "hr_manager"
}

TEST_JOB = {
    "title": "Senior Python Developer",
    "description": "Looking for an experienced Python developer",
    "required_skills": ["python", "django", "fastapi", "sql", "docker"],
    "experience_required": 5.0,
    "location": "New York",
    "status": "Open"
}

TEST_RESUME_TEXT = """
Senior Python Developer with 6 years of experience
Skills: Python, Django, FastAPI, SQL, Docker, AWS
Location: New York
"""

@pytest.fixture
def test_data(db: Session, test_hr_manager: User):
    # Create test applicant
    applicant = Applicant(
        name="Test Applicant",
        email="applicant@test.com",
        role="Applicant"
    )
    db.add(applicant)
    db.commit()
    db.refresh(applicant)

    # Create test job
    job = JobDescription(
        **TEST_JOB,
        admin_id=test_hr_manager.id,
        posted_date=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Create test resume
    resume = Resume(
        applicant_id=applicant.id,
        job_description_id=job.id,
        file_path="/test/resume.pdf",
        parsed_status="Completed",
        text_content=TEST_RESUME_TEXT,
        file_type="pdf",
        file_size=1024,
        status="Pending"
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {"applicant": applicant, "job": job, "resume": resume}

def test_evaluate_resume(client: TestClient, test_data: dict, test_token: str, db: Session):
    # Test evaluation endpoint
    response = client.post(
        "/screening/evaluate",
        json={"resume_id": test_data["resume"].id, "job_id": test_data["job"].id},
        headers={"Authorization": f"Bearer {test_token}"}
    )

    assert response.status_code == 201
    data = response.json()

    # Verify evaluation results
    assert data["resume_id"] == test_data["resume"].id
    assert data["job_id"] == test_data["job"].id
    assert "suitability_score" in data
    assert "comments" in data
    assert "status" in data

def test_evaluate_resume_unauthorized(client: TestClient, test_data: dict):
    response = client.post(
        "/screening/evaluate",
        json={"resume_id": test_data["resume"].id, "job_id": test_data["job"].id}
    )
    assert response.status_code == 401

def test_evaluate_resume_not_hr_manager(client: TestClient, test_data: dict):
    # Create access token for non-HR user
    access_token = create_access_token(data={"sub": "user@test.com", "role": "applicant"})

    response = client.post(
        "/screening/evaluate",
        json={"resume_id": test_data["resume"].id, "job_id": test_data["job"].id},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 403

def test_evaluate_resume_not_found(client: TestClient, test_token: str):
    response = client.post(
        "/screening/evaluate",
        json={"resume_id": 999, "job_id": 999},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 404

def test_evaluate_resume_already_exists(client: TestClient, test_data: dict, test_token: str, db: Session):
    # Create first evaluation
    response = client.post(
        "/screening/evaluate",
        json={"resume_id": test_data["resume"].id, "job_id": test_data["job"].id},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201

    # Try to create duplicate evaluation
    response = client.post(
        "/screening/evaluate",
        json={"resume_id": test_data["resume"].id, "job_id": test_data["job"].id},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 409

def test_create_evaluation(client, db: Session, test_hr_manager: User, test_token: str):
    # Create test applicant and resume
    applicant = Applicant(
        name="John Doe",
        email="john@example.com",
        phone="1234567890",
        skills=["Python", "FastAPI"],
        designation="Software Engineer",
        total_experience=5.0
    )
    db.add(applicant)
    db.commit()
    db.refresh(applicant)

    resume = Resume(
        applicant_id=applicant.id,
        file_path="/path/to/resume.pdf",
        parsed_status="Completed",
        text_content="Python developer with 5 years of experience in FastAPI",
        file_type="pdf",
        file_size=1024,
        status="Pending"
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    job = JobDescription(
        title="Software Engineer",
        description="Python developer role",
        required_skills=["Python", "FastAPI"],
        experience_required=5.0,
        location="Remote",
        status="Open"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    evaluation_data = {
        "resume_id": resume.id,
        "job_id": job.id,
        "suitability_score": 85,
        "comments": "Strong candidate with relevant experience",
        "status": "shortlisted"
    }

    response = client.post(
        "/screening/evaluations/",
        json=evaluation_data,
        headers={"Authorization": f"Bearer {test_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["resume_id"] == resume.id
    assert data["job_id"] == job.id
    assert data["suitability_score"] == 85

def test_get_evaluation(client, db: Session, test_hr_manager: User, test_token: str):
    # Create test applicant and resume
    applicant = Applicant(
        name="Jane Smith",
        email="jane@example.com",
        phone="0987654321",
        skills=["Java", "Spring Boot"],
        designation="Backend Developer",
        total_experience=3.0
    )
    db.add(applicant)
    db.commit()
    db.refresh(applicant)

    resume = Resume(
        applicant_id=applicant.id,
        file_path="/path/to/resume2.pdf",
        parsed_status="Completed",
        text_content="Java developer with Spring Boot experience",
        file_type="pdf",
        file_size=1024,
        status="Pending"
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    job = JobDescription(
        title="Backend Developer",
        description="Java developer role",
        required_skills=["Java", "Spring Boot"],
        experience_required=3.0,
        location="New York",
        status="Open"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    evaluation = CandidateEvaluation(
        resume_id=resume.id,
        job_id=job.id,
        hr_manager_id=test_hr_manager.id,
        suitability_score=90,
        comments="Excellent technical background",
        status="selected"
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    # Test get evaluation
    response = client.get(
        f"/screening/evaluations/{evaluation.id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == evaluation.id
    assert data["suitability_score"] == 90

def test_list_evaluations(client, db: Session, test_hr_manager: User, test_token: str):
    # Create test applicant and resume
    applicant = Applicant(
        name="Alice Brown",
        email="alice@example.com",
        phone="1112223333",
        skills=["Python", "Django"],
        designation="Full Stack Developer",
        total_experience=2.0
    )
    db.add(applicant)
    db.commit()
    db.refresh(applicant)

    resume = Resume(
        applicant_id=applicant.id,
        file_path="/path/to/resume3.pdf",
        parsed_status="Completed",
        text_content="Python and Django developer",
        file_type="pdf",
        file_size=1024,
        status="Pending"
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    job = JobDescription(
        title="Full Stack Developer",
        description="Python/React developer role",
        required_skills=["Python", "React"],
        experience_required=2.0,
        location="Remote",
        status="Open"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    evaluations = [
        CandidateEvaluation(
            resume_id=resume.id,
            job_id=job.id,
            hr_manager_id=test_hr_manager.id,
            suitability_score=75,
            comments="Good potential",
            status="under_review"
        ),
        CandidateEvaluation(
            resume_id=resume.id,
            job_id=job.id,
            hr_manager_id=test_hr_manager.id,
            suitability_score=80,
            comments="Strong communication skills",
            status="shortlisted"
        )
    ]
    db.add_all(evaluations)
    db.commit()
    for eval in evaluations:
        db.refresh(eval)

    # Test list evaluations
    response = client.get(
        "/screening/evaluations",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_update_evaluation(client, db: Session, test_hr_manager: User, test_token: str):
    # Create test applicant and resume
    applicant = Applicant(
        name="Bob Wilson",
        email="bob@example.com",
        phone="4445556666",
        skills=["Python", "FastAPI", "React"],
        designation="Senior Developer",
        total_experience=4.0
    )
    db.add(applicant)
    db.commit()
    db.refresh(applicant)

    resume = Resume(
        applicant_id=applicant.id,
        file_path="/path/to/resume4.pdf",
        parsed_status="Completed",
        text_content="Senior Python developer with React experience",
        file_type="pdf",
        file_size=1024,
        status="Pending"
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    job = JobDescription(
        title="Senior Developer",
        description="Full stack role",
        required_skills=["Python", "React"],
        experience_required=4.0,
        location="San Francisco",
        status="Open"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    evaluation = CandidateEvaluation(
        resume_id=resume.id,
        job_id=job.id,
        hr_manager_id=test_hr_manager.id,
        suitability_score=70,
        comments="Needs technical assessment",
        status="under_review"
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    # Test update evaluation
    update_data = {
        "suitability_score": 85,
        "comments": "Passed technical assessment",
        "status": "shortlisted"
    }
    response = client.put(
        f"/screening/evaluations/{evaluation.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["suitability_score"] == 85
    assert data["status"] == "shortlisted"

def test_delete_evaluation(client, db: Session, test_hr_manager: User, test_token: str):
    # Create test applicant and resume
    applicant = Applicant(
        name="Charlie Davis",
        email="charlie@example.com",
        phone="7778889999",
        skills=["JavaScript", "React"],
        designation="Frontend Developer",
        total_experience=1.0
    )
    db.add(applicant)
    db.commit()
    db.refresh(applicant)

    resume = Resume(
        applicant_id=applicant.id,
        file_path="/path/to/resume5.pdf",
        parsed_status="Completed",
        text_content="Frontend developer with React experience",
        file_type="pdf",
        file_size=1024,
        status="Pending"
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    job = JobDescription(
        title="Frontend Developer",
        description="React developer role",
        required_skills=["React", "JavaScript"],
        experience_required=1.0,
        location="Remote",
        status="Open"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    evaluation = CandidateEvaluation(
        resume_id=resume.id,
        job_id=job.id,
        hr_manager_id=test_hr_manager.id,
        suitability_score=65,
        comments="Junior level candidate",
        status="rejected"
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    # Test delete evaluation
    response = client.delete(
        f"/screening/evaluations/{evaluation.id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 204

    # Verify evaluation is deleted
    response = client.get(
        f"/screening/evaluations/{evaluation.id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 404 