from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import sent_jobs_repository as repo


@pytest.mark.asyncio
async def test_sent_job_not_exists_initially(db_session: AsyncSession) -> None:
    assert await repo.exists_for_user(db_session, 42, "https://example.com/v/1") is False


@pytest.mark.asyncio
async def test_create_and_exists_prevents_duplicate_alerts(db_session: AsyncSession) -> None:
    user_id = 99
    link = "https://example.com/vacancy/alert-1"
    await repo.create(db_session, user_id, link)
    assert await repo.exists_for_user(db_session, user_id, link) is True


@pytest.mark.asyncio
async def test_duplicate_sent_job_raises_integrity_error(db_session: AsyncSession) -> None:
    user_id = 77
    link = "https://example.com/vacancy/dup"
    await repo.create(db_session, user_id, link)
    with pytest.raises(IntegrityError):
        await repo.create(db_session, user_id, link)


@pytest.mark.asyncio
async def test_count_sent_jobs(db_session: AsyncSession) -> None:
    await repo.create(db_session, 1, "https://example.com/1")
    await repo.create(db_session, 2, "https://example.com/2")
    assert await repo.count_all(db_session) == 2
