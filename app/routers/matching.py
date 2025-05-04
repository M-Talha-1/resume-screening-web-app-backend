from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer
from fastapi_limiter.depends import RateLimiter
from pydantic import BaseModel, Field
import pytz

from app.database import get_db
from app.models import Resume, Job, CandidateEvaluation, EvaluationStatus, User
from app.services.matcher import evaluate_candidate, batch_evaluate_candidates, calculate_match_score
from app.auth import get_current_user
from app.cache import cache
from app.schemas import EvaluationResult

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/matching",
    tags=["matching"]
)

security = HTTPBearer()

class EvaluationResponse(BaseModel):
    evaluation_id: int
    resume_id: int
    job_id: int
    overall_score: float = Field(..., ge=0, le=100)
    semantic_score: float = Field(..., ge=0, le=100)
    skills_score: float = Field(..., ge=0, le=100)
    matching_skills: List[str]
    status: str

@router.post(
    "/evaluate/{job_id}/{resume_id}",
    response_model=EvaluationResult,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=10, minutes=1))]
)
async def evaluate_candidate_match(
    job_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Evaluate a candidate's match for a job"""
    try:
        # Get job and resume
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Check if evaluation already exists
        existing_eval = db.query(CandidateEvaluation).filter(
            CandidateEvaluation.job_id == job_id,
            CandidateEvaluation.resume_id == resume_id
        ).first()
        
        if existing_eval:
            # Update existing evaluation
            result = evaluate_candidate(job, resume)
            existing_eval.overall_score = result.overall_score
            existing_eval.skill_match = result.skill_match
            existing_eval.experience_match = result.experience_match
            existing_eval.matching_skills = result.matching_skills
            existing_eval.updated_at = datetime.now(pytz.UTC)
            db.commit()
            db.refresh(existing_eval)
            return EvaluationResult(
                id=existing_eval.id,
                job_id=existing_eval.job_id,
                resume_id=existing_eval.resume_id,
                overall_score=existing_eval.overall_score,
                skill_match=existing_eval.skill_match,
                experience_match=existing_eval.experience_match,
                matching_skills=existing_eval.matching_skills,
                evaluation_date=datetime.now(pytz.UTC)
            )
        
        # Create new evaluation
        result = evaluate_candidate(job, resume)
        evaluation = CandidateEvaluation(
            job_id=job_id,
            resume_id=resume_id,
            admin_id=current_user.id,
            overall_score=result.overall_score,
            skill_match=result.skill_match,
            experience_match=result.experience_match,
            matching_skills=result.matching_skills
        )
        
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        return EvaluationResult(
            id=evaluation.id,
            job_id=evaluation.job_id,
            resume_id=evaluation.resume_id,
            overall_score=evaluation.overall_score,
            skill_match=evaluation.skill_match,
            experience_match=evaluation.experience_match,
            matching_skills=evaluation.matching_skills,
            evaluation_date=datetime.now(pytz.UTC)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error evaluating candidate: {str(e)}")
        raise HTTPException(status_code=500, detail="Error evaluating candidate")

@router.get(
    "/job/{job_id}",
    response_model=List[EvaluationResponse],
    dependencies=[Depends(RateLimiter(times=20, minutes=1))]
)
async def get_job_evaluations(
    job_id: int,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all evaluations for a specific job"""
    query = db.query(CandidateEvaluation).filter(CandidateEvaluation.job_id == job_id)
    
    if min_score is not None:
        query = query.filter(CandidateEvaluation.overall_score >= min_score)
    if max_score is not None:
        query = query.filter(CandidateEvaluation.overall_score <= max_score)
    
    query = query.order_by(CandidateEvaluation.overall_score.desc())
    
    evaluations = query.all()
    return [
        EvaluationResponse(
            evaluation_id=e.id,
            resume_id=e.resume_id,
            job_id=e.job_id,
            overall_score=e.overall_score,
            semantic_score=e.skill_match,
            skills_score=e.experience_match,
            matching_skills=e.matching_skills,
            status=e.status.value
        )
        for e in evaluations
    ]

@router.post(
    "/batch-evaluate/{job_id}",
    dependencies=[Depends(RateLimiter(times=5, minutes=1))]
)
async def batch_evaluate_resumes(
    job_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Evaluate all resumes for a specific job."""
    try:
        # Get job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Get all resumes for the job
        resumes = db.query(Resume).filter(Resume.job_id == job_id).all()
        if not resumes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resumes found for this job"
            )

        # Prepare resume data for batch processing
        resume_data = [
            {
                "id": resume.id,
                "text": resume.raw_text,
                "skills": resume.applicant.skills if resume.applicant.skills else []
            }
            for resume in resumes
        ]

        # Batch evaluate
        results = batch_evaluate_candidates(
            job_description=job.description,
            job_requirements=job.requirements,
            resumes=resume_data
        )

        # Update evaluations in database
        for result in results:
            evaluation = db.query(CandidateEvaluation).filter(
                CandidateEvaluation.resume_id == result["resume_id"],
                CandidateEvaluation.job_id == job_id
            ).first()

            if evaluation:
                evaluation.suitability_score = result["overall_score"]
                evaluation.status = EvaluationStatus[result["status"]]
                evaluation.comments = f"Semantic Score: {result['semantic_score']}%, Skills Score: {result['skills_score']}%"
                evaluation.last_updated = datetime.utcnow()
            else:
                evaluation = CandidateEvaluation(
                    resume_id=result["resume_id"],
                    job_id=job_id,
                    admin_id=current_user.id,
                    suitability_score=result["overall_score"],
                    status=EvaluationStatus[result["status"]],
                    comments=f"Semantic Score: {result['semantic_score']}%, Skills Score: {result['skills_score']}%",
                    evaluation_date=datetime.utcnow()
                )
                db.add(evaluation)

        db.commit()

        return {
            "job_id": job_id,
            "total_evaluated": len(resumes),
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in batch evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in batch evaluation"
        )

@router.get("/match-resumes/{job_id}")
async def match_resumes(
    job_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Match resumes to a job and save evaluations."""
    try:
        # Get job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Get resumes for the job
        resumes = db.query(Resume).filter(Resume.job_id == job_id).all()
        if not resumes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resumes found for this job"
            )

        results = []
        for resume in resumes:
            try:
                # Calculate match score
                score = calculate_match_score(job.description, resume.raw_text)

                # Get or create evaluation
                evaluation = db.query(CandidateEvaluation).filter(
                    CandidateEvaluation.resume_id == resume.id,
                    CandidateEvaluation.job_id == job_id
                ).first()

                if evaluation:
                    # Update existing evaluation
                    evaluation.suitability_score = score
                    evaluation.status = EvaluationStatus.SHORTLISTED if score >= 70 else EvaluationStatus.REJECTED
                else:
                    # Create new evaluation
                    evaluation = CandidateEvaluation(
                        resume_id=resume.id,
                        job_id=job_id,
                        admin_id=current_user.id,
                        suitability_score=score,
                        status=EvaluationStatus.SHORTLISTED if score >= 70 else EvaluationStatus.REJECTED
                    )
                    db.add(evaluation)

                results.append({
                    "resume_id": resume.id,
                    "applicant_name": resume.applicant.name,
                    "score": score,
                    "status": evaluation.status.value
                })
            except Exception as e:
                logger.error(f"Error processing resume {resume.id}: {str(e)}")
                continue

        # Commit changes
        db.commit()

        # Sort results by score and return top 10
        results.sort(key=lambda x: x["score"], reverse=True)
        return {
            "job_id": job_id,
            "job_title": job.title,
            "matched_resumes": results[:10]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching resumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error matching resumes"
        )
