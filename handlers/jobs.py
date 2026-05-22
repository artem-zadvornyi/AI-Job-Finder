from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from core.constants import (
    DEFAULT_WORK_TYPE,
    MSG_JOBS_FAILED,
    MSG_JOBS_SEARCHING,
    MSG_PREFS_NOT_SET,
)
from core.logging import log_event
from repositories import user_repository as user_repo
from services.job_pagination import build_jobs_page_view
from services.job_search import format_empty_results_message, search_vacancies_for_user
from services.remotive_api import RemotiveAPI
from services.resume_service import get_user_resume_profile
from services.vacancy_cache import get_jobs_results, store_jobs_results

logger = logging.getLogger(__name__)


async def jobs(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
    remotive: RemotiveAPI,
) -> None:
    """/jobs: search vacancies and show the first result with pagination."""
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    pref = await user_repo.get_by_user_id(session, user_id)

    if pref is None or not pref.keyword or not pref.location:
        await update.message.reply_text(MSG_PREFS_NOT_SET)
        return

    loading_message = await update.message.reply_text(MSG_JOBS_SEARCHING)

    resume_profile, _resume_row = await get_user_resume_profile(session, user_id)

    try:
        vacancies = await search_vacancies_for_user(
            remotive,
            keyword=pref.keyword,
            location=pref.location,
            work_type=pref.work_type or DEFAULT_WORK_TYPE,
            resume_profile=resume_profile,
        )
    except Exception:
        logger.exception("Unexpected error during job search")
        await loading_message.edit_text(MSG_JOBS_FAILED)
        return

    if not vacancies:
        await loading_message.edit_text(format_empty_results_message())
        return

    store_jobs_results(context.user_data, vacancies)

    log_event(
        logger,
        logging.INFO,
        "Job search completed",
        user_id=user_id,
        results=len(vacancies),
    )

    page = build_jobs_page_view(get_jobs_results(context.user_data), 0)
    if page is None:
        await loading_message.edit_text(MSG_JOBS_FAILED)
        return

    text, markup = page
    await loading_message.edit_text(
        text,
        reply_markup=markup,
        disable_web_page_preview=True,
    )
