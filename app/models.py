from pydantic import BaseModel
from typing import List, Optional, Any


class JobRateRequest(BaseModel):
    url: str


class ScorecardRow(BaseModel):
    metric: str
    weight: str
    score: int
    evaluation: str


class JobRating(BaseModel):
    score: int
    score_pct: int = 0
    grade_label: str = ""
    scorecard: List[ScorecardRow] = []
    stack_match: List[str] = []
    stack_missing: List[str] = []
    seniority_match: bool = False
    remote_friendly: bool = False
    red_flags: List[str] = []
    highlights: List[str] = []
    summary: str = ""
    raw_title: Optional[str] = None
    raw_company: Optional[str] = None
    raw_output: Optional[str] = None


class JobRateResponse(BaseModel):
    url: str
    rating: JobRating
    jd_excerpt: str