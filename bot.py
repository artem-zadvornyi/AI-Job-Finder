from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from core.config import Settings, load_settings_or_exit
from core.constants import (
    ALERT_SAVE_CALLBACK_PREFIX,
    CMD_ABOUT,
    CMD_ALERTS_OFF,
    CMD_ALERTS_ON,
    CMD_DELETE_RESUME,
    CMD_HEALTH,
    CMD_HELP,
    CMD_JOBS,
    CMD_MY_RESUME,
    CMD_PING,
    CMD_RESUME,
    CMD_SAVED,
    CMD_SETTINGS,
    CMD_START,
    CMD_STATS,
    CMD_VERSION,
    DELETE_SAVED_CALLBACK_PREFIX,
    JOBS_CALLBACK_PREFIX,
    SAVE_CALLBACK_PREFIX,
)
from core.database import close_db, create_engine, create_session_factory, init_db
from core.logging import log_event, log_shutdown_complete, log_startup_summary, setup_logging
from core.startup import run_startup_checks_or_exit
from handlers.about import about_command
from handlers.alerts import alerts_off, alerts_on
from handlers.errors import global_error_handler
from handlers.help import help_command
from handlers.job_callbacks import on_jobs_callback
from handlers.jobs import jobs as jobs_handler
from handlers.monitoring import health, stats, version_cmd
from handlers.ping import ping
from handlers.resume import (
    delete_resume_command,
    my_resume_command,
    on_resume_document,
    resume_command,
)
from handlers.saved import (
    on_alert_save_vacancy,
    on_delete_saved_vacancy,
    on_save_vacancy,
    saved_list_command,
)
from handlers.settings import settings as settings_handler
from handlers.start import on_keyword, on_location, on_work_type, start
from services.alerts import start_alerts_scheduler
from services.health_server import start_health_server
from services.remotive_api import RemotiveAPI
from services.telegram_commands import setup_bot_commands
from states import KEYWORD, LOCATION, WORK_TYPE

logger = logging.getLogger(__name__)


