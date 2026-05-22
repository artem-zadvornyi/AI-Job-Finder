from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from core.constants import (
    ALERT_SAVE_CALLBACK_PREFIX,
    DELETE_SAVED_CALLBACK_PREFIX,
    MSG_ACTION_UNAVAILABLE,
    MSG_ALREADY_DELETED,
    MSG_DELETED,
    MSG_NO_SAVED,
    SAVE_CALLBACK_PREFIX,
)
from services.callback_guard import try_claim_callback
from services.saved_jobs import delete_saved_job, list_saved_jobs
from services.vacancy_cache import get_alert_vacancy
from services.vacancy_cards import format_saved_vacancy_from_row, saved_vacancy_inline_keyboard
from services.vacancy_save import save_vacancy_from_cache

logger = logging.getLogger(__name__)


async def saved_list_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """/saved — show all vacancies saved by the current user."""
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    jobs = await list_saved_jobs(session, user_id)

    if not jobs:
        await update.message.reply_text(MSG_NO_SAVED)
        return

    await update.message.reply_text(f"Your saved jobs ({len(jobs)}):")

    for job in jobs:
        await _send_saved_card(update, job)


async def _send_saved_card(update: Update, job) -> None:
    message = update.message
    if not message:
        return
    await message.reply_text(
        format_saved_vacancy_from_row(job),
        reply_markup=saved_vacancy_inline_keyboard(link=job.link, saved_id=job.id),
        disable_web_page_preview=True,
    )


async def on_save_vacancy(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """Handle legacy save:<index> callbacks (backward compatibility)."""
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return

    if not query.data.startswith(SAVE_CALLBACK_PREFIX):
        return

    await _handle_save_by_index(
        update,
        context,
        session,
        index_raw=query.data[len(SAVE_CALLBACK_PREFIX) :],
        cache_getter=lambda idx: context.user_data.get("vacancy_cache", {}).get(idx),
    )


async def on_alert_save_vacancy(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """Handle alert save callbacks (asv:<index>)."""
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return

    if not query.data.startswith(ALERT_SAVE_CALLBACK_PREFIX):
        return

    index_raw = query.data[len(ALERT_SAVE_CALLBACK_PREFIX) :]

    def _get_alert(idx: str):
        if not idx.isdigit():
            return None
        return get_alert_vacancy(context.user_data, int(idx))

    await _handle_save_by_index(
        update,
        context,
        session,
        index_raw=index_raw,
        cache_getter=_get_alert,
    )


async def _handle_save_by_index(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
    *,
    index_raw: str,
    cache_getter,
) -> None:
    query = update.callback_query
    if not query:
        return

    if not try_claim_callback(context.user_data, str(query.id)):
        await query.answer()
        return

    vacancy = cache_getter(index_raw)
    if not vacancy or not isinstance(vacancy, dict):
        await query.answer(MSG_ACTION_UNAVAILABLE, show_alert=True)
        return

    message, status = await save_vacancy_from_cache(
        session,
        context.user_data,
        update.effective_user.id,
        vacancy,
    )
    if status == "invalid":
        await query.answer(MSG_ACTION_UNAVAILABLE, show_alert=True)
        return

    await query.answer(message)
    if status == "saved":
        logger.info(
            "Saved vacancy for user %s | link=%s",
            update.effective_user.id,
            vacancy.get("link"),
        )


async def on_delete_saved_vacancy(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """Handle 🗑 Delete on a saved vacancy (callback_data: del_saved:<id>)."""
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return

    if not query.data.startswith(DELETE_SAVED_CALLBACK_PREFIX):
        return

    if not try_claim_callback(context.user_data, str(query.id)):
        await query.answer()
        return

    raw_id = query.data[len(DELETE_SAVED_CALLBACK_PREFIX) :]
    try:
        job_id = int(raw_id)
    except ValueError:
        await query.answer(MSG_ALREADY_DELETED, show_alert=True)
        return

    user_id = update.effective_user.id
    result = await delete_saved_job(session, user_id, job_id)

    if result == "not_found":
        await query.answer(MSG_ALREADY_DELETED, show_alert=True)
        await _remove_saved_card_message(query, MSG_ALREADY_DELETED)
        return

    logger.info("Deleted saved job id=%s for user %s", job_id, user_id)
    await query.answer(MSG_DELETED)
    await _remove_saved_card_message(query, MSG_DELETED)


async def _remove_saved_card_message(query, fallback_text: str) -> None:
    """Try to delete the card message; fall back to editing the text."""
    if not query.message:
        return
    try:
        await query.message.delete()
    except Exception:
        logger.debug("Could not delete message, trying edit", exc_info=True)
        try:
            await query.edit_message_text(fallback_text, reply_markup=None)
        except Exception:
            logger.debug("Could not edit message after delete", exc_info=True)
