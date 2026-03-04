import json
import re
from pathlib import Path
from openai import OpenAI
from app.config import settings
from app.models import JobRating


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "job_rating.txt"


def rate_jd(jd_data: dict) -> JobRating:
    """
    Send JD to Ollama (Qwen3:8b) and return structured rating.
    """
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt_template.format(
        title=jd_data.get("title", "Unknown"),
        company=jd_data.get("company", "Unknown"),
        location=jd_data.get("location", "Unknown"),
        jd_text=jd_data.get("jd_text", "")[:4000],  # cap token input
    )

    client = OpenAI(
        base_url=settings.ollama_base_url,
        api_key="ollama",
    )

    response = client.chat.completions.create(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
        timeout=settings.ollama_timeout,
    )

    raw = response.choices[0].message.content
    parsed = _parse_json(raw)

    return JobRating(
        score=parsed.get("score", 0),
        stack_match=parsed.get("stack_match", []),
        stack_missing=parsed.get("stack_missing", []),
        seniority_match=parsed.get("seniority_match", False),
        remote_friendly=parsed.get("remote_friendly", False),
        red_flags=parsed.get("red_flags", []),
        highlights=parsed.get("highlights", []),
        summary=parsed.get("summary", ""),
        raw_title=jd_data.get("title"),
        raw_company=jd_data.get("company"),
    )


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response, handle markdown code blocks."""
    text = re.sub(r"```(?:json)?", "", text).strip("` \n")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON block inside response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}
