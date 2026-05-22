from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from core.constants import MSG_USER_ERROR
from core.logging import log_event

logger = logging.getLogger(__name__)


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log full traceback and notify the user when possible."""
    log_event(
        logger,
        logging.ERROR,
        "Unhandled exception while processing update",
        error=str(context.error),
    )
    logger.error("Traceback", exc_info=context.error)

    if not isinstance(update, Update):
        return

    message = update.effective_message
    if message is None:
        return

    try:
        await message.reply_text(MSG_USER_ERROR)
    except Exception:
        logger.exception("Failed to send error message to user")
