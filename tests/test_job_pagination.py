from __future__ import annotations

from services.job_pagination import (
    JobsNavAction,
    build_jobs_page_view,
    clamp_page_index,
    parse_jobs_callback,
    resolve_navigation_index,
)
from services.remotive_api import Vacancy
from services.vacancy_cache import get_jobs_results, store_jobs_results


def _sample_results() -> list[dict[str, str | None]]:
    return [
        {
            "title": "Python Developer",
            "company": "A",
            "location": "Remote",
            "salary": None,
            "link": "https://example.com/1",
            "source": "Remotive",
            "description": "Python APIs",
        },
        {
            "title": "Backend Engineer",
            "company": "B",
            "location": "Remote",
            "salary": None,
            "link": "https://example.com/2",
            "source": "Remotive",
            "description": "Backend services",
        },
        {
            "title": "FastAPI Developer",
            "company": "C",
            "location": "Remote",
            "salary": None,
            "link": "https://example.com/3",
            "source": "Remotive",
            "description": "FastAPI",
        },
    ]


def test_parse_jobs_callback_valid() -> None:
    parsed = parse_jobs_callback("jobs:1:n")
    assert parsed is not None
    assert parsed.page_index == 1
    assert parsed.action == JobsNavAction.NEXT


def test_parse_jobs_callback_invalid() -> None:
    assert parse_jobs_callback("save:1") is None
    assert parse_jobs_callback("jobs:1:x") is None
    assert parse_jobs_callback("jobs:-1:n") is None
    assert parse_jobs_callback(None) is None


def test_clamp_page_index() -> None:
    assert clamp_page_index(0, 3) == 0
    assert clamp_page_index(2, 3) == 2
    assert clamp_page_index(3, 3) is None
    assert clamp_page_index(-1, 3) is None


def test_resolve_navigation_index() -> None:
    assert resolve_navigation_index(1, JobsNavAction.PREV, 3) == 0
    assert resolve_navigation_index(1, JobsNavAction.NEXT, 3) == 2
    assert resolve_navigation_index(0, JobsNavAction.PREV, 3) is None
    assert resolve_navigation_index(2, JobsNavAction.NEXT, 3) is None


def test_build_jobs_page_view_first_page_hides_previous() -> None:
    results = _sample_results()
    text, markup = build_jobs_page_view(results, 0)  # type: ignore[misc]
    assert "1 / 3" in text
    assert "Python Developer" in text
    labels = [btn.text for row in markup.inline_keyboard for btn in row]
    assert "⬅ Previous" not in labels
    assert "Next ➡" in labels
    assert "🔖 Save" in labels


def test_build_jobs_page_view_last_page_hides_next() -> None:
    results = _sample_results()
    text, markup = build_jobs_page_view(results, 2)  # type: ignore[misc]
    assert "3 / 3" in text
    labels = [btn.text for row in markup.inline_keyboard for btn in row]
    assert "Next ➡" not in labels
    assert "⬅ Previous" in labels


def test_store_jobs_results_in_user_data() -> None:
    user_data: dict = {}
    vacancies = [
        Vacancy(
            title="Dev",
            company="Co",
            location="Remote",
            salary=None,
            link="https://example.com",
            source="Remotive",
            description="desc",
        )
    ]
    store_jobs_results(user_data, vacancies)
    assert len(get_jobs_results(user_data)) == 1
