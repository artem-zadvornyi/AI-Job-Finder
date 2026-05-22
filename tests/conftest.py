from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import Settings
from models import Base

# Isolated in-memory SQLite — never touches project .env or real DB files.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def isolate_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Override environment so tests never use real secrets or production DB."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("BOT_TOKEN", "test-bot-token-for-ci-only")
    monkeypatch.setenv("SQLITE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PORT", "8000")
    monkeypatch.delenv("ADMIN_USER_ID", raising=False)


@pytest.fixture
def test_settings(isolate_test_environment: None) -> Settings:
    from core.config import load_settings

    return load_settings()


@pytest_asyncio.fixture
async def db_session(isolate_test_environment: None) -> AsyncSession:
    """Fresh in-memory database per test."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


def pytest_configure(config: pytest.Config) -> None:
    """Ensure BOT_TOKEN is never read from a developer .env during collection."""
    os.environ.setdefault("BOT_TOKEN", "test-bot-token-for-ci-only")
