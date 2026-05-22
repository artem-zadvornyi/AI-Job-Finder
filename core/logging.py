from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from core.config import Settings, __version__
from core.constants import (
    ENV_PRODUCTION,
    LOG_BACKUP_COUNT,
    LOG_DIR_NAME,
    LOG_FILE_NAME,
    LOG_MAX_BYTES,
)

LOG_DIR = Path(LOG_DIR_NAME)
LOG_FILE = LOG_DIR / LOG_FILE_NAME

_NOISY_LOGGERS = ("httpx", "httpcore", "urllib3")


def setup_logging(settings: Settings) -> None:
    """Configure console and rotating file handlers based on environment."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if settings.is_development else logging.INFO
    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")

    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root.addHandler(file_handler)

    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root.addHandler(console_handler)

    if settings.is_production:
        for name in _NOISY_LOGGERS:
            logging.getLogger(name).setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    else:
        logging.getLogger("telegram").setLevel(logging.DEBUG)


def log_event(logger: logging.Logger, level: int, message: str, **context: object) -> None:
    """Log a message with optional key=value context (structured-style)."""
    if context:
        details = " | ".join(f"{key}={value}" for key, value in context.items())
        logger.log(level, "%s | %s", message, details)
    else:
        logger.log(level, message)


def log_startup_summary(
    settings: Settings,
    *,
    alerts_enabled: bool,
    startup_seconds: float | None = None,
    health_port: int | None = None,
) -> None:
    """Print the production-style startup banner to logs."""
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    alerts_label = "enabled" if alerts_enabled else "disabled"
    timing = f"{startup_seconds:.2f}s" if startup_seconds is not None else "—"
    port = health_port if health_port is not None else settings.health_port
    mode = ENV_PRODUCTION if settings.is_production else settings.environment

    banner = (
        "\n"
        "╔══════════════════════════════════════╗\n"
        "║       Job Finder Bot — online        ║\n"
        "╠══════════════════════════════════════╣\n"
        f"║  Version      {__version__:<22}║\n"
        f"║  Environment  {mode:<22}║\n"
        f"║  Database     {settings.database_type:<22}║\n"
        f"║  Alerts       {alerts_label:<22}║\n"
        f"║  Health HTTP  :{port:<21}║\n"
        f"║  Python       {py_version:<22}║\n"
        f"║  Startup      {timing:<22}║\n"
        "╚══════════════════════════════════════╝"
    )
    logging.getLogger(__name__).info("%s", banner)


def log_shutdown_complete(logger: logging.Logger) -> None:
    log_event(logger, logging.INFO, "Shutdown complete")
