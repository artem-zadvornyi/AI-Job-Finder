from __future__ import annotations

import logging

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from core.constants import HEALTH_CHECK_HTTP_TIMEOUT_SECONDS, REMOTIVE_API_URL

logger = logging.getLogger(__name__)


async def check_database(engine: AsyncEngine) -> tuple[bool, str]:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:
        logger.exception("Database health check failed")
        return False, str(exc)


async def check_remotive_api() -> tuple[bool, str]:
    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_HTTP_TIMEOUT_SECONDS) as client:
            resp = await client.get(REMOTIVE_API_URL, params={"search": "python"})
        if resp.status_code == 200:
            return True, "ok"
        return False, f"HTTP {resp.status_code}"
    except Exception as exc:
        logger.exception("Remotive API health check failed")
        return False, str(exc)


def check_alerts_scheduler(alerts_scheduler_running: bool) -> tuple[bool, str]:
    if alerts_scheduler_running:
        return True, "running"
    return False, "not running (job queue missing or not started)"
