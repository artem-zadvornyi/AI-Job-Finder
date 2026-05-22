from __future__ import annotations

from datetime import UTC, datetime


def format_uptime(started_at: datetime) -> str:
    """Human-readable uptime since bot process started."""
    now = datetime.now(UTC)
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=UTC)
    delta = now - started_at
    total_seconds = int(delta.total_seconds())
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)
