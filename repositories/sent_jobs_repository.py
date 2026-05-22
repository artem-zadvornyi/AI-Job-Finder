from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import SentJob


async def exists_for_user(
    session: AsyncSession,
    user_id: int,
    vacancy_link: str,
) -> bool:
    result = await session.execute(
        select(SentJob.id).where(
            SentJob.user_id == user_id,
            SentJob.vacancy_link == vacancy_link,
        )
    )
    return result.scalar_one_or_none() is not None


async def create(session: AsyncSession, user_id: int, vacancy_link: str) -> None:
    session.add(SentJob(user_id=user_id, vacancy_link=vacancy_link))
    await session.commit()


async def count_all(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(SentJob))
    return int(result.scalar_one())
