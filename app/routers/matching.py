from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Resume, JobDescription, CandidateEvaluation
from app.services.matcher import calculate_match_score

router = APIRouter()

@router.get("/match-resumes/{job_id}")
def match_resumes(job_id: int, db: Session = Depends(get_db)):
    """Match resumes to a job and save evaluations."""

    job = db.query(JobDescription).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resumes = db.query(Resume).filter_by(job_description_id=job_id).all()
    if not resumes:
        raise HTTPException(status_code=404, detail="No resumes found for this job")

    results = []

    for resume in resumes:
        score = calculate_match_score(job.description, resume.text_content)

        evaluation = db.query(CandidateEvaluation).filter_by(
            resume_id=resume.id, job_id=job_id
        ).first()

        if evaluation:
            evaluation.suitability_score = score
            evaluation.status = "Accepted" if score >= 70 else "Rejected"
        else:
            evaluation = CandidateEvaluation(
                resume_id=resume.id,
                job_id=job_id,
                suitability_score=score,
                status="Accepted" if score >= 70 else "Rejected",
            )
            db.add(evaluation)

        results.append({
            "resume_id": resume.id,
            "score": score
        })

    db.commit()
    results.sort(key=lambda x: x["score"], reverse=True)

    return {"job_id": job_id, "matched_resumes": results[:10]}  # Return top 10
