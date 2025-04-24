# Resume Screening Backend

A FastAPI-based backend system for resume screening and job matching. This system allows HR managers to post jobs, applicants to submit resumes, and automatically matches candidates to job requirements.

## Features

- User authentication and authorization (Admin, HR roles)
- Job posting and management
- Resume upload and parsing
- Automated resume-job matching
- Candidate evaluation system
- File storage for resumes
- RESTful API endpoints

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy ORM
- Alembic for database migrations
- JWT for authentication
- NLTK for text processing
- PDF and DOCX parsing

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd resume_web_backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
DATABASE_URL=postgresql://user:password@localhost/resume_screening
SECRET_KEY=your-secret-key-here
```

5. Run database migrations:
```bash
alembic upgrade head
```

## Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- POST `/auth/register` - Register a new user
- POST `/auth/login` - Login and get access token
- GET `/auth/me` - Get current user profile

### Jobs
- GET `/job/` - Get all jobs
- POST `/job/` - Create a new job
- PUT `/job/{job_id}` - Update a job
- DELETE `/job/{job_id}` - Delete a job

### Resumes
- POST `/upload-resume/` - Upload and parse a resume
- GET `/resumes/{job_id}` - Get resumes for a job

### Matching
- GET `/match-resumes/{job_id}` - Match resumes to a job

## Database Schema

The system uses the following main tables:
- Users
- Applicants
- Resumes
- Job Descriptions
- Candidate Evaluations

## Security

- JWT-based authentication
- Password hashing using bcrypt
- CORS protection
- File upload validation
- Input sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
