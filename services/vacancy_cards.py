from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from core.constants import (
    ALERT_SAVE_CALLBACK_PREFIX,
    DELETE_SAVED_CALLBACK_PREFIX,
    DESCRIPTION_PREVIEW_CHARS,
    JOB_SOURCE_REMOTIVE,
    JOBS_CALLBACK_PREFIX,
    RESUME_MAX_MATCHED_SKILLS_DISPLAY,
)
from services.remotive_api import Vacancy


def _format_source(source: str) -> str:
    if source == JOB_SOURCE_REMOTIVE:
        return "Remotive (remotive.com)"
    return source


def _format_ai_match_block(
    match_score: int | None,
    matched_skills: tuple[str, ...] | list[str] | None,
) -> str:
    if match_score is None:
        return ""
    skills = list(matched_skills or ())[:RESUME_MAX_MATCHED_SKILLS_DISPLAY]
    block = f"\n\n🤖 AI Match: {match_score}%"
    if skills:
        lines = "\n".join(f"• {skill}" for skill in skills)
        block += f"\nMatched skills:\n{lines}"
    return block


def format_vacancy_card(
    *,
    title: str,
    company: str,
    location: str,
    salary: str | None,
    source: str,
    description: str,
    page_index: int | None = None,
    page_total: int | None = None,
    match_score: int | None = None,
    matched_skills: tuple[str, ...] | list[str] | None = None,
) -> str:
    """Plain-text card body (emoji headers + short description)."""
    salary_text = salary if salary else "Not specified"
    desc = (description or "").strip()
    if len(desc) > DESCRIPTION_PREVIEW_CHARS:
        desc = desc[: DESCRIPTION_PREVIEW_CHARS - 1] + "…"
    if not desc:
        desc = "—"

    body = (
        f"💼 {title}\n"
        f"🏢 {company}\n"
        f"🌍 {location}\n"
        f"💰 {salary_text}\n"
        f"📌 {_format_source(source)}\n"
        f"\n{desc}"
    )
    body += _format_ai_match_block(match_score, matched_skills)
    if page_index is not None and page_total is not None and page_total > 0:
        body += f"\n\n📄 {page_index + 1} / {page_total}"
    return body


def format_vacancy_from_dict(
    vacancy: dict[str, str | None],
    *,
    page_index: int | None = None,
    page_total: int | None = None,
) -> str:
    match_score_raw = vacancy.get("match_score")
    match_score: int | None = None
    if match_score_raw is not None:
        try:
            match_score = int(match_score_raw)
        except (TypeError, ValueError):
            match_score = None

    matched_raw = vacancy.get("matched_skills")
    matched: tuple[str, ...] = ()
    if isinstance(matched_raw, str) and matched_raw:
        matched = tuple(s.strip() for s in matched_raw.split(",") if s.strip())
    elif isinstance(matched_raw, list | tuple):
        matched = tuple(str(s) for s in matched_raw if s)

    return format_vacancy_card(
        title=str(vacancy.get("title") or "Untitled role"),
        company=str(vacancy.get("company") or "Unknown company"),
        location=str(vacancy.get("location") or "Remote"),
        salary=vacancy.get("salary"),
        source=str(vacancy.get("source") or JOB_SOURCE_REMOTIVE),
        description=str(vacancy.get("description") or ""),
        page_index=page_index,
        page_total=page_total,
        match_score=match_score,
        matched_skills=matched,
    )


def format_saved_vacancy_card(
    *,
    title: str,
    company: str,
    location: str,
    salary: str | None,
    source: str,
    link: str,
) -> str:
    """Card for /saved listings (includes link, no description block)."""
    salary_text = salary if salary else "Not specified"
    link_text = link if link else "No link"
    return (
        f"💼 {title}\n"
        f"🏢 {company}\n"
        f"🌍 {location}\n"
        f"💰 {salary_text}\n"
        f"📌 {_format_source(source)}\n"
        f"🔗 {link_text}"
    )


def format_saved_vacancy_from_row(job) -> str:
    """Build saved card text from a SavedJob ORM row."""
    return format_saved_vacancy_card(
        title=job.title,
        company=job.company,
        location=job.location,
        salary=job.salary,
        source=job.source,
        link=job.link,
    )


def format_vacancy_from_model(vacancy: Vacancy) -> str:
    return format_vacancy_card(
        title=vacancy.title,
        company=vacancy.company,
        location=vacancy.location,
        salary=vacancy.salary,
        source=vacancy.source,
        description=vacancy.description,
        match_score=vacancy.match_score,
        matched_skills=vacancy.matched_skills,
    )


def _jobs_callback_data(page_index: int, action: str) -> str:
    return f"{JOBS_CALLBACK_PREFIX}{page_index}:{action}"


def jobs_pagination_keyboard(
    *,
    page_index: int,
    total: int,
    link: str,
) -> InlineKeyboardMarkup:
    """Navigation + Save + Open URL for paginated /jobs view."""
    nav_row: list[InlineKeyboardButton] = []
    if page_index > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅ Previous",
                callback_data=_jobs_callback_data(page_index, "p"),
            )
        )
    if page_index < total - 1:
        nav_row.append(
            InlineKeyboardButton(
                text="Next ➡",
                callback_data=_jobs_callback_data(page_index, "n"),
            )
        )

    action_row = [
        InlineKeyboardButton(
            text="🔖 Save",
            callback_data=_jobs_callback_data(page_index, "s"),
        ),
    ]
    if link:
        action_row.append(InlineKeyboardButton(text="🌐 Open Vacancy", url=link))

    rows: list[list[InlineKeyboardButton]] = []
    if nav_row:
        rows.append(nav_row)
    rows.append(action_row)
    return InlineKeyboardMarkup(rows)


def alert_vacancy_keyboard(*, link: str, index: int) -> InlineKeyboardMarkup:
    """Save + Open for automatic alert messages."""
    row = [
        InlineKeyboardButton(
            text="🔖 Save",
            callback_data=f"{ALERT_SAVE_CALLBACK_PREFIX}{index}",
        ),
    ]
    if link:
        row.append(InlineKeyboardButton(text="🌐 Open Vacancy", url=link))
    return InlineKeyboardMarkup([row])


def vacancy_inline_keyboard(*, link: str, index: int) -> InlineKeyboardMarkup:
    """Legacy keyboard — kept for compatibility in tests."""
    return jobs_pagination_keyboard(page_index=index, total=max(index + 1, 1), link=link)


def saved_vacancy_inline_keyboard(*, link: str, saved_id: int) -> InlineKeyboardMarkup:
    """Delete (callback) + Open Vacancy (URL) under each saved card."""
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="🗑 Delete",
                callback_data=f"{DELETE_SAVED_CALLBACK_PREFIX}{saved_id}",
            ),
        ]
    ]
    if link:
        rows[0].append(
            InlineKeyboardButton(text="🌐 Open Vacancy", url=link),
        )
    return InlineKeyboardMarkup(rows)


def vacancy_to_cache_dict(vacancy: Vacancy) -> dict[str, str | None]:
    matched = ",".join(vacancy.matched_skills) if vacancy.matched_skills else None
    return {
        "title": vacancy.title,
        "company": vacancy.company,
        "location": vacancy.location,
        "salary": vacancy.salary,
        "link": vacancy.link,
        "source": vacancy.source,
        "description": vacancy.description,
        "match_score": str(vacancy.match_score) if vacancy.match_score is not None else None,
        "matched_skills": matched,
    }
