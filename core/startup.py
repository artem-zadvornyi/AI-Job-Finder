from __future__ import annotations

import logging
import sys
import time

from sqlalchemy.ext.asyncio import AsyncEngine

from core.config import Settings
from core.constants import LOG_DIR_NAME
from core.database import verify_connection
from core.logging import LOG_DIR, log_event

logger = logging.getLogger(__name__)


class StartupValidationError(Exception):
    """Raised when pre-flight checks fail before the bot goes live."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("\n".join(messages))


def validate_logs_writable() -> None:
    """Ensure the logs directory exists and is writable."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        probe = LOG_DIR / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        raise StartupValidationError(
            [
                f"Cannot write to logs folder ({LOG_DIR_NAME}/):\n"
                f"  → {exc}\n"
                "  → Check permissions or set a writable path."
            ]
        ) from exc


async def validate_database(engine: AsyncEngine, settings: Settings) -> None:
    try:
        await verify_connection(engine)
    except Exception as exc:
        raise StartupValidationError(
            [
                f"Database connection failed ({settings.database_type}):\n"
                f"  → {exc}\n"
                "  → Verify DATABASE_URL / SQLITE_URL and that the database is reachable."
            ]
        ) from exc


async def run_startup_checks(settings: Settings, engine: AsyncEngine) -> float:
    """
    Run all startup validations.

    Returns elapsed time in seconds.
    """
    started = time.perf_counter()

    validate_logs_writable()
    log_event(logger, logging.INFO, "Logs folder writable", path=str(LOG_DIR.resolve()))

    await validate_database(engine, settings)

    elapsed = time.perf_counter() - started
    log_event(
        logger,
        logging.INFO,
        "Startup validation passed",
        duration_seconds=round(elapsed, 2),
    )
    return elapsed


def print_startup_error(exc: StartupValidationError) -> None:
    print("\n❌ Startup validation failed\n", file=sys.stderr)
    for message in exc.messages:
        print(message, file=sys.stderr)
        print(file=sys.stderr)
    print("Fix the issue above and restart the bot.\n", file=sys.stderr)


def run_startup_checks_or_exit(settings: Settings, engine: AsyncEngine) -> float:
    """Run startup checks synchronously or exit with a clean message."""
    import asyncio

    try:
        return asyncio.run(run_startup_checks(settings, engine))
    except StartupValidationError as exc:
        print_startup_error(exc)
        sys.exit(1)
