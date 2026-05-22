from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from core.constants import CMD_START, DEFAULT_WORK_TYPE
from repositories import user_repository as user_repo


async def settings(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession
) -> None:
    """/settings: show saved user preferences."""
    if not update.effective_user or not update.message:
        return

    pref = await user_repo.get_by_user_id(session, update.effective_user.id)

    if pref is None or (not pref.keyword and not pref.location):
        await update.message.reply_text(
            "You don't have saved preferences yet.\n"
            f"Use /{CMD_START} to set job keyword, location, and work type."
        )
        return

    await update.message.reply_text(
        "Your current preferences:\n"
        f"- Keyword: {pref.keyword or '(not set)'}\n"
        f"- Location: {pref.location or '(not set)'}\n"
        f"- Work type: {pref.work_type or DEFAULT_WORK_TYPE}\n\n"
        f"To change them, use /{CMD_START} again."
    )
