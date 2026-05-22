from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import Settings
from core.logging import log_event
from models import Base

logger = logging.getLogger(__name__)


def create_engine(settings: Settings) -> AsyncEngine:
    """Create an async SQLAlchemy engine (SQLite or PostgreSQL)."""
    url = settings.database_url
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(url, echo=False)


def create_session_factory(engine: AsyncEngine) -> sessionmaker[AsyncSession]:
    """Create a session factory for dependency injection."""
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _migrate_sqlite_columns(sync_conn) -> None:
    """Add new columns to existing SQLite DBs (create_all does not alter tables)."""
    inspector = inspect(sync_conn)
    if not inspector.has_table("user_preferences"):
        return
    columns = {col["name"] for col in inspector.get_columns("user_preferences")}
    if "alerts_enabled" not in columns:
        sync_conn.execute(
            text(
                "ALTER TABLE user_preferences ADD COLUMN alerts_enabled BOOLEAN NOT NULL DEFAULT 0"
            )
        )


async def verify_connection(engine: AsyncEngine) -> None:
    """Ping the database; raises on failure."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def init_db(engine: AsyncEngine, *, settings: Settings) -> None:
    """Create database tables on startup (if they don't exist)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if not settings.uses_postgres:
            await conn.run_sync(_migrate_sqlite_columns)
    log_event(
        logger,
        logging.INFO,
        "Database connected",
        database=settings.database_type,
    )


async def close_db(engine: AsyncEngine) -> None:
    """Dispose of the engine and close all pooled connections."""
    await engine.dispose()
    log_event(logger, logging.INFO, "Database connections closed")