def ensure_event_loop() -> None:
    """Ensure a main-thread event loop exists before run_polling (Python 3.12+)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


def setup_dependency_injection(
    app: Application,
    session_factory,
    remotive: RemotiveAPI,
    settings: Settings,
    engine,
    *,
    startup_seconds: float,
) -> None:
    """Store shared dependencies in application.bot_data so handlers can access them."""
    app.bot_data["session_factory"] = session_factory
    app.bot_data["remotive"] = remotive
    app.bot_data["settings"] = settings
    app.bot_data["engine"] = engine
    app.bot_data["bot_started_at"] = datetime.now(UTC)
    app.bot_data["alerts_scheduler_running"] = False
    app.bot_data["startup_seconds"] = startup_seconds


async def with_session(
    handler_func, update: Update, context: ContextTypes.DEFAULT_TYPE, *, need_remotive: bool = False
):
    """
    Small helper to open an AsyncSession for each update and call a handler.
    This avoids extra frameworks/middleware and keeps things beginner-friendly.
    """
    session_factory = context.application.bot_data["session_factory"]
    remotive = context.application.bot_data["remotive"]

    async with session_factory() as session:
        if need_remotive:
            return await handler_func(update, context, session, remotive)
        return await handler_func(update, context, session)


async def settings_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(settings_handler, update, context)


async def jobs_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(jobs_handler, update, context, need_remotive=True)


async def save_vacancy_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(on_save_vacancy, update, context)


async def on_alert_save_vacancy_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(on_alert_save_vacancy, update, context)


async def saved_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(saved_list_command, update, context)


async def delete_saved_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(on_delete_saved_vacancy, update, context)


async def alerts_on_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(alerts_on, update, context)


async def alerts_off_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(alerts_off, update, context)


async def stats_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings_obj: Settings = context.application.bot_data["settings"]
    async with context.application.bot_data["session_factory"]() as session:
        await stats(update, context, session, settings_obj)


async def health_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    engine = context.application.bot_data["engine"]
    await health(update, context, engine)


async def version_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await version_cmd(update, context)


async def ping_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await ping(update, context)


async def help_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await help_command(update, context)


async def about_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await about_command(update, context)


async def resume_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(resume_command, update, context)


async def my_resume_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(my_resume_command, update, context)


async def delete_resume_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(delete_resume_command, update, context)


async def resume_document_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(on_resume_document, update, context)


async def jobs_callback_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await with_session(on_jobs_callback, update, context)


async def work_type_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await with_session(on_work_type, update, context)


def build_application(
    settings: Settings,
    engine,
    session_factory,
    remotive: RemotiveAPI,
    *,
    startup_seconds: float,
) -> Application:
    """Create the Telegram application with lifecycle hooks."""

    async def post_init(application: Application) -> None:
        await init_db(engine, settings=settings)
        alerts_ok = start_alerts_scheduler(application, settings.alerts_interval_seconds)
        try:
            await setup_bot_commands(application.bot)
            log_event(logger, logging.INFO, "Telegram commands registered successfully")
        except Exception:
            logger.exception("Failed to register Telegram commands; bot will continue running")
        log_startup_summary(
            settings,
            alerts_enabled=alerts_ok,
            startup_seconds=application.bot_data.get("startup_seconds"),
            health_port=settings.health_port,
        )

    async def post_shutdown(application: Application) -> None:
        shutdown_engine = application.bot_data.get("engine")
        if shutdown_engine is not None:
            await close_db(shutdown_engine)
        log_shutdown_complete(logger)

    application = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    setup_dependency_injection(
        application,
        session_factory,
        remotive,
        settings,
        engine,
        startup_seconds=startup_seconds,
    )
    return application


def register_handlers(application: Application) -> None:
    """Wire command and callback handlers."""
    conv = ConversationHandler(
        entry_points=[CommandHandler(CMD_START, start)],
        states={
            KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_keyword)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_location)],
            WORK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_type_entry)],
        },
        fallbacks=[CommandHandler(CMD_START, start)],
    )

    application.add_handler(conv)
    application.add_handler(CommandHandler(CMD_SETTINGS, settings_entry))
    application.add_handler(CommandHandler(CMD_JOBS, jobs_entry))
    application.add_handler(CommandHandler(CMD_SAVED, saved_entry))
    application.add_handler(CommandHandler(CMD_ALERTS_ON, alerts_on_entry))
    application.add_handler(CommandHandler(CMD_ALERTS_OFF, alerts_off_entry))
    application.add_handler(CommandHandler(CMD_STATS, stats_entry))
    application.add_handler(CommandHandler(CMD_HEALTH, health_entry))
    application.add_handler(CommandHandler(CMD_VERSION, version_entry))
    application.add_handler(CommandHandler(CMD_PING, ping_entry))
    application.add_handler(CommandHandler(CMD_HELP, help_entry))
    application.add_handler(CommandHandler(CMD_ABOUT, about_entry))
    application.add_handler(CommandHandler(CMD_RESUME, resume_entry))
    application.add_handler(CommandHandler(CMD_MY_RESUME, my_resume_entry))
    application.add_handler(CommandHandler(CMD_DELETE_RESUME, delete_resume_entry))
    application.add_handler(
        MessageHandler(
            filters.Document.PDF | filters.Document.FileExtension("docx"),
            resume_document_entry,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            jobs_callback_entry,
            pattern=rf"^{JOBS_CALLBACK_PREFIX}\d+:[pns]$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            save_vacancy_entry,
            pattern=f"^{SAVE_CALLBACK_PREFIX}\\d+$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            on_alert_save_vacancy_entry,
            pattern=f"^{ALERT_SAVE_CALLBACK_PREFIX}\\d+$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            delete_saved_entry,
            pattern=f"^{DELETE_SAVED_CALLBACK_PREFIX}\\d+$",
        )
    )
    application.add_error_handler(global_error_handler)


if __name__ == "__main__":
    settings = load_settings_or_exit()
    setup_logging(settings)

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    startup_seconds = run_startup_checks_or_exit(settings, engine)

    remotive = RemotiveAPI()
    log_event(logger, logging.INFO, "Remotive API initialized")

    start_health_server(settings)

    application = build_application(
        settings,
        engine,
        session_factory,
        remotive,
        startup_seconds=startup_seconds,
    )
    register_handlers(application)

    log_event(
        logger,
        logging.INFO,
        "Bot started",
        environment=settings.environment,
        health_url=f"http://0.0.0.0:{settings.health_port}/health",
    )
    ensure_event_loop()
    application.run_polling()
