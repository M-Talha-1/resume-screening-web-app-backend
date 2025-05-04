#!/bin/bash

# Base URL
BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test data
TIMESTAMP=$(date +%s)
TEST_EMAIL="test${TIMESTAMP}@example.com"
TEST_PASSWORD="StrongPass123!"
TEST_NAME="Test User"
ACCESS_TOKEN=""

# Function to print test results
print_result() {
    local status_code=$1
    local test_name=$2
    local response=$3
    if [ $status_code -eq 200 ] || [ $status_code -eq 201 ]; then
        echo -e "${GREEN}✓ $test_name${NC}"
    else
        echo -e "${RED}✗ $test_name (Status: $status_code)${NC}"
        echo "Response: $response"
    fi
}

echo -e "${YELLOW}Starting API Tests...${NC}\n"

# Test 1: Register User
echo "1. Testing User Registration..."
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"$TEST_NAME\",
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\",
        \"role\": \"admin\"
    }")
status_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | sed '$d')
print_result $status_code "User Registration" "$response_body"

# Test 2: Login and get access token
echo -e "\n2. Testing Login..."
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$TEST_EMAIL&password=$TEST_PASSWORD")
status_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | sed '$d')
print_result $status_code "User Login" "$response_body"

# Extract access token
ACCESS_TOKEN=$(echo $response_body | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}Failed to get access token. Stopping tests.${NC}"
    exit 1
fi

# Test 3: Get Current User
echo -e "\n3. Testing Get Current User..."
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
status_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | sed '$d')
print_result $status_code "Get Current User" "$response_body"

# Test 4: Create Job
echo -e "\n4. Testing Job Creation..."
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/jobs/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Software Engineer",
        "description": "We are looking for a software engineer",
        "requirements": ["Python", "FastAPI"],
        "department": "Engineering",
        "location": "Remote",
        "salary_range": {"min": 50000, "max": 100000},
        "job_type": "Full-time",
        "experience_required": 2,
        "skills_required": ["Python", "FastAPI", "SQL"]
    }')
status_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | sed '$d')
print_result $status_code "Job Creation" "$response_body"

# Extract job_id
JOB_ID=$(echo $response_body | grep -o '"id":[0-9]*' | cut -d':' -f2 | head -1)
if [ -z "$JOB_ID" ]; then
    echo -e "${RED}Failed to get job ID. Some tests will be skipped.${NC}"
fi

# Test 5: Get Job by ID
if [ ! -z "$JOB_ID" ]; then
    echo -e "\n5. Testing Get Job by ID..."
    response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/jobs/$JOB_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    print_result $status_code "Get Job by ID" "$response_body"
fi

# Test 6: Create Resume
if [ ! -z "$JOB_ID" ]; then
    echo -e "\n6. Testing Resume Creation..."
    # Use existing PDF file
    RESUME_FILE="talha.pdf"
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/resumes/" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -F "file=@$RESUME_FILE" \
        -F "job_id=$JOB_ID")
    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    print_result $status_code "Resume Creation" "$response_body"

    # Extract resume_id
    RESUME_ID=$(echo $response_body | grep -o '"id":[0-9]*' | cut -d':' -f2 | head -1)
fi

# Test 7: Get Analytics Dashboard
echo -e "\n7. Testing Analytics Dashboard..."
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/analytics/dashboard" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
status_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | sed '$d')
print_result $status_code "Get Analytics Dashboard" "$response_body"

# Test 8: Get Job Analytics
if [ ! -z "$JOB_ID" ]; then
    echo -e "\n8. Testing Job Analytics..."
    response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/analytics/jobs/$JOB_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    print_result $status_code "Get Job Analytics" "$response_body"
fi

# Test 9: Get Skills Analytics
echo -e "\n9. Testing Skills Analytics..."
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/analytics/skills" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
status_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | sed '$d')
print_result $status_code "Get Skills Analytics" "$response_body"

# Test 10: Evaluate Resume
if [ ! -z "$JOB_ID" ] && [ ! -z "$RESUME_ID" ]; then
    echo -e "\n10. Testing Resume Evaluation..."
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/matching/evaluate/$JOB_ID/$RESUME_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    print_result $status_code "Resume Evaluation" "$response_body"
fi

# Test 11: Get Screening Results
if [ ! -z "$JOB_ID" ]; then
    echo -e "\n11. Testing Get Screening Results..."
    response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/screening/job/$JOB_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    print_result $status_code "Get Screening Results" "$response_body"
fi

# Test 12: Cleanup - Delete Job
if [ ! -z "$JOB_ID" ]; then
    echo -e "\n12. Testing Job Deletion..."
    response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/jobs/$JOB_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    print_result $status_code "Delete Job" "$response_body"
fi

# Test 13: Deactivate Account
echo -e "\n13. Testing Account Deactivation..."
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/deactivate" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
status_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | sed '$d')
print_result $status_code "Account Deactivation" "$response_body"

echo -e "\n${YELLOW}API Tests Completed${NC}" 