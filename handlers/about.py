from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from services.bot_info import build_about_message


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/about — project and technology overview."""
    if update.message:
        await update.message.reply_text(build_about_message())
