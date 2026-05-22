from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

from core.constants import (
    DEFAULT_ALERTS_INTERVAL_SECONDS,
    ENV_DEVELOPMENT,
    ENV_PRODUCTION,
    MIN_ALERTS_INTERVAL_SECONDS,
)

load_dotenv()

__version__ = "1.3.0"
BOT_VERSION = __version__

REQUIRED_ENV_VARS: tuple[str, ...] = ("BOT_TOKEN",)
DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///./job_finder_bot.db"
DEFAULT_HEALTH_PORT = 8000


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("\n".join(messages))


@dataclass(frozen=True)
class Settings:
    bot_token: str
    environment: str
    admin_user_id: int | None
    database_url: str
    alerts_interval_seconds: int = DEFAULT_ALERTS_INTERVAL_SECONDS
    health_port: int = DEFAULT_HEALTH_PORT

    @property
    def is_production(self) -> bool:
        return self.environment == ENV_PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == ENV_DEVELOPMENT

    @property
    def sqlite_url(self) -> str:
        """Backward-compatible alias for database_url."""
        return self.database_url

    @property
    def database_type(self) -> str:
        url = self.database_url.lower()
        if "sqlite" in url:
            return "SQLite"
        if "postgres" in url:
            return "PostgreSQL"
        return "SQL database"

    @property
    def uses_postgres(self) -> bool:
        return "postgres" in self.database_url.lower()


def normalize_database_url(url: str) -> str:
    """
    Normalize DATABASE_URL for async SQLAlchemy.

    Railway/Render often provide postgres:// — convert to postgresql+asyncpg://.
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def resolve_database_url() -> str:
    """Prefer DATABASE_URL (PostgreSQL); fall back to SQLITE_URL or local SQLite file."""
    database_url = (os.getenv("DATABASE_URL") or "").strip()
    if database_url:
        return normalize_database_url(database_url)
    sqlite_url = (os.getenv("SQLITE_URL") or "").strip()
    return sqlite_url or DEFAULT_SQLITE_URL


def _parse_admin_user_id(raw: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(
            ["ADMIN_USER_ID must be a numeric Telegram user id (example: 123456789)."]
        ) from exc


def _parse_health_port() -> int:
    raw = (os.getenv("PORT") or os.getenv("HEALTH_PORT") or str(DEFAULT_HEALTH_PORT)).strip()
    try:
        port = int(raw)
    except ValueError as exc:
        raise ConfigurationError(
            [f"PORT / HEALTH_PORT must be a valid integer (got {raw!r})."]
        ) from exc
    if not 1 <= port <= 65535:
        raise ConfigurationError([f"PORT must be between 1 and 65535 (got {port})."])
    return port


def load_settings() -> Settings:
    """Load and validate settings from environment variables."""
    errors: list[str] = []

    bot_token = (os.getenv("BOT_TOKEN") or "").strip()
    if not bot_token:
        errors.append(
            "Missing required environment variable: BOT_TOKEN\n"
            "  → Create a bot token via @BotFather and add it to your .env file."
        )

    environment = (os.getenv("ENVIRONMENT") or ENV_DEVELOPMENT).strip().lower()
    if environment not in (ENV_DEVELOPMENT, ENV_PRODUCTION):
        errors.append(
            f"Invalid ENVIRONMENT value: {environment!r}\n"
            f"  → Use {ENV_DEVELOPMENT!r} or {ENV_PRODUCTION!r}."
        )

    raw_interval = os.getenv(
        "ALERTS_INTERVAL_SECONDS", str(DEFAULT_ALERTS_INTERVAL_SECONDS)
    ).strip()
    try:
        alerts_interval_seconds = max(MIN_ALERTS_INTERVAL_SECONDS, int(raw_interval))
    except ValueError:
        errors.append(
            "Invalid ALERTS_INTERVAL_SECONDS\n"
            f"  → Must be an integer >= {MIN_ALERTS_INTERVAL_SECONDS} (seconds)."
        )
        alerts_interval_seconds = DEFAULT_ALERTS_INTERVAL_SECONDS

    admin_user_id: int | None = None
    raw_admin = (os.getenv("ADMIN_USER_ID") or "").strip()
    if raw_admin:
        try:
            admin_user_id = _parse_admin_user_id(raw_admin)
        except ConfigurationError as exc:
            errors.extend(exc.messages)

    health_port = DEFAULT_HEALTH_PORT
    try:
        health_port = _parse_health_port()
    except ConfigurationError as exc:
        errors.extend(exc.messages)

    database_url = resolve_database_url()

    if errors:
        raise ConfigurationError(errors)

    return Settings(
        bot_token=bot_token,
        environment=environment,
        admin_user_id=admin_user_id,
        database_url=database_url,
        alerts_interval_seconds=alerts_interval_seconds,
        health_port=health_port,
    )


def print_configuration_error(exc: ConfigurationError) -> None:
    """Print a clean startup error for missing/invalid configuration."""
    print("\n❌ Configuration error\n", file=sys.stderr)
    for message in exc.messages:
        print(message, file=sys.stderr)
        print(file=sys.stderr)
    print("Fix your .env file (see .env.example) and restart the bot.\n", file=sys.stderr)


def load_settings_or_exit() -> Settings:
    """Load settings or exit the process with a helpful message."""
    try:
        return load_settings()
    except ConfigurationError as exc:
        print_configuration_error(exc)
        sys.exit(1)
