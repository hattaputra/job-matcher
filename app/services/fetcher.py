import requests
from bs4 import BeautifulSoup
from app.config import settings


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_jd(url: str) -> dict:
    """
    Fetch job description from LinkedIn URL.
    Tries unauthenticated first, falls back to cookie-based auth.
    Returns dict with title, company, location, and full jd_text.
    """
    cookies = {}
    if settings.linkedin_cookie:
        cookies["li_at"] = settings.linkedin_cookie

    response = requests.get(
        url,
        headers=HEADERS,
        cookies=cookies,
        timeout=settings.request_timeout,
        allow_redirects=True,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = _extract_text(soup, [
        "h1.top-card-layout__title",
        "h1.job-details-jobs-unified-top-card__job-title",
        "h1",
    ])

    company = _extract_text(soup, [
        "a.topcard__org-name-link",
        "span.top-card-layout__second-subline",
        ".job-details-jobs-unified-top-card__company-name",
    ])

    location = _extract_text(soup, [
        "span.topcard__flavor--bullet",
        ".job-details-jobs-unified-top-card__bullet",
    ])

    jd_text = _extract_text(soup, [
        "div.description__text",
        "div.job-details-jobs-unified-top-card__job-insight",
        "div#job-details",
        "section.description",
    ])

    # Fallback: grab all visible text if selectors miss
    if not jd_text:
        jd_text = soup.get_text(separator=" ", strip=True)[:5000]

    return {
        "title": title,
        "company": company,
        "location": location,
        "jd_text": jd_text,
    }


def _extract_text(soup: BeautifulSoup, selectors: list) -> str:
    for selector in selectors:
        el = soup.select_one(selector)
        if el:
            return el.get_text(separator=" ", strip=True)
    return ""
