from __future__ import annotations

import sys

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from core.config import Settings, __version__
from core.constants import (
    JOB_SOURCE,
    MSG_ADMIN_NOT_CONFIGURED,
    MSG_ADMIN_ONLY,
    MSG_HEALTH_RUNNING,
)
from repositories import saved_jobs_repository as saved_repo
from repositories import sent_jobs_repository as sent_repo
from repositories import user_repository as user_repo
from services.health_checks import (
    check_alerts_scheduler,
    check_database,
    check_remotive_api,
)
from services.uptime import format_uptime


def _is_admin(update: Update, settings: Settings) -> bool:
    if settings.admin_user_id is None:
        return False
    user = update.effective_user
    return user is not None and user.id == settings.admin_user_id


async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: AsyncSession,
    settings: Settings,
) -> None:
    """/stats — admin-only bot statistics."""
    if not update.effective_user or not update.message:
        return

    if settings.admin_user_id is None:
        await update.message.reply_text(MSG_ADMIN_NOT_CONFIGURED)
        return

    if not _is_admin(update, settings):
        await update.message.reply_text(MSG_ADMIN_ONLY)
        return

    total_users = await user_repo.count_total(session)
    alerts_users = await user_repo.count_with_alerts_enabled(session)
    saved_total = await saved_repo.count_all(session)
    sent_total = await sent_repo.count_all(session)

    started_at = context.application.bot_data.get("bot_started_at")
    uptime_text = format_uptime(started_at) if started_at else "unknown"

    await update.message.reply_text(
        "📊 Bot statistics\n\n"
        "👤 Users:\n"
        f"- total users count: {total_users}\n"
        f"- users with alerts enabled: {alerts_users}\n\n"
        "💾 Saved jobs:\n"
        f"- total saved vacancies: {saved_total}\n\n"
        "📨 Alerts:\n"
        f"- total sent alerts: {sent_total}\n\n"
        "🕒 Uptime:\n"
        f"- bot running time: {uptime_text}"
    )


async def health(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    engine: AsyncEngine,
) -> None:
    """/health — public status check."""
    if not update.message:
        return

    scheduler_ok, scheduler_detail = check_alerts_scheduler(
        bool(context.application.bot_data.get("alerts_scheduler_running"))
    )
    db_ok, db_detail = await check_database(engine)
    api_ok, api_detail = await check_remotive_api()

    def status_line(ok: bool, label: str, detail: str) -> str:
        icon = "✅" if ok else "❌"
        extra = "" if detail in ("ok", "running") else f" ({detail})"
        return f"{icon} {label}{extra}"

    lines = [
        MSG_HEALTH_RUNNING,
        "",
        status_line(db_ok, "Database", db_detail),
        status_line(api_ok, "Remotive API", api_detail),
        status_line(scheduler_ok, "Alerts scheduler", scheduler_detail),
    ]
    await update.message.reply_text("\n".join(lines))


async def version_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/version — build and runtime info."""
    if not update.message:
        return

    settings: Settings = context.application.bot_data["settings"]
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    await update.message.reply_text(
        f"Bot version: {__version__}\n"
        f"Python version: {py_version}\n"
        f"Database type: {settings.database_type}\n"
        f"Active job source: {JOB_SOURCE}"
    )
