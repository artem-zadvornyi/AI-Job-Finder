from __future__ import annotations

from typing import Any

from core.constants import PROCESSED_CALLBACKS_KEY, SESSION_SAVED_LINKS_KEY


def try_claim_callback(user_data: dict[str, Any], callback_query_id: str) -> bool:
    """
    Return True if this callback may be processed.

    Prevents double-processing when users tap buttons repeatedly.
    """
    seen: set[str] = user_data.setdefault(PROCESSED_CALLBACKS_KEY, set())
    if callback_query_id in seen:
        return False
    seen.add(callback_query_id)
    if len(seen) > 200:
        seen.clear()
        seen.add(callback_query_id)
    return True


def is_link_saved_in_session(user_data: dict[str, Any], link: str) -> bool:
    normalized = (link or "").strip()
    if not normalized:
        return False
    saved: set[str] = user_data.setdefault(SESSION_SAVED_LINKS_KEY, set())
    return normalized in saved


def mark_link_saved_in_session(user_data: dict[str, Any], link: str) -> None:
    normalized = (link or "").strip()
    if normalized:
        user_data.setdefault(SESSION_SAVED_LINKS_KEY, set()).add(normalized)
