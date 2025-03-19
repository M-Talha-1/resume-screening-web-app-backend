from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Resume, JobDescription, CandidateEvaluation
from app.services.matcher import calculate_match_score  # Import NLP Matching Logic

router = APIRouter()

@router.get("/match-resumes/{job_id}")
def match_resumes(job_id: int, db: Session = Depends(get_db)):
    """Match resumes only for the given job ID and store results in the database."""
    
    # Fetch job description
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch resumes linked to this job
    resumes = db.query(Resume).filter(Resume.job_id == job_id).all()
    if not resumes:
        raise HTTPException(status_code=404, detail="No resumes found for this job")

    scored_resumes = []
    
    for resume in resumes:
        score = calculate_match_score(job.description, resume.text_content)

        # Store the evaluation in the database
        existing_evaluation = db.query(CandidateEvaluation).filter(
            CandidateEvaluation.resume_id == resume.id,
            CandidateEvaluation.job_id == job_id
        ).first()

        if existing_evaluation:
            existing_evaluation.score = score  # Update score
            existing_evaluation.status = "Accepted" if score >= 70 else "Rejected"
        else:
            evaluation = CandidateEvaluation(
                resume_id=resume.id,
                job_id=job_id,
                score=score,
                status="Accepted" if score >= 70 else "Rejected",
            )
            db.add(evaluation)

        scored_resumes.append({"resume_id": resume.id, "score": score})

    db.commit()  # Save evaluations

    # Sort and return top 10 matched resumes
    scored_resumes.sort(key=lambda x: x["score"], reverse=True)

    return {"job_id": job_id, "matched_resumes": scored_resumes[:10]}  # Top 10 matches
