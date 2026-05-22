from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.constants import (
    JOBS_CALLBACK_PREFIX,
    MSG_JOBS_BOUNDARY_FIRST,
    MSG_JOBS_BOUNDARY_LAST,
)
from services.vacancy_cards import format_vacancy_from_dict, jobs_pagination_keyboard

_JOBS_CALLBACK_RE = re.compile(rf"^{re.escape(JOBS_CALLBACK_PREFIX)}(\d+):([pns])$")


class JobsNavAction(str, Enum):
    PREV = "p"
    NEXT = "n"
    SAVE = "s"


@dataclass(frozen=True)
class ParsedJobsCallback:
    page_index: int
    action: JobsNavAction


def parse_jobs_callback(data: str | None) -> ParsedJobsCallback | None:
    if not data:
        return None
    match = _JOBS_CALLBACK_RE.match(data.strip())
    if not match:
        return None
    try:
        page_index = int(match.group(1))
        action = JobsNavAction(match.group(2))
    except (ValueError, KeyError):
        return None
    if page_index < 0:
        return None
    return ParsedJobsCallback(page_index=page_index, action=action)


def clamp_page_index(index: int, total: int) -> int | None:
    """Return a valid page index or None if out of range."""
    if total <= 0:
        return None
    if index < 0 or index >= total:
        return None
    return index


def resolve_navigation_index(current_index: int, action: JobsNavAction, total: int) -> int | None:
    """Compute target page after prev/next, or None if move is invalid."""
    if total <= 0:
        return None
    if action == JobsNavAction.PREV:
        if current_index <= 0:
            return None
        return current_index - 1
    if action == JobsNavAction.NEXT:
        if current_index >= total - 1:
            return None
        return current_index + 1
    return None


def boundary_message(action: JobsNavAction) -> str | None:
    if action == JobsNavAction.PREV:
        return MSG_JOBS_BOUNDARY_FIRST
    if action == JobsNavAction.NEXT:
        return MSG_JOBS_BOUNDARY_LAST
    return None


def build_jobs_page_view(
    results: list[dict[str, str | None]],
    page_index: int,
) -> tuple[str, Any] | None:
    """
    Build card text and keyboard for one page.

    Returns None if index is invalid.
    """
    safe_index = clamp_page_index(page_index, len(results))
    if safe_index is None:
        return None

    vacancy = results[safe_index]
    text = format_vacancy_from_dict(
        vacancy,
        page_index=safe_index,
        page_total=len(results),
    )
    link = str(vacancy.get("link") or "")
    markup = jobs_pagination_keyboard(
        page_index=safe_index,
        total=len(results),
        link=link,
    )
    return text, markup
