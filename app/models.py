from pydantic import BaseModel
from typing import List, Optional


class JobRateRequest(BaseModel):
    url: str


class JobRating(BaseModel):
    score: int
    stack_match: List[str]
    stack_missing: List[str]
    seniority_match: bool
    remote_friendly: bool
    red_flags: List[str]
    highlights: List[str]
    summary: str
    raw_title: Optional[str] = None
    raw_company: Optional[str] = None


class JobRateResponse(BaseModel):
    url: str
    rating: JobRating
    jd_excerpt: str
