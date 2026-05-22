from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Resume


async def get_by_user_id(session: AsyncSession, user_id: int) -> Resume | None:
    result = await session.execute(select(Resume).where(Resume.user_id == user_id))
    return result.scalar_one_or_none()


async def upsert(
    session: AsyncSession,
    user_id: int,
    *,
    filename: str,
    file_path: str,
    extracted_skills: str,
) -> Resume:
    existing = await get_by_user_id(session, user_id)
    if existing is not None:
        existing.filename = filename
        existing.file_path = file_path
        existing.extracted_skills = extracted_skills
        await session.commit()
        await session.refresh(existing)
        return existing

    row = Resume(
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        extracted_skills=extracted_skills,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def delete_for_user(session: AsyncSession, user_id: int) -> bool:
    row = await get_by_user_id(session, user_id)
    if row is None:
        return False
    await session.delete(row)
    await session.commit()
    return True
