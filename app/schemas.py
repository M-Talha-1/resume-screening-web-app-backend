from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    FILLED = "Filled"
    DRAFT = "Draft"

class EvaluationStatus(str, Enum):
    PENDING = "Pending"
    SHORTLISTED = "Shortlisted"
    REJECTED = "Rejected"
    INTERVIEW_SCHEDULED = "Interview Scheduled"
    OFFER_EXTENDED = "Offer Extended"
    HIRED = "Hired"

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    date_created: datetime
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ApplicantBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    skills: Optional[List[str]] = None
    designation: Optional[str] = None
    total_experience: Optional[float] = None
    current_company: Optional[str] = None
    current_location: Optional[str] = None
    notice_period: Optional[int] = None
    expected_salary: Optional[float] = None
    source: Optional[str] = None

class ApplicantCreate(ApplicantBase):
    pass

class ApplicantResponse(ApplicantBase):
    id: int
    date_created: datetime

    class Config:
        orm_mode = True

class JobDescriptionBase(BaseModel):
    title: str
    description: str
    required_skills: Optional[List[str]] = None
    status: JobStatus = JobStatus.DRAFT
    location: Optional[str] = None
    department: Optional[str] = None
    experience_required: Optional[float] = None
    salary_range_min: Optional[float] = None
    salary_range_max: Optional[float] = None
    job_type: Optional[str] = None
    closing_date: Optional[datetime] = None

class JobDescriptionCreate(JobDescriptionBase):
    admin_id: Optional[int] = None

class JobDescriptionResponse(JobDescriptionBase):
    id: int
    admin_id: int
    posted_date: datetime
    total_applicants: int
    total_shortlisted: int
    total_rejected: int

    class Config:
        orm_mode = True

class ResumeBase(BaseModel):
    applicant_id: int
    job_description_id: int
    file_path: str
    parsed_status: str
    text_content: Optional[str] = None
    file_type: str
    file_size: int
    status: str = "Pending"

class ResumeCreate(ResumeBase):
    pass

class ResumeResponse(ResumeBase):
    id: int
    upload_date: datetime

    class Config:
        orm_mode = True

class CandidateEvaluationBase(BaseModel):
    resume_id: int
    job_id: int
    hr_manager_id: Optional[int] = None
    suitability_score: float
    comments: Optional[str] = None
    status: EvaluationStatus = EvaluationStatus.PENDING
    interview_date: Optional[datetime] = None
    interview_notes: Optional[str] = None
    offer_details: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None

class CandidateEvaluationCreate(CandidateEvaluationBase):
    pass

class CandidateEvaluationResponse(CandidateEvaluationBase):
    id: int
    evaluation_date: datetime
    last_updated: Optional[datetime] = None

    class Config:
        orm_mode = True

class AnalyticsResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    closed_jobs: int
    total_applicants: int
    shortlisted_applicants: int
    rejected_applicants: int
    average_processing_time: float  # in days
    top_skills: List[Dict[str, Any]]
    job_status_distribution: Dict[str, int]
    applicant_status_distribution: Dict[str, int]

class JobAnalyticsResponse(BaseModel):
    job_id: int
    title: str
    total_applicants: int
    shortlisted: int
    rejected: int
    average_score: float
    status_distribution: Dict[str, int]
    skill_match_distribution: Dict[str, int]
    experience_distribution: Dict[str, int]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class JobSearchParams(BaseModel):
    query: Optional[str] = None
    skills: Optional[List[str]] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    job_type: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    status: Optional[JobStatus] = None

class SkillTrendsResponse(BaseModel):
    timeframe: str
    skills: List[Dict[str, Any]]

class HiringTrendsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    department: Optional[str] = None
    trends: List[Dict[str, Any]]

class DepartmentAnalyticsResponse(BaseModel):
    department: str
    total_jobs: int
    open_jobs: int
    filled_jobs: int
    total_applicants: int
    avg_time_to_fill: float

class ApplicantMetricsResponse(BaseModel):
    total_applications: int
    shortlisted: int
    rejected: int
    average_score: float
    application_timeline: List[Dict[str, Any]]

class JobMetricsResponse(BaseModel):
    total_applicants: int
    shortlisted: int
    rejected: int
    average_score: float
    status: str
    days_open: Optional[int] = None
    avg_time_to_first_review: Optional[int] = None
    skill_match_distribution: Dict[str, int]

class JobRecommendationResponse(BaseModel):
    job_id: int
    title: str
    department: str
    location: str
    match_score: float
    matching_skills: List[str]
    experience_match: bool
    location_match: bool

