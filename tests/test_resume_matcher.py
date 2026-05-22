from __future__ import annotations

from services.remotive_api import Vacancy
from services.resume_matcher import compute_match, rank_vacancies_by_resume
from services.resume_parser import ParsedResume


def _vacancy(title: str, description: str) -> Vacancy:
    return Vacancy(
        title=title,
        company="Co",
        location="Remote",
        salary=None,
        link="https://example.com/job",
        source="Remotive",
        description=description,
    )


def test_compute_match_high_score_for_matching_skills() -> None:
    profile = ParsedResume(
        skills=("Python", "FastAPI", "Docker"),
        technologies=("PostgreSQL",),
        experience_keywords=("Backend",),
        education_keywords=(),
    )
    vacancy = _vacancy(
        "Python Backend Developer",
        "Build APIs with FastAPI and Docker on PostgreSQL.",
    )
    result = compute_match(vacancy, profile)
    assert result.score >= 60
    assert "Python" in result.matched_skills
    assert "FastAPI" in result.matched_skills


def test_rank_vacancies_by_resume_orders_highest_first() -> None:
    profile = ParsedResume(
        skills=("Python", "FastAPI"),
        technologies=(),
        experience_keywords=(),
        education_keywords=(),
    )
    low = _vacancy("Marketing Manager", "Sales and growth.")
    high = _vacancy("Python FastAPI Developer", "Python FastAPI backend APIs.")
    ranked = rank_vacancies_by_resume([low, high], profile)
    assert ranked[0].title.startswith("Python")
    assert ranked[0].match_score is not None
    assert ranked[0].match_score >= (ranked[1].match_score or 0)
