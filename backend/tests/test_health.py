import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test")
os.environ.setdefault("SECRET_KEY", "a" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "b" * 32)

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
get_settings.cache_clear()

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_health_endpoint_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


async def test_health_endpoint_includes_database_status(client):
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "database" in data
    assert data["database"] in ("up", "down")