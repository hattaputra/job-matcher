from fastapi import APIRouter, HTTPException
from app.models import JobRateRequest, JobRateResponse
from app.services.fetcher import fetch_jd
from app.services.rater import rate_jd

router = APIRouter()


@router.post("/rate-job", response_model=JobRateResponse)
def rate_job(request: JobRateRequest):
    """
    Accept a LinkedIn job URL, fetch the JD, and return an AI-powered rating.
    """
    try:
        jd_data = fetch_jd(request.url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch JD: {str(e)}")

    if not jd_data.get("jd_text"):
        raise HTTPException(status_code=404, detail="Could not extract job description from URL")

    try:
        rating = rate_jd(jd_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM rating failed: {str(e)}")

    return JobRateResponse(
        url=request.url,
        rating=rating,
        jd_excerpt=jd_data["jd_text"][:300] + "...",
    )
