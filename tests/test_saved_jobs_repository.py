from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import saved_jobs_repository as repo


@pytest.mark.asyncio
async def test_create_and_list_saved_jobs(db_session: AsyncSession) -> None:
    user_id = 1001
    await repo.create(
        db_session,
        user_id,
        title="Python Developer",
        company="Acme",
        location="Remote",
        salary="$90k",
        link="https://example.com/jobs/1",
        source="Remotive",
    )
    jobs = await repo.list_by_user(db_session, user_id)
    assert len(jobs) == 1
    assert jobs[0].title == "Python Developer"
    assert jobs[0].link == "https://example.com/jobs/1"


@pytest.mark.asyncio
async def test_find_by_user_and_link_detects_duplicate(db_session: AsyncSession) -> None:
    user_id = 2002
    link = "https://example.com/jobs/dup"
    await repo.create(
        db_session,
        user_id,
        title="Role A",
        company="Co",
        location="Remote",
        salary=None,
        link=link,
        source="Remotive",
    )
    found_id = await repo.find_by_user_and_link(db_session, user_id, link)
    assert found_id is not None
    missing = await repo.find_by_user_and_link(db_session, user_id, "https://other.com")
    assert missing is None


@pytest.mark.asyncio
async def test_delete_saved_job(db_session: AsyncSession) -> None:
    user_id = 3003
    job = await repo.create(
        db_session,
        user_id,
        title="To Delete",
        company="Co",
        location="Remote",
        salary=None,
        link="https://example.com/delete",
        source="Remotive",
    )
    loaded = await repo.get_by_id_for_user(db_session, user_id, job.id)
    assert loaded is not None
    await repo.delete(db_session, loaded)
    assert await repo.get_by_id_for_user(db_session, user_id, job.id) is None


@pytest.mark.asyncio
async def test_count_all_saved_jobs(db_session: AsyncSession) -> None:
    assert await repo.count_all(db_session) == 0
    await repo.create(
        db_session,
        1,
        title="A",
        company="C",
        location="R",
        salary=None,
        link="https://example.com/a",
        source="Remotive",
    )
    assert await repo.count_all(db_session) == 1
