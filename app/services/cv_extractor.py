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


SALARY_BENCHMARK_PROMPT = """You are a compensation expert specializing in tech talent markets across Southeast Asia, Australia, and the Middle East.

Based on the candidate profile below, generate realistic monthly salary benchmarks for each target market they specified.

CANDIDATE:
- Primary Track: {primary_track}
- Effective Level: {level}
- Years of Experience: {years_exp}
- Domain Experience: {domains}
- Key Stack: {stack}

TARGET MARKETS: {markets}

INSTRUCTIONS:
- Use current market rates (2025-2026)
- Be realistic and conservative, not optimistic
- Consider the candidate's specific stack and domain — fintech/CDP commands premium over general e-commerce
- For each country, provide a monthly range in local currency
- Add a one-line basis explaining the range
- If a market is not in your knowledge (e.g. niche location), say "Insufficient data"

Return ONLY this exact markdown format, no preamble:

## Salary Benchmarks

### {Country 1}
- Range: {currency} {min}k - {max}k/month
- Basis: {one line explanation}

### {Country 2}
- Range: {currency} {min}k - {max}k/month
- Basis: {one line explanation}

(repeat for each target market)
"""


def generate_salary_benchmarks(profile_md: str, markets: str) -> str:
    """
    Parse key fields from profile markdown and generate salary benchmarks via LLM.
    """
    import re

    def extract(pattern, text, default="Not stated"):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    primary_track = extract(r"Primary Track:\s*(.+)", profile_md)
    level = extract(r"Effective Level:\s*(.+)", profile_md)
    years_exp = extract(r"Years of Experience:\s*(.+)", profile_md)
    domains = extract(r"## Domain Experience\n([\s\S]+?)(?=\n##|$)", profile_md)
    stack_section = extract(r"### Production-grade.*?\n([\s\S]+?)(?=\n###|\n##|$)", profile_md)

    prompt = SALARY_BENCHMARK_PROMPT.format(
        primary_track=primary_track,
        level=level,
        years_exp=years_exp,
        domains=domains[:300],
        stack=stack_section[:300],
        markets=markets,
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

    return response.choices[0].message.content.strip()