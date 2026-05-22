from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler

from core.constants import CMD_JOBS, CMD_SETTINGS, WORK_TYPES
from keyboards import work_type_keyboard
from repositories import user_repository as user_repo
from states import KEYWORD, LOCATION, WORK_TYPE


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/start: greet user and start collecting preferences (ConversationHandler)."""
    if update.message:
        await update.message.reply_text(
            "Welcome! I can help you find job vacancies.\n\n"
            "Step 1/3: Send me a job keyword (example: Python developer)."
        )
    return KEYWORD


async def on_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        return KEYWORD

    keyword = update.message.text.strip()
    context.user_data["keyword"] = keyword

    await update.message.reply_text(
        "Step 2/3: Enter a city or country (example: Berlin or Germany)."
    )
    return LOCATION


async def on_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        return LOCATION

    location = update.message.text.strip()
    context.user_data["location"] = location

    await update.message.reply_text(
        "Step 3/3: Choose a preferred work type.",
        reply_markup=work_type_keyboard(),
    )
    return WORK_TYPE


async def on_work_type(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession
) -> int:
    """Final step: validate work type, save preferences to DB."""
    if not update.message or not update.message.text:
        return WORK_TYPE

    work_type = update.message.text.strip()
    if work_type not in WORK_TYPES:
        await update.message.reply_text("Please pick a work type using the keyboard buttons.")
        return WORK_TYPE

    keyword = str(context.user_data.get("keyword") or "").strip()
    location = str(context.user_data.get("location") or "").strip()

    if not keyword or not location:
        await update.message.reply_text(
            "Something went wrong: keyword or location is empty.\nPlease use /start again."
        )
        context.user_data.clear()
        return ConversationHandler.END

    await user_repo.upsert_preferences(
        session,
        update.effective_user.id,
        keyword=keyword,
        location=location,
        work_type=work_type,
    )

    await update.message.reply_text(
        "Saved! Your preferences are stored.\n\n"
        f"Use /{CMD_JOBS} to search vacancies or /{CMD_SETTINGS} to view your preferences.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END
