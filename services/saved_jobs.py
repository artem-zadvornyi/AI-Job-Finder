from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import (
    MSG_ALREADY_DELETED,
    MSG_ALREADY_SAVED,
    MSG_DELETED,
    MSG_NO_SAVED,
    MSG_SAVED,
)
from models import SavedJob
from repositories import saved_jobs_repository as saved_repo

__all__ = (
    "MSG_SAVED",
    "MSG_ALREADY_SAVED",
    "MSG_NO_SAVED",
    "MSG_DELETED",
    "MSG_ALREADY_DELETED",
    "save_vacancy",
    "list_saved_jobs",
    "delete_saved_job",
)


async def save_vacancy(
    session: AsyncSession,
    user_id: int,
    *,
    title: str,
    company: str,
    location: str,
    salary: str | None,
    link: str,
    source: str,
) -> str:
    """
    Save a vacancy for a user.

    Returns:
        "saved" if inserted, "duplicate" if user_id + link already exists.
    """
    link = (link or "").strip()
    if not link:
        return "duplicate"

    if await saved_repo.find_by_user_and_link(session, user_id, link) is not None:
        return "duplicate"

    await saved_repo.create(
        session,
        user_id,
        title=title,
        company=company,
        location=location,
        salary=salary,
        link=link,
        source=source,
    )
    return "saved"


async def list_saved_jobs(session: AsyncSession, user_id: int) -> list[SavedJob]:
    return await saved_repo.list_by_user(session, user_id)


async def delete_saved_job(session: AsyncSession, user_id: int, job_id: int) -> str:
    """
    Delete one saved vacancy for a user.

    Returns:
        "deleted" if removed, "not_found" if id missing or belongs to another user.
    """
    job = await saved_repo.get_by_id_for_user(session, user_id, job_id)
    if job is None:
        return "not_found"

    await saved_repo.delete(session, job)
    return "deleted"
