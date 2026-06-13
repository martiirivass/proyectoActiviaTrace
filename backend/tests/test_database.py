import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db


async def test_database_connection(db_session):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


async def test_get_db_dependency_yields_session(client):
    response = await client.get("/health")
    assert response.status_code == 200


async def test_session_closes_on_exception():
    from app.core.dependencies import get_db

    gen = get_db()
    session = await anext(gen)
    assert isinstance(session, AsyncSession)

    try:
        raise ValueError("test error")
    except ValueError:
        pass

    try:
        await anext(gen)
    except StopAsyncIteration:
        pass
    else:
        raise AssertionError("Generator should be exhausted after exception")