from __future__ import annotations

from typing import Any

from core.constants import ALERT_VACANCY_CACHE_KEY, JOBS_PAGE_INDEX_KEY, JOBS_RESULTS_KEY
from services.remotive_api import Vacancy
from services.vacancy_cards import vacancy_to_cache_dict


def store_jobs_results(user_data: dict[str, Any], vacancies: list[Vacancy]) -> None:
    """Persist search results for instant pagination (no extra API calls)."""
    user_data[JOBS_RESULTS_KEY] = [vacancy_to_cache_dict(v) for v in vacancies]
    user_data[JOBS_PAGE_INDEX_KEY] = 0


def get_jobs_results(user_data: dict[str, Any]) -> list[dict[str, str | None]]:
    raw = user_data.get(JOBS_RESULTS_KEY)
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def get_jobs_page_index(user_data: dict[str, Any]) -> int:
    try:
        return max(0, int(user_data.get(JOBS_PAGE_INDEX_KEY, 0)))
    except (TypeError, ValueError):
        return 0


def set_jobs_page_index(user_data: dict[str, Any], index: int) -> None:
    user_data[JOBS_PAGE_INDEX_KEY] = index


def get_vacancy_at(user_data: dict[str, Any], index: int) -> dict[str, str | None] | None:
    results = get_jobs_results(user_data)
    if index < 0 or index >= len(results):
        return None
    return results[index]


def store_alert_results(user_data: dict[str, Any], vacancies: list[dict[str, str | None]]) -> None:
    user_data[ALERT_VACANCY_CACHE_KEY] = {str(i): v for i, v in enumerate(vacancies)}


def get_alert_vacancy(user_data: dict[str, Any], index: int) -> dict[str, str | None] | None:
    cache = user_data.get(ALERT_VACANCY_CACHE_KEY, {})
    if not isinstance(cache, dict):
        return None
    item = cache.get(str(index))
    return item if isinstance(item, dict) else None
