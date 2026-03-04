import httpx
import pymupdf
from openai import OpenAI
from app.config import settings


CV_EXTRACT_PROMPT = """You are a CV parser. Extract structured information from the CV text below and return it in this exact markdown format. Be conservative — only include what is explicitly stated. Do not infer or fabricate.

## Identity
- Name: {name}
- Current Location: {city, country — or "Not stated"}
- Current Role: {most recent job title}

## Career Track & Level
- Primary Track: {e.g., Data Engineer / Data Analyst / Software Engineer}
- Effective Level: {Junior / Mid / Senior / Lead — infer from years and scope}
- Years of Experience: {total years}
- Career Summary: {2-3 sentences about overall scope and impact}

## Seniority Evidence
- Scope: {what systems or teams they owned}
- Ownership: {decisions they made, architectures they led}
- Impact: {measurable outcomes if any}

## Technical Stack
### Production-grade (explicitly mentioned in work experience)
- Languages: 
- Orchestration: 
- Cloud: 
- Databases: 
- Streaming: 
- Other: 

### Exposure only (mentioned in skills but not in work experience)
- 

## Domain Experience
- {list industries/domains from job history}

---

CV TEXT:
{cv_text}

Return ONLY the markdown. No preamble, no explanation."""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using pymupdf."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def generate_profile_from_cv_text(cv_text: str) -> str:
    """Send CV text to LLM and return structured markdown profile."""
    client = OpenAI(
        base_url=settings.ollama_base_url,
        api_key=settings.ollama_api_key,
        http_client=httpx.Client(timeout=settings.ollama_timeout),
    )

    prompt = CV_EXTRACT_PROMPT.replace("{cv_text}", cv_text[:6000])

    response = client.chat.completions.create(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2048,
    )

    return response.choices[0].message.content.strip()