from __future__ import annotations

import logging
import threading

import uvicorn
from fastapi import FastAPI

from core.config import Settings, __version__

logger = logging.getLogger(__name__)

_app_settings: Settings | None = None


def create_health_app(settings: Settings) -> FastAPI:
    """Lightweight HTTP health API for Docker, Railway, and Render."""
    app = FastAPI(
        title="Job Finder Bot Health",
        docs_url=None,
        redoc_url=None,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "version": __version__,
            "environment": settings.environment,
        }

    return app


def start_health_server(settings: Settings) -> threading.Thread:
    """
    Run uvicorn in a background daemon thread alongside the Telegram bot.

    Binds to 0.0.0.0:{PORT} (Railway/Render set PORT automatically).
    """
    global _app_settings
    _app_settings = settings
    app = create_health_app(settings)
    uvicorn_log_level = "warning" if settings.is_production else "info"

    def _run() -> None:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=settings.health_port,
            log_level=uvicorn_log_level,
            access_log=not settings.is_production,
        )

    thread = threading.Thread(target=_run, name="health-server", daemon=True)
    thread.start()
    logger.info(
        "Health HTTP server starting on 0.0.0.0:%s",
        settings.health_port,
    )
    return thread
