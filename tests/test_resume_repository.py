from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import resume_repository as resume_repo
from services.resume_parser import ParsedResume


@pytest.mark.asyncio
async def test_resume_upsert_and_replace(db_session: AsyncSession) -> None:
    user_id = 9001
    profile = ParsedResume(
        skills=("Python",), technologies=(), experience_keywords=(), education_keywords=()
    )

    first = await resume_repo.upsert(
        db_session,
        user_id,
        filename="v1.pdf",
        file_path="/tmp/v1.pdf",
        extracted_skills=profile.to_json(),
    )
    assert first.filename == "v1.pdf"

    second = await resume_repo.upsert(
        db_session,
        user_id,
        filename="v2.docx",
        file_path="/tmp/v2.docx",
        extracted_skills=profile.to_json(),
    )
    assert second.filename == "v2.docx"

    row = await resume_repo.get_by_user_id(db_session, user_id)
    assert row is not None
    assert row.filename == "v2.docx"


@pytest.mark.asyncio
async def test_resume_delete(db_session: AsyncSession) -> None:
    user_id = 9002
    profile = ParsedResume(
        skills=("Go",), technologies=(), experience_keywords=(), education_keywords=()
    )
    await resume_repo.upsert(
        db_session,
        user_id,
        filename="resume.pdf",
        file_path="/tmp/resume.pdf",
        extracted_skills=profile.to_json(),
    )
    deleted = await resume_repo.delete_for_user(db_session, user_id)
    assert deleted is True
    assert await resume_repo.get_by_user_id(db_session, user_id) is None
