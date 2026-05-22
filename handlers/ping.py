from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from core.constants import MSG_PONG


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/ping — quick liveness check in Telegram."""
    if update.message:
        await update.message.reply_text(MSG_PONG)
