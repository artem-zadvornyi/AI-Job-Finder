from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import SavedJob


async def find_by_user_and_link(
    session: AsyncSession,
    user_id: int,
    link: str,
) -> int | None:
    result = await session.execute(
        select(SavedJob.id).where(
            SavedJob.user_id == user_id,
            SavedJob.link == link,
        )
    )
    row = result.scalar_one_or_none()
    return int(row) if row is not None else None


async def create(
    session: AsyncSession,
    user_id: int,
    *,
    title: str,
    company: str,
    location: str,
    salary: str | None,
    link: str,
    source: str,
) -> SavedJob:
    job = SavedJob(
        user_id=user_id,
        title=title,
        company=company,
        location=location,
        salary=salary,
        link=link,
        source=source,
    )
    session.add(job)
    await session.commit()
    return job


async def list_by_user(session: AsyncSession, user_id: int) -> list[SavedJob]:
    result = await session.execute(
        select(SavedJob).where(SavedJob.user_id == user_id).order_by(SavedJob.created_at.desc())
    )
    return list(result.scalars().all())


async def get_by_id_for_user(
    session: AsyncSession,
    user_id: int,
    job_id: int,
) -> SavedJob | None:
    result = await session.execute(
        select(SavedJob).where(
            SavedJob.id == job_id,
            SavedJob.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def delete(session: AsyncSession, job: SavedJob) -> None:
    await session.delete(job)
    await session.commit()


async def count_all(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(SavedJob))
    return int(result.scalar_one())
