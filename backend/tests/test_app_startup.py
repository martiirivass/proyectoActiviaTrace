import os

os.environ["SECRET_KEY"] = "a" * 32
os.environ["ENCRYPTION_KEY"] = "b" * 32

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
get_settings.cache_clear()

from app.main import app


async def test_app_starts_without_error():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200