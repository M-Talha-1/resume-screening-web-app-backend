#!/bin/bash

# Test health check endpoint
echo "Testing health check endpoint..."
curl -X GET "http://localhost:8000/health"

# Test root endpoint
echo -e "\n\nTesting root endpoint..."
curl -X GET "http://localhost:8000/"

# Test user registration
echo -e "\n\nTesting user registration..."
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPassword123!",
    "role": "admin"
  }'

# Test user login and get token
echo -e "\n\nTesting user login..."
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -d "username=test@example.com&password=TestPassword123!" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r '.access_token')

echo "Token received: $TOKEN"

# Test protected endpoint
echo -e "\n\nTesting protected endpoint..."
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# Test job creation
echo -e "\n\nTesting job creation..."
curl -X POST "http://localhost:8000/jobs/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Software Engineer",
    "description": "Looking for a skilled software engineer",
    "requirements": ["Python", "FastAPI"],
    "department": "Engineering",
    "location": "Remote",
    "salary_range": {"min": 50000, "max": 100000},
    "job_type": "Full-time",
    "experience_required": 3.0,
    "skills_required": ["Python", "FastAPI", "SQL"]
  }'

# Test job search
echo -e "\n\nTesting job search..."
curl -X GET "http://localhost:8000/jobs/?query=engineer" \
  -H "Authorization: Bearer $TOKEN"

# Create a test resume file
echo -e "\n\nCreating test resume file..."
cat > tests/test_resume.txt << 'EOF'
John Doe
Software Engineer
john.doe@example.com
(123) 456-7890

EDUCATION
Bachelor of Science in Computer Science
University of Technology
2018 - 2022

EXPERIENCE
Software Engineer at Tech Corp
2022 - Present
- Developed and maintained web applications using Python and FastAPI
- Implemented RESTful APIs and microservices architecture
- Collaborated with cross-functional teams to deliver high-quality software

SKILLS
Python, FastAPI, SQL, Docker, AWS, Git, REST APIs, Microservices
EOF

# Test resume upload
echo -e "\n\nTesting resume upload..."
curl -X POST "http://localhost:8000/resumes/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "job_id=1" \
  -F "name=John Doe" \
  -F "email=john.doe@example.com" \
  -F "phone=1234567890" \
  -F "file=@tests/test_resume.txt"

# Test resume evaluation
echo -e "\n\nTesting resume evaluation..."
curl -X POST "http://localhost:8000/matching/evaluate/1/1" \
  -H "Authorization: Bearer $TOKEN"

# Test analytics endpoint
echo -e "\n\nTesting analytics endpoint..."
curl -X GET "http://localhost:8000/analytics/dashboard" \
  -H "Authorization: Bearer $TOKEN" 