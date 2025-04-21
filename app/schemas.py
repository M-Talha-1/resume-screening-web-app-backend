from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ApplicantBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    skills: Optional[List[str]] = []
    designation: Optional[str] = None
    total_experience: Optional[float] = 0.0

class ResumeBase(BaseModel):
    applicant_id: int
    job_description_id: int
    file_path: str
    text_content: Optional[str]

class ResumeResponse(BaseModel):
    id: int
    applicant_id: int
    job_description_id: int
    file_path: str
    upload_date: datetime
    parsed_status: str

    class Config:
        orm_mode = True

class JobDescriptionRequest(BaseModel):
    title: str
    description: str
    status: str
    admin_id: Optional[int]  # Optional if you're assigning it from session/context

class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    posted_date: datetime
    admin_id: Optional[int]

    class Config:
        orm_mode = True
