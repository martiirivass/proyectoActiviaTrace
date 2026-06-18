import os
import sys

# Set the env vars like conftest does
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test")
os.environ["SECRET_KEY"] = "a" * 32
os.environ["ENCRYPTION_KEY"] = "b" * 32
print("1. After setdefault: DATABASE_URL=" + os.environ["DATABASE_URL"])

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Now simulate test_app_startup.py import (it overwrites)
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5433/activia_trace_test"
print("2. After test_app_startup overwrite: DATABASE_URL=" + os.environ["DATABASE_URL"])

# Now import database module
from app.core.config import get_settings
get_settings.cache_clear()

from app.core.database import Base, engine
print("3. Settings database_url: " + get_settings().database_url)
print("4. Engine URL: " + str(engine.url))
