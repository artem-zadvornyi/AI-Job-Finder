from __future__ import annotations

import logging
from datetime import UTC

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot

from core.constants import (
    MSG_RESUME_DELETED,
    MSG_RESUME_INVALID_FILE,
    MSG_RESUME_NO_SKILLS,
    MSG_RESUME_NONE,
    MSG_RESUME_SAVED,
)
from repositories import resume_repository as resume_repo
from services.resume_parser import ParsedResume, parse_resume_bytes
from services.resume_storage import delete_user_resume_files, save_resume_file

logger = logging.getLogger(__name__)


def load_parsed_profile(extracted_skills: str | None) -> ParsedResume | None:
    if not extracted_skills:
        return None
    return ParsedResume.from_json(extracted_skills)


async def get_user_resume_profile(
    session: AsyncSession,
    user_id: int,
) -> tuple[ParsedResume | None, object | None]:
    """Return (parsed profile, ORM row) for a user."""
    row = await resume_repo.get_by_user_id(session, user_id)
    if row is None:
        return None, None
    return load_parsed_profile(row.extracted_skills), row


def format_skills_summary(profile: ParsedResume) -> str:
    terms = list(profile.skills) + [t for t in profile.technologies if t not in profile.skills]
    if not terms:
        return "—"
    return ", ".join(terms[:12])


def format_my_resume_message(row) -> str:
    profile = load_parsed_profile(row.extracted_skills)
    if profile is None:
        profile = ParsedResume((), (), (), ())

    uploaded = row.uploaded_at
    if uploaded.tzinfo is None:
        uploaded = uploaded.replace(tzinfo=UTC)
    uploaded_str = uploaded.strftime("%Y-%m-%d %H:%M UTC")

    skills = format_skills_summary(profile)
    tech = ", ".join(profile.technologies[:8]) or "—"
    exp = ", ".join(profile.experience_keywords[:6]) or "—"

    return (
        "📄 Your resume profile\n\n"
        f"📎 File: {row.filename}\n"
        f"📅 Uploaded: {uploaded_str}\n\n"
        f"🛠 Skills: {skills}\n"
        f"⚙️ Technologies: {tech}\n"
        f"💼 Experience keywords: {exp}\n\n"
        "Use /jobs for AI-ranked matches or /resume to replace this file."
    )


async def save_resume_from_telegram(
    session: AsyncSession,
    *,
    user_id: int,
    bot: Bot,
    file_id: str,
    filename: str,
    file_size: int | None,
    mime_type: str | None,
) -> tuple[str, bool]:
    """
    Download, validate, parse, and persist a resume.

    Returns (user_message, success).
    """
    from services.resume_storage import validate_resume_upload

    try:
        safe_name, ext = validate_resume_upload(
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
        )
    except ValueError as exc:
        return (str(exc) if str(exc) else MSG_RESUME_INVALID_FILE, False)

    try:
        tg_file = await bot.get_file(file_id)
        data = bytes(await tg_file.download_as_bytearray())
    except Exception:
        logger.exception("Failed to download resume from Telegram")
        return (MSG_RESUME_INVALID_FILE, False)

    try:
        validate_resume_upload(filename=safe_name, file_size=len(data), mime_type=mime_type)
        parsed = parse_resume_bytes(data, ext)
        delete_user_resume_files(user_id)
        path = save_resume_file(user_id, data, safe_name)
        await resume_repo.upsert(
            session,
            user_id,
            filename=safe_name,
            file_path=str(path),
            extracted_skills=parsed.to_json(),
        )
    except ValueError as exc:
        return (str(exc) if str(exc) else MSG_RESUME_INVALID_FILE, False)
    except Exception:
        logger.exception("Failed to process resume for user %s", user_id)
        return (MSG_RESUME_INVALID_FILE, False)

    summary = format_skills_summary(parsed)
    if summary == "—":
        return (MSG_RESUME_NO_SKILLS, True)
    return (MSG_RESUME_SAVED.format(skills=summary), True)


async def delete_user_resume(session: AsyncSession, user_id: int) -> str:
    deleted = await resume_repo.delete_for_user(session, user_id)
    delete_user_resume_files(user_id)
    if not deleted:
        return MSG_RESUME_NONE
    return MSG_RESUME_DELETED
