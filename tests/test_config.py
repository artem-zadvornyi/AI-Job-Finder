from __future__ import annotations

import pytest

from core.config import (
    ConfigurationError,
    Settings,
    load_settings,
    normalize_database_url,
    resolve_database_url,
)


def test_load_settings_success(test_settings: Settings) -> None:
    assert test_settings.bot_token == "test-bot-token-for-ci-only"
    assert test_settings.environment == "development"
    assert test_settings.is_development is True
    assert test_settings.is_production is False
    assert "sqlite" in test_settings.database_url.lower()


def test_missing_bot_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings()
    assert "BOT_TOKEN" in exc_info.value.messages[0]


def test_invalid_environment_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings()
    assert "ENVIRONMENT" in exc_info.value.messages[0]


def test_invalid_admin_user_id_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_USER_ID", "not-a-number")
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings()
    assert "ADMIN_USER_ID" in exc_info.value.messages[0]


def test_normalize_postgres_url() -> None:
    assert normalize_database_url("postgres://user:pass@host/db") == (
        "postgresql+asyncpg://user:pass@host/db"
    )
    assert normalize_database_url("postgresql://user:pass@host/db") == (
        "postgresql+asyncpg://user:pass@host/db"
    )


def test_resolve_database_url_prefers_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@localhost/mydb")
    monkeypatch.setenv("SQLITE_URL", "sqlite+aiosqlite:///./other.db")
    assert "asyncpg" in resolve_database_url()


def test_production_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    settings = load_settings()
    assert settings.is_production is True
    assert settings.database_type in ("SQLite", "PostgreSQL", "SQL database")
