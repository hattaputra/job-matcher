import os
from pathlib import Path
from datetime import datetime

PROFILES_DIR = Path(__file__).parent.parent / "profiles"
PROFILES_DIR.mkdir(exist_ok=True)


def profile_path(sender_id: int) -> Path:
    return PROFILES_DIR / f"{sender_id}.md"


def profile_exists(sender_id: int) -> bool:
    return profile_path(sender_id).exists()


def load_profile(sender_id: int) -> str:
    path = profile_path(sender_id)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def save_profile(sender_id: int, content: str):
    profile_path(sender_id).write_text(content, encoding="utf-8")


def append_preferences(sender_id: int, preferences: dict):
    """Append user preferences to existing profile."""
    existing = load_profile(sender_id)

    prefs_section = f"""
## Job Preferences

### Target Markets & Salary Expectations
{preferences.get('markets', 'Not specified')}

### Work Arrangement
{preferences.get('work_arrangement', 'Not specified')}

### Employment Type
{preferences.get('employment_type', 'Permanent / Full-time only')}

### Relocation
{preferences.get('relocation', 'Not specified')}
"""
    updated = existing + prefs_section
    save_profile(sender_id, updated)


def generate_profile_from_cv(sender_id: int, cv_text: str, llm_profile: str):
    """Save LLM-generated profile from CV extraction."""
    content = f"""# Candidate Profile
Generated: {datetime.now().strftime('%Y-%m-%d')}
Sender ID: {sender_id}

{llm_profile}
"""
    save_profile(sender_id, content)


def delete_profile(sender_id: int):
    path = profile_path(sender_id)
    if path.exists():
        path.unlink()


def append_salary_benchmarks(sender_id: int, salary_md: str):
    """Append LLM-generated salary benchmarks to existing profile."""
    existing = load_profile(sender_id)
    updated = existing + "" + salary_md
    save_profile(sender_id, updated)