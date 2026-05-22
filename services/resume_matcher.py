from __future__ import annotations

import re
from dataclasses import dataclass

from services.remotive_api import Vacancy
from services.resume_parser import ParsedResume

_TERM_WEIGHTS: dict[str, int] = {
    "skills": 14,
    "technologies": 12,
    "experience_keywords": 6,
    "education_keywords": 4,
}


@dataclass(frozen=True)
class MatchResult:
    score: int
    matched_skills: tuple[str, ...]


def _vacancy_text(vacancy: Vacancy) -> str:
    return f"{vacancy.title}\n{vacancy.description}".lower()


def _term_in_text(term: str, text: str) -> bool:
    escaped = re.escape(term.lower())
    return bool(re.search(rf"\b{escaped}\b", text, re.I))


def compute_match(vacancy: Vacancy, profile: ParsedResume) -> MatchResult:
    """Score 0–100 by comparing resume terms with vacancy title + description."""
    text = _vacancy_text(vacancy)
    matched: list[str] = []
    points = 0
    max_points = 0

    groups: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("skills", profile.skills),
        ("technologies", profile.technologies),
        ("experience_keywords", profile.experience_keywords),
        ("education_keywords", profile.education_keywords),
    )

    for group_name, terms in groups:
        weight = _TERM_WEIGHTS[group_name]
        for term in terms:
            max_points += weight
            if _term_in_text(term, text):
                points += weight
                if term not in matched:
                    matched.append(term)

    if max_points == 0:
        return MatchResult(score=0, matched_skills=())

    raw = int(round((points / max_points) * 100))
    score = max(0, min(100, raw))
    if score == 0 and matched:
        score = min(100, len(matched) * 15)

    display = tuple(matched[:8])
    return MatchResult(score=score, matched_skills=display)


def rank_vacancies_by_resume(
    vacancies: list[Vacancy],
    profile: ParsedResume,
) -> list[Vacancy]:
    """Re-rank vacancies by resume match score (highest first)."""
    if not profile.all_match_terms():
        return vacancies

    scored: list[tuple[Vacancy, int, tuple[str, ...]]] = []
    for vacancy in vacancies:
        result = compute_match(vacancy, profile)
        scored.append(
            (
                Vacancy(
                    title=vacancy.title,
                    company=vacancy.company,
                    location=vacancy.location,
                    salary=vacancy.salary,
                    link=vacancy.link,
                    source=vacancy.source,
                    description=vacancy.description,
                    match_score=result.score,
                    matched_skills=result.matched_skills,
                ),
                result.score,
                result.matched_skills,
            )
        )

    scored.sort(key=lambda item: item[1], reverse=True)
    return [item[0] for item in scored]
