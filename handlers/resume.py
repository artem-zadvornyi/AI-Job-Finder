from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from core.constants import (
    MSG_RESUME_NONE,
    MSG_RESUME_REPLACE_HINT,
    MSG_RESUME_UPLOAD_PROMPT,
    RESUME_AWAITING_UPLOAD_KEY,
)
from repositories import resume_repository as resume_repo
from services.resume_service import (
    delete_user_resume,
    format_my_resume_message,
    save_resume_from_telegram,
)

logger = logging.getLogger(__name__)


async def resume_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """/resume — prompt user to upload or replace a PDF/DOCX resume."""
    if not update.effective_user or not update.message:
        return

    context.user_data[RESUME_AWAITING_UPLOAD_KEY] = True
    existing = await resume_repo.get_by_user_id(session, update.effective_user.id)
    text = MSG_RESUME_UPLOAD_PROMPT
    if existing is not None:
        text = f"{MSG_RESUME_REPLACE_HINT}\n\n{text}"
    await update.message.reply_text(text, parse_mode="Markdown")


async def my_resume_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """/my_resume — show stored resume metadata and detected skills."""
    if not update.effective_user or not update.message:
        return

    row = await resume_repo.get_by_user_id(session, update.effective_user.id)
    if row is None:
        await update.message.reply_text(MSG_RESUME_NONE)
        return

    await update.message.reply_text(format_my_resume_message(row))


async def delete_resume_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """/delete_resume — remove resume file and database row."""
    if not update.effective_user or not update.message:
        return

    context.user_data.pop(RESUME_AWAITING_UPLOAD_KEY, None)
    message = await delete_user_resume(session, update.effective_user.id)
    await update.message.reply_text(message)


async def on_resume_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """Handle PDF/DOCX document upload after /resume."""
    if not update.effective_user or not update.message:
        return

    if not context.user_data.get(RESUME_AWAITING_UPLOAD_KEY):
        return

    document = update.message.document
    if document is None:
        return

    context.user_data.pop(RESUME_AWAITING_UPLOAD_KEY, None)

    message, ok = await save_resume_from_telegram(
        session,
        user_id=update.effective_user.id,
        bot=context.bot,
        file_id=document.file_id,
        filename=document.file_name or "resume.pdf",
        file_size=document.file_size,
        mime_type=document.mime_type,
    )
    await update.message.reply_text(message)

    if ok:
        logger.info("Resume saved for user %s", update.effective_user.id)
