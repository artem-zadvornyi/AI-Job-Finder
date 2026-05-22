from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from core.constants import MSG_ACTION_UNAVAILABLE
from core.logging import log_event
from services.callback_guard import try_claim_callback
from services.job_pagination import (
    JobsNavAction,
    boundary_message,
    build_jobs_page_view,
    parse_jobs_callback,
    resolve_navigation_index,
)
from services.vacancy_cache import (
    get_jobs_results,
    get_vacancy_at,
    set_jobs_page_index,
)
from services.vacancy_save import save_vacancy_from_cache

logger = logging.getLogger(__name__)


async def on_jobs_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
) -> None:
    """Handle jobs pagination and save callbacks (jobs:{index}:p|n|s)."""
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return

    if not try_claim_callback(context.user_data, str(query.id)):
        await query.answer()
        return

    parsed = parse_jobs_callback(query.data)
    if parsed is None:
        await query.answer(MSG_ACTION_UNAVAILABLE, show_alert=True)
        return

    results = get_jobs_results(context.user_data)
    if not results:
        await query.answer(MSG_ACTION_UNAVAILABLE, show_alert=True)
        return

    if parsed.page_index < 0 or parsed.page_index >= len(results):
        await query.answer(MSG_ACTION_UNAVAILABLE, show_alert=True)
        return

    if parsed.action == JobsNavAction.SAVE:
        vacancy = get_vacancy_at(context.user_data, parsed.page_index)
        if vacancy is None:
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
            log_event(
                logger,
                logging.INFO,
                "Saved vacancy from jobs pagination",
                user_id=update.effective_user.id,
                page=parsed.page_index,
            )
        return

    new_index = resolve_navigation_index(parsed.page_index, parsed.action, len(results))
    if new_index is None:
        hint = boundary_message(parsed.action)
        await query.answer(hint or MSG_ACTION_UNAVAILABLE, show_alert=True)
        return

    page = build_jobs_page_view(results, new_index)
    if page is None:
        await query.answer(MSG_ACTION_UNAVAILABLE, show_alert=True)
        return

    text, markup = page
    try:
        await query.edit_message_text(
            text,
            reply_markup=markup,
            disable_web_page_preview=True,
        )
    except Exception:
        logger.exception("Failed to edit jobs pagination message")
        await query.answer(MSG_ACTION_UNAVAILABLE, show_alert=True)
        return

    set_jobs_page_index(context.user_data, new_index)
    await query.answer()
