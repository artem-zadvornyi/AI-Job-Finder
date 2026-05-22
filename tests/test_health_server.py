from __future__ import annotations

from fastapi.testclient import TestClient

from core.config import Settings, __version__
from services.health_server import create_health_app


def test_health_endpoint_response() -> None:
    settings = Settings(
        bot_token="test-token",
        environment="production",
        admin_user_id=None,
        database_url="sqlite+aiosqlite:///:memory:",
        health_port=8000,
    )
    client = TestClient(create_health_app(settings))
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": __version__,
        "environment": "production",
    }
