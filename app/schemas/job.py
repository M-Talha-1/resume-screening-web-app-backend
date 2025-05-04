from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from app.models import JobStatus

class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    requirements: List[str] = Field(default_factory=list)
    department: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    salary_range: Dict[str, float] = Field(..., description="Dictionary with 'min' and 'max' keys")
    job_type: str = Field(..., min_length=1)
    experience_required: float = Field(..., ge=0)
    skills_required: List[str] = Field(default_factory=list)
    status: JobStatus = Field(default=JobStatus.DRAFT)

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1)
    requirements: Optional[List[str]] = None
    department: Optional[str] = Field(None, min_length=1)
    location: Optional[str] = Field(None, min_length=1)
    salary_range: Optional[Dict[str, float]] = None
    job_type: Optional[str] = Field(None, min_length=1)
    experience_required: Optional[float] = Field(None, ge=0)
    skills_required: Optional[List[str]] = None
    status: Optional[JobStatus] = None

class JobInDB(JobBase):
    id: int
    admin_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Job(JobInDB):
    pass 