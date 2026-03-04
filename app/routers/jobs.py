from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.models import JobRateRequest, JobRateResponse
from app.services.fetcher import fetch_jd
from app.services.rater import rate_jd
from app.services.profile import load_profile, profile_exists

router = APIRouter()


class JobRateRequestWithUser(BaseModel):
    url: str
    sender_id: Optional[int] = None


@router.post("/rate-job", response_model=JobRateResponse)
def rate_job(request: JobRateRequestWithUser):
    # Load candidate profile
    if request.sender_id and profile_exists(request.sender_id):
        candidate_profile = load_profile(request.sender_id)
    else:
        raise HTTPException(
            status_code=403,
            detail="Candidate profile not found. Please complete onboarding first."
        )

    # Fetch JD
    try:
        jd_data = fetch_jd(request.url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch JD: {str(e)}")

    if not jd_data.get("jd_text"):
        raise HTTPException(status_code=404, detail="Could not extract job description from URL")

    # Rate
    try:
        rating = rate_jd(jd_data, candidate_profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM rating failed: {str(e)}")

    return JobRateResponse(
        url=request.url,
        rating=rating,
        jd_excerpt=jd_data["jd_text"][:300] + "...",
    )