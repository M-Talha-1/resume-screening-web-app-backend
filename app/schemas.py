from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models import JobStatus, EvaluationStatus
import re
import json
from enum import Enum
import pytz

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = Field(default="user", pattern="^(admin|hr|user)$")
    is_active: bool = True

class UserCreate(UserBase):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one number')
        return v

class UserResponse(UserBase):
    id: int
    role: str
    date_created: datetime
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ApplicantBase(BaseModel):
    name: str
    email: str
    phone: str
    skills: List[str]
    experience_years: float
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    education: Optional[List[Dict[str, str]]] = None
    work_experience: Optional[List[Dict[str, Any]]] = None

class ApplicantCreate(ApplicantBase):
    pass

class ApplicantResponse(ApplicantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class JobStatus(str, Enum):
    DRAFT = "Draft"
    OPEN = "Open"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"

class JobBase(BaseModel):
    title: str
    description: str
    requirements: List[str] = Field(default_factory=list)
    department: str
    location: str
    salary_range: Dict[str, float]
    job_type: str
    experience_required: float
    skills_required: List[str] = Field(default_factory=list)
    status: JobStatus = JobStatus.OPEN

    @validator('salary_range')
    def validate_salary_range(cls, v):
        if 'min' not in v or 'max' not in v:
            raise ValueError("salary_range must contain 'min' and 'max' keys")
        if v['min'] > v['max']:
            raise ValueError("min salary cannot be greater than max salary")
        return v

    @validator('requirements', 'skills_required', pre=True)
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    department: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[Dict[str, float]] = None
    job_type: Optional[str] = None
    experience_required: Optional[float] = None
    skills_required: Optional[List[str]] = None
    status: Optional[JobStatus] = None

    @validator('requirements', 'skills_required', pre=True)
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []

    @validator('salary_range')
    def validate_salary_range(cls, v):
        if v is None:
            return v
        if 'min' not in v or 'max' not in v:
            raise ValueError("salary_range must contain 'min' and 'max' keys")
        if v['min'] > v['max']:
            raise ValueError("min salary cannot be greater than max salary")
        return v

class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    requirements: List[str]
    department: str
    location: str
    salary_range: Dict[str, float]
    job_type: str
    experience_required: float
    skills_required: List[str]
    status: JobStatus
    admin_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class ResumeBase(BaseModel):
    applicant_id: int
    job_id: int
    parsed_content: Dict[str, Any]
    extracted_skills: List[str]
    total_experience: float
    education: List[Dict[str, str]]
    work_experience: List[Dict[str, Any]]
    file_path: str
    file_type: str
    file_size: int

class ResumeCreate(ResumeBase):
    pass

class ResumeResponse(ResumeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CandidateEvaluationBase(BaseModel):
    resume_id: int
    job_id: int
    overall_score: float = Field(ge=0, le=1)
    semantic_score: float = Field(ge=0, le=1)
    skills_score: float = Field(ge=0, le=1)
    matching_skills: List[str]
    comments: Optional[str] = None
    status: EvaluationStatus = EvaluationStatus.PENDING

class CandidateEvaluationCreate(CandidateEvaluationBase):
    pass

class CandidateEvaluationUpdate(BaseModel):
    overall_score: Optional[float] = Field(None, ge=0, le=1)
    semantic_score: Optional[float] = Field(None, ge=0, le=1)
    skills_score: Optional[float] = Field(None, ge=0, le=1)
    matching_skills: Optional[List[str]] = None
    comments: Optional[str] = None
    status: Optional[EvaluationStatus] = None

class CandidateEvaluationResponse(CandidateEvaluationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    resume: ResumeResponse

    class Config:
        orm_mode = True

class EvaluateRequest(BaseModel):
    resume_id: int
    job_id: int

class JobAnalytics(BaseModel):
    total_applicants: int
    average_score: float
    matching_skills_frequency: Dict[str, int]
    status_distribution: Dict[str, int]
    daily_applications: Dict[str, int]

class JobSearchParams(BaseModel):
    query: Optional[str] = None
    skills: Optional[List[str]] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    job_type: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    status: Optional[JobStatus] = None

    @validator('skills', pre=True)
    def split_string_to_list(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(',')]
        return v

class AnalyticsResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    closed_jobs: int
    total_applicants: int
    shortlisted_applicants: int
    rejected_applicants: int
    average_processing_time: float
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

class UserTokenData(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserTokenData

    class Config:
        orm_mode = True

class TokenData(BaseModel):
    email: Optional[str] = None

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

class EvaluationResult(BaseModel):
    job_id: int
    resume_id: int
    overall_score: float = Field(..., ge=0, le=1)
    skill_match: float = Field(..., ge=0, le=1)
    experience_match: float = Field(..., ge=0, le=1)
    matching_skills: List[str]
    evaluation_date: datetime

    class Config:
        from_attributes = True

class CandidateEvaluation(BaseModel):
    id: int
    job_id: int
    resume_id: int
    overall_score: float
    skill_match: float
    experience_match: float
    matching_skills: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

