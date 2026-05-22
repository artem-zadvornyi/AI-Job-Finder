from __future__ import annotations

from services.remotive_api import (
    _final_relevance_score,
    _is_python_developer_search,
    _plain_text,
    _rank_jobs,
)


def _job(
    *,
    title: str,
    description: str = "",
    url: str = "https://remotive.com/remote-jobs/1",
    category: str = "software-dev",
) -> dict:
    return {
        "title": title,
        "company_name": "Test Co",
        "description": description,
        "url": url,
        "category": category,
        "candidate_required_location": "Worldwide",
    }


def test_is_python_developer_search() -> None:
    assert _is_python_developer_search("Python developer") is True
    assert _is_python_developer_search("backend engineer") is False


def test_rank_jobs_prefers_python_backend() -> None:
    jobs = [
        _job(title="Senior Sales Manager", description="B2B sales"),
        _job(
            title="Junior Python Backend Developer",
            description="Python FastAPI PostgreSQL",
        ),
        _job(title="Marketing Copywriter", description="content writing"),
    ]
    ranked = _rank_jobs(jobs, "Python developer")
    assert len(ranked) >= 1
    assert "Python" in ranked[0][0]["title"]


def test_rank_jobs_excludes_hard_blocked_titles() -> None:
    jobs = [
        _job(title="Office Assistant", description="admin tasks"),
        _job(title="Python API Developer", description="Python REST API"),
    ]
    ranked = _rank_jobs(jobs, "Python developer")
    titles = [j["title"] for j, _ in ranked]
    assert "Office Assistant" not in titles


def test_rank_jobs_limits_to_five() -> None:
    jobs = [
        _job(
            title=f"Python Developer {i}",
            description="Python backend developer API",
        )
        for i in range(10)
    ]
    ranked = _rank_jobs(jobs, "Python developer")
    assert len(ranked) <= 5


def test_final_relevance_score_higher_for_python_in_title() -> None:
    plain = _plain_text("Python Django REST API for backend services")
    python_job = _job(title="Python Backend Developer", description=plain)
    sales_job = _job(title="Sales Representative", description="sales targets")
    python_score = _final_relevance_score(python_job, "Python developer", plain)
    sales_score = _final_relevance_score(sales_job, "Python developer", plain)
    assert python_score > sales_score
