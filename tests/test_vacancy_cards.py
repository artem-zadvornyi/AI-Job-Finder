from __future__ import annotations

from core.constants import DELETE_SAVED_CALLBACK_PREFIX, JOB_SOURCE_REMOTIVE
from services.remotive_api import Vacancy
from services.vacancy_cards import (
    alert_vacancy_keyboard,
    format_saved_vacancy_card,
    format_vacancy_card,
    format_vacancy_from_dict,
    format_vacancy_from_model,
    jobs_pagination_keyboard,
    saved_vacancy_inline_keyboard,
    vacancy_to_cache_dict,
)


def test_format_vacancy_card_includes_fields() -> None:
    text = format_vacancy_card(
        title="Python Developer",
        company="Acme",
        location="Remote · EU",
        salary="$80k",
        source=JOB_SOURCE_REMOTIVE,
        description="Build APIs with FastAPI.",
    )
    assert "Python Developer" in text
    assert "Acme" in text
    assert "Remotive" in text
    assert "FastAPI" in text


def test_format_vacancy_card_truncates_long_description() -> None:
    long_desc = "x" * 500
    text = format_vacancy_card(
        title="Role",
        company="Co",
        location="Remote",
        salary=None,
        source=JOB_SOURCE_REMOTIVE,
        description=long_desc,
    )
    assert "…" in text
    assert len(text) < len(long_desc) + 200


def test_format_saved_vacancy_card_includes_link() -> None:
    text = format_saved_vacancy_card(
        title="Backend Dev",
        company="Startup",
        location="Remote",
        salary=None,
        source=JOB_SOURCE_REMOTIVE,
        link="https://example.com/job/1",
    )
    assert "https://example.com/job/1" in text


def test_jobs_pagination_keyboard_callbacks() -> None:
    keyboard = jobs_pagination_keyboard(
        page_index=1,
        total=4,
        link="https://example.com/j",
    )
    callback_data = [
        btn.callback_data for row in keyboard.inline_keyboard for btn in row if btn.callback_data
    ]
    assert "jobs:1:p" in callback_data
    assert "jobs:1:n" in callback_data
    assert "jobs:1:s" in callback_data


def test_alert_vacancy_keyboard_prefix() -> None:
    keyboard = alert_vacancy_keyboard(link="https://example.com/j", index=2)
    assert keyboard.inline_keyboard[0][0].callback_data == "asv:2"


def test_format_vacancy_from_dict_page_footer() -> None:
    text = format_vacancy_from_dict(
        {
            "title": "Dev",
            "company": "Co",
            "location": "Remote",
            "salary": None,
            "link": "https://example.com",
            "source": "Remotive",
            "description": "Python",
        },
        page_index=0,
        page_total=2,
    )
    assert "1 / 2" in text


def test_saved_vacancy_inline_keyboard_delete_prefix() -> None:
    keyboard = saved_vacancy_inline_keyboard(link="https://example.com/j", saved_id=42)
    assert keyboard.inline_keyboard[0][0].callback_data == f"{DELETE_SAVED_CALLBACK_PREFIX}42"


def test_vacancy_to_cache_dict() -> None:
    vacancy = Vacancy(
        title="Dev",
        company="Co",
        location="Remote",
        salary=None,
        link="https://example.com",
        source=JOB_SOURCE_REMOTIVE,
        description="desc",
    )
    data = vacancy_to_cache_dict(vacancy)
    assert data["title"] == "Dev"
    assert data["link"] == "https://example.com"


def test_format_vacancy_from_model() -> None:
    vacancy = Vacancy(
        title="API Engineer",
        company="Tech",
        location="Remote · Worldwide",
        salary="100k",
        link="https://example.com/api",
        source=JOB_SOURCE_REMOTIVE,
        description="Python APIs",
    )
    text = format_vacancy_from_model(vacancy)
    assert "API Engineer" in text
