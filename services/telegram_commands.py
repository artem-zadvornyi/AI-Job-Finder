from __future__ import annotations

import logging

from telegram import Bot, BotCommand

from core.constants import COMMAND_DESCRIPTIONS

logger = logging.getLogger(__name__)

BOT_COMMANDS: tuple[BotCommand, ...] = tuple(
    BotCommand(command, description) for command, description in COMMAND_DESCRIPTIONS
)


async def setup_bot_commands(bot: Bot) -> None:
    """Register slash commands with Telegram so they appear in the client menu."""
    await bot.set_my_commands(list(BOT_COMMANDS))
    logger.debug("Registered %d bot commands with Telegram", len(BOT_COMMANDS))
