from __future__ import annotations

from core.constants import JOB_SEARCH_SUGGESTIONS, MSG_JOBS_EMPTY
from services.remotive_api import RemotiveAPI, Vacancy
from services.resume_matcher import rank_vacancies_by_resume
from services.resume_parser import ParsedResume


async def search_vacancies_for_user(
    remotive: RemotiveAPI,
    *,
    keyword: str,
    location: str,
    work_type: str,
    resume_profile: ParsedResume | None = None,
) -> list[Vacancy]:
    """Fetch ranked vacancies from Remotive (single API call per /jobs)."""
    vacancies = await remotive.search_jobs(
        keyword=keyword,
        location=location,
        work_type=work_type,
    )
    if resume_profile and resume_profile.all_match_terms():
        return rank_vacancies_by_resume(vacancies, resume_profile)
    return vacancies


def format_empty_results_message() -> str:
    suggestions = "\n".join(f"• {item}" for item in JOB_SEARCH_SUGGESTIONS)
    return MSG_JOBS_EMPTY.format(suggestions=suggestions)
