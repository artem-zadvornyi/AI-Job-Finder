from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserPreference


async def get_by_user_id(session: AsyncSession, user_id: int) -> UserPreference | None:
    result = await session.execute(select(UserPreference).where(UserPreference.user_id == user_id))
    return result.scalar_one_or_none()


async def upsert_preferences(
    session: AsyncSession,
    user_id: int,
    *,
    keyword: str,
    location: str,
    work_type: str,
) -> UserPreference:
    pref = await get_by_user_id(session, user_id)
    if pref is None:
        pref = UserPreference(user_id=user_id)
        session.add(pref)

    pref.keyword = keyword
    pref.location = location
    pref.work_type = work_type
    await session.commit()
    return pref


async def set_alerts_enabled(
    session: AsyncSession,
    user_id: int,
    *,
    enabled: bool,
) -> UserPreference | None:
    pref = await get_by_user_id(session, user_id)
    if pref is None:
        return None

    pref.alerts_enabled = enabled
    await session.commit()
    return pref


async def list_with_alerts_enabled(session: AsyncSession) -> list[UserPreference]:
    result = await session.execute(
        select(UserPreference).where(
            UserPreference.alerts_enabled.is_(True),
            UserPreference.keyword != "",
            UserPreference.location != "",
        )
    )
    return list(result.scalars().all())


async def count_total(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(UserPreference))
    return int(result.scalar_one())


async def count_with_alerts_enabled(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(UserPreference)
        .where(UserPreference.alerts_enabled.is_(True))
    )
    return int(result.scalar_one())
