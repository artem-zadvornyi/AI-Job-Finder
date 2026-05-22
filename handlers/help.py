from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from services.bot_info import build_help_message


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help — formatted command reference."""
    if update.message:
        await update.message.reply_text(build_help_message())
