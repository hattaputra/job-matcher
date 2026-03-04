import json
import re
import httpx
from pathlib import Path
from openai import OpenAI
from app.config import settings
from app.models import JobRating


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "job_rating.txt"


def rate_jd(jd_data: dict, candidate_profile: str) -> JobRating:
    """
    Send JD + candidate profile to LLM and return structured rating.
    """
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt_template.format(
        candidate_profile=candidate_profile,
        title=jd_data.get("title", "Unknown"),
        company=jd_data.get("company", "Unknown"),
        location=jd_data.get("location", "Unknown"),
        jd_text=jd_data.get("jd_text", "")[:4000],
    )

    client = OpenAI(
        base_url=settings.ollama_base_url,
        api_key=settings.ollama_api_key,
        http_client=httpx.Client(timeout=settings.ollama_timeout),
    )

    response = client.chat.completions.create(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
    )

    raw = response.choices[0].message.content
    parsed = _parse_table(raw)

    return JobRating(
        score=parsed.get("score", 0),
        stack_match=parsed.get("stack_match", []),
        stack_missing=parsed.get("stack_missing", []),
        seniority_match=parsed.get("seniority_match", False),
        remote_friendly=parsed.get("remote_friendly", False),
        red_flags=parsed.get("red_flags", []),
        highlights=parsed.get("highlights", []),
        summary=parsed.get("summary", raw),
        raw_title=jd_data.get("title"),
        raw_company=jd_data.get("company"),
    )


def _parse_table(text: str) -> dict:
    """
    Parse the markdown table output from LLM.
    Extract Final Fit Grade as score.
    Return raw text as summary for display.
    """
    result = {
        "score": 0,
        "stack_match": [],
        "stack_missing": [],
        "seniority_match": False,
        "remote_friendly": False,
        "red_flags": [],
        "highlights": [],
        "summary": text,
    }

    # Extract Final Fit Grade percentage
    grade_match = re.search(r"Final Fit Grade:\s*(\d+)%", text)
    if grade_match:
        result["score"] = int(grade_match.group(1)) // 10  # convert % to /10

    return result