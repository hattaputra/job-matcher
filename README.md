# Job Matcher API

AI-powered job description analyzer for Senior Data Engineers. Send a LinkedIn job URL, get a structured fit score and analysis back — designed to integrate with a Telegram bot for on-the-go job hunting.

## Architecture

```
Telegram Bot (PicoClaw)
        ↓
Job Matcher API  ←── this repo
        ↓
LinkedIn (fetch JD via requests)
        ↓
Local LLM via Ollama (Qwen3:8b)
        ↓
Structured JSON rating
```

## Features

- Fetch LinkedIn job descriptions without a browser
- AI-powered scoring against a configurable candidate profile
- Returns structured JSON: score, stack match, red flags, summary
- Integrates with any Telegram bot as a backend tool
- Runs fully local — no external API costs

## Quick Start

**1. Clone and configure**

```bash
git clone https://github.com/yourusername/job-matcher.git
cd job-matcher
cp .env.example .env
# Edit .env and add your LinkedIn cookie and Ollama settings
```

**2. Get your LinkedIn cookie**

Open LinkedIn in Chrome → F12 → Application → Cookies → `www.linkedin.com` → copy `li_at` value → paste into `.env`

**3. Make sure Ollama is running**

```bash
ollama pull qwen3:8b
ollama serve
```

**4. Run the API**

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or with Docker:

```bash
docker compose up --build
```

**5. Test it**

```bash
curl -X POST http://localhost:8000/api/v1/rate-job \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.linkedin.com/jobs/view/1234567890/"}'
```

## Example Response

```json
{
  "url": "https://www.linkedin.com/jobs/view/1234567890/",
  "rating": {
    "score": 8,
    "stack_match": ["Python", "BigQuery", "Airflow", "GCP"],
    "stack_missing": ["dbt"],
    "seniority_match": true,
    "remote_friendly": true,
    "highlights": [
      "Strong GCP stack alignment",
      "Remote-first company",
      "Senior-level scope and autonomy"
    ],
    "red_flags": [
      "Requires dbt experience (not in current stack)"
    ],
    "summary": "Strong fit overall. Stack aligns well with GCP and Airflow experience. The dbt requirement is a minor gap but learnable. Remote policy and seniority level are both a match.",
    "raw_title": "Senior Data Engineer",
    "raw_company": "Example Corp"
  },
  "jd_excerpt": "We are looking for a Senior Data Engineer to join our growing data platform team..."
}
```

## Candidate Profile

The scoring prompt is in `app/prompts/job_rating.txt`. Edit it to match your own profile, target markets, and preferences.

## Project Structure

```
job-matcher/
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Settings from environment variables
│   ├── models.py         # Pydantic request/response models
│   ├── routers/
│   │   └── jobs.py       # /rate-job endpoint
│   ├── services/
│   │   ├── fetcher.py    # LinkedIn HTML fetcher
│   │   └── rater.py      # Ollama LLM rating service
│   └── prompts/
│       └── job_rating.txt  # Scoring prompt (edit to your profile)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── .gitignore
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LINKEDIN_COOKIE` | - | Your `li_at` session cookie from LinkedIn |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama API base URL |
| `OLLAMA_MODEL` | `qwen3:8b` | Model to use for rating |
| `OLLAMA_TIMEOUT` | `300` | LLM request timeout in seconds |
| `REQUEST_TIMEOUT` | `30` | LinkedIn fetch timeout in seconds |

## Tech Stack

- **FastAPI** — API framework
- **Ollama** — Local LLM inference
- **Qwen3:8b** — Reasoning model for job analysis
- **BeautifulSoup4** — HTML parsing
- **Docker** — Containerization

## License

MIT
