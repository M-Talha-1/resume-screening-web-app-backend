from fastapi import status

def test_create_job(client, auth_headers):
    job_data = {
        "title": "Software Engineer",
        "description": "Looking for a skilled software engineer",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "location": "Remote",
        "department": "Engineering",
        "experience_required": 3.0,
        "salary_range_min": 80000,
        "salary_range_max": 120000,
        "job_type": "Full-time"
    }
    response = client.post("/jobs/", json=job_data, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == job_data["title"]
    assert data["description"] == job_data["description"]
    assert data["required_skills"] == job_data["required_skills"]
    assert "id" in data

def test_create_job_unauthorized(client):
    job_data = {
        "title": "Software Engineer",
        "description": "Test job"
    }
    response = client.post("/jobs/", json=job_data)
    assert response.status_code == 401

def test_get_jobs(client, auth_headers):
    # First create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test job"
    }
    client.post("/jobs/", json=job_data, headers=auth_headers)
    
    # Get all jobs
    response = client.get("/jobs/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert isinstance(data, list)

def test_get_job_by_id(client, auth_headers):
    # First create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test job"
    }
    create_response = client.post("/jobs/", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Get the job by ID
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["title"] == job_data["title"]

def test_update_job(client, auth_headers):
    # First create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test job"
    }
    create_response = client.post("/jobs/", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Update the job
    update_data = {
        "title": "Senior Software Engineer",
        "description": "Updated test job",
        "status": "Open"
    }
    response = client.put(f"/jobs/{job_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]
    assert data["status"] == update_data["status"]

def test_delete_job(client, auth_headers):
    # First create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test job"
    }
    create_response = client.post("/jobs/", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Delete the job
    response = client.delete(f"/jobs/{job_id}", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify job is deleted
    get_response = client.get(f"/jobs/{job_id}")
    assert get_response.status_code == 404

def test_search_jobs(client, auth_headers):
    # Create test jobs
    job_data1 = {
        "title": "Python Developer",
        "description": "Looking for Python expert",
        "required_skills": ["Python", "Django"],
        "location": "Remote"
    }
    job_data2 = {
        "title": "Frontend Developer",
        "description": "Looking for React expert",
        "required_skills": ["JavaScript", "React"],
        "location": "Office"
    }
    client.post("/jobs/", json=job_data1, headers=auth_headers)
    client.post("/jobs/", json=job_data2, headers=auth_headers)
    
    # Search by skill
    response = client.get("/jobs/search?skills=Python")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any("Python" in job["required_skills"] for job in data)
    
    # Search by location
    response = client.get("/jobs/search?location=Remote")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(job["location"] == "Remote" for job in data)

def test_job_analytics(client, auth_headers):
    # First create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test job"
    }
    create_response = client.post("/jobs/", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Get job analytics
    response = client.get(f"/jobs/{job_id}/analytics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_applicants" in data
    assert "shortlisted" in data
    assert "rejected" in data
    assert "average_score" in data

def test_close_job(client, auth_headers):
    # First create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test job"
    }
    create_response = client.post("/jobs/", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Close the job
    response = client.post(f"/jobs/{job_id}/close", headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "Closed"
    assert data["id"] == job_id 