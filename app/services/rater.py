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
        summary=parsed.get("summary", ""),
        raw_title=jd_data.get("title"),
        raw_company=jd_data.get("company"),
        raw_output=raw,
    )


def _parse_table(text: str) -> dict:
    """
    Parse markdown table + Final Fit Grade from LLM output.
    Extracts each row of the scorecard and the final grade.
    """
    result = {
        "score": 0,
        "score_pct": 0,
        "grade_label": "",
        "scorecard": [],
        "stack_match": [],
        "stack_missing": [],
        "seniority_match": False,
        "remote_friendly": False,
        "red_flags": [],
        "highlights": [],
        "summary": "",
    }

    # Extract Final Fit Grade
    grade_match = re.search(r"Final Fit Grade:\s*(\d+)%\s*[—-]\s*(.+)", text)
    if grade_match:
        result["score_pct"] = int(grade_match.group(1))
        result["score"] = result["score_pct"] // 10
        result["grade_label"] = grade_match.group(2).strip()

    # Parse markdown table rows
    # Format: | Metric | Weight | Score | Evaluation |
    table_rows = re.findall(
        r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(-?\d+)\s*\|\s*([^|]+?)\s*\|",
        text
    )

    scorecard = []
    for row in table_rows:
        metric, weight, score, evaluation = row
        # Skip header row
        if "metric" in metric.lower() or "weight" in metric.lower():
            continue
        try:
            scorecard.append({
                "metric": metric.strip(),
                "weight": weight.strip(),
                "score": int(score.strip()),
                "evaluation": evaluation.strip(),
            })
        except ValueError:
            continue

    result["scorecard"] = scorecard

    # Extract red flags from low-scoring rows
    for row in scorecard:
        if row["score"] < 0 or ("red flag" in row["metric"].lower() or "gap" in row["metric"].lower()):
            if row["evaluation"] and row["evaluation"] not in result["red_flags"]:
                result["red_flags"].append(row["evaluation"])

    return result