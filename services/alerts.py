from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from telegram import Bot
from telegram.ext import Application, ContextTypes

from core.constants import (
    ALERT_HEADER,
    ALERTS_JOB_NAME,
    ALERTS_SCHEDULER_FIRST_DELAY_SECONDS,
    DEFAULT_WORK_TYPE,
)
from core.logging import log_event
from models import UserPreference
from repositories import sent_jobs_repository as sent_repo
from repositories import user_repository as user_repo
from services.job_search import search_vacancies_for_user
from services.remotive_api import RemotiveAPI
from services.resume_service import get_user_resume_profile
from services.vacancy_cache import store_alert_results
from services.vacancy_cards import (
    alert_vacancy_keyboard,
    format_vacancy_from_model,
    vacancy_to_cache_dict,
)

logger = logging.getLogger(__name__)


async def check_user_alerts(
    bot: Bot,
    session: AsyncSession,
    remotive: RemotiveAPI,
    pref: UserPreference,
    application: Application,
) -> int:
    """
    Search jobs for one user and send only vacancies not yet in sent_jobs.

    Returns the number of new notifications sent.
    """
    user_id = pref.user_id
    log_event(logger, logging.INFO, "Checking alerts for user", user_id=user_id)

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
        logger.exception("Alerts: job search failed for user %s", user_id)
        return 0

    user_data = application.user_data.setdefault(user_id, {})
    alert_cache: list[dict] = []
    sent_count = 0

    for vacancy in vacancies:
        link = (vacancy.link or "").strip()
        if not link:
            continue

        try:
            if await sent_repo.exists_for_user(session, user_id, link):
                continue

            alert_cache.append(vacancy_to_cache_dict(vacancy))
            index = len(alert_cache) - 1
            text = ALERT_HEADER + format_vacancy_from_model(vacancy)
            await bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=alert_vacancy_keyboard(link=link, index=index),
                disable_web_page_preview=True,
            )
            await sent_repo.create(session, user_id, link)
            sent_count += 1
        except Exception:
            logger.exception(
                "Alerts: failed to send vacancy to user %s | link=%s",
                user_id,
                link,
            )

    if alert_cache:
        store_alert_results(user_data, alert_cache)

    if sent_count == 0:
        log_event(logger, logging.INFO, "No new alert jobs", user_id=user_id)
    else:
        log_event(
            logger,
            logging.INFO,
            "Sent alert jobs",
            user_id=user_id,
            count=sent_count,
        )

    return sent_count


async def run_alerts_cycle(application: Application) -> None:
    """
    Check all users with alerts enabled and send new vacancy notifications.
    Never raises — errors are logged per user and for the whole cycle.
    """
    session_factory: async_sessionmaker[AsyncSession] = application.bot_data["session_factory"]
    remotive: RemotiveAPI = application.bot_data["remotive"]
    bot = application.bot

    try:
        async with session_factory() as session:
            users = await user_repo.list_with_alerts_enabled(session)
            if not users:
                log_event(logger, logging.INFO, "No users with alerts enabled")
                return

            for pref in users:
                try:
                    await check_user_alerts(bot, session, remotive, pref, application)
                except Exception:
                    logger.exception("Alerts: unexpected error for user %s", pref.user_id)
    except Exception:
        logger.exception("Alerts: cycle failed")


async def alerts_background_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job-queue entry point (called every N seconds)."""
    try:
        await run_alerts_cycle(context.application)
    except Exception:
        logger.exception("Alerts: background job crashed")


def start_alerts_scheduler(application: Application, interval_seconds: int) -> bool:
    """
    Register the repeating background task when the bot starts.

    Returns True if the scheduler was registered successfully.
    """
    application.bot_data["alerts_scheduler_running"] = False
    job_queue = application.job_queue
    if job_queue is None:
        logger.error(
            "Alerts scheduler not started: job queue missing. "
            'Install with: pip install "python-telegram-bot[job-queue]"'
        )
        return False

    job_queue.run_repeating(
        alerts_background_job,
        interval=interval_seconds,
        first=ALERTS_SCHEDULER_FIRST_DELAY_SECONDS,
        name=ALERTS_JOB_NAME,
    )
    application.bot_data["alerts_scheduler_running"] = True
    log_event(
        logger,
        logging.INFO,
        "Alerts scheduler started",
        interval_seconds=interval_seconds,
    )
    return True
