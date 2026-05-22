from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import MSG_ALREADY_SAVED, MSG_SAVED
from services.callback_guard import is_link_saved_in_session, mark_link_saved_in_session
from services.saved_jobs import save_vacancy


async def save_vacancy_from_cache(
    session: AsyncSession,
    user_data: dict[str, Any],
    user_id: int,
    vacancy: dict[str, str | None],
) -> tuple[str, str]:
    """
    Save a vacancy dict from session cache.

    Returns (user_message, status) where status is 'saved' | 'duplicate' | 'invalid'.
    """
    link = str(vacancy.get("link") or "").strip()
    if not link:
        return ("", "invalid")

    if is_link_saved_in_session(user_data, link):
        return (MSG_ALREADY_SAVED, "duplicate")

    result = await save_vacancy(
        session,
        user_id,
        title=str(vacancy.get("title") or ""),
        company=str(vacancy.get("company") or ""),
        location=str(vacancy.get("location") or ""),
        salary=vacancy.get("salary"),
        link=link,
        source=str(vacancy.get("source") or ""),
    )

    if result == "saved":
        mark_link_saved_in_session(user_data, link)
        return (MSG_SAVED, "saved")
    mark_link_saved_in_session(user_data, link)
    return (MSG_ALREADY_SAVED, "duplicate")
