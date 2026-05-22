from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from core.constants import MSG_ALERTS_OFF, MSG_ALERTS_ON, MSG_NO_PREFS
from repositories import user_repository as user_repo


async def alerts_on(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """/alerts_on — enable automatic job notifications."""
    if not update.effective_user or not update.message:
        return

    pref = await user_repo.set_alerts_enabled(
        session,
        update.effective_user.id,
        enabled=True,
    )
    if pref is None:
        await update.message.reply_text(MSG_NO_PREFS)
        return

    await update.message.reply_text(MSG_ALERTS_ON)


async def alerts_off(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """/alerts_off — disable automatic job notifications."""
    if not update.effective_user or not update.message:
        return

    pref = await user_repo.set_alerts_enabled(
        session,
        update.effective_user.id,
        enabled=False,
    )
    if pref is None:
        await update.message.reply_text(MSG_NO_PREFS)
        return

    await update.message.reply_text(MSG_ALERTS_OFF)
