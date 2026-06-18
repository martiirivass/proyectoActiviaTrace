import asyncio
import os
import sys
import pytest
import pytest_asyncio
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from httpx import ASGITransport, AsyncClient

# Default to port 5432 for native PostgreSQL; Docker users can override via env before import
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/activia_trace_test")
os.environ["SECRET_KEY"] = "a" * 32
os.environ["ENCRYPTION_KEY"] = "b" * 32

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.config import get_settings
get_settings.cache_clear()

from app.core.database import Base
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    from app.core.config import refresh_settings
    refresh_settings()
    settings = get_settings()
    db_url = settings.database_url
    print(f"\n[DEBUGCONFTEST] DB_URL='{db_url}'")
    print(f"[DEBUGCONFTEST] ENV_DB_URL='{os.environ.get('DATABASE_URL', 'NOT SET')}'")
    engine = create_async_engine(db_url, echo=False, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_session_factory(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    yield factory

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(test_session_factory):
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def reset_globals():
    from app.core.dependencies import reset_rate_limiter
    await reset_rate_limiter()
    yield


@pytest_asyncio.fixture
async def client(db_session):
    from app.core.dependencies import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
