import os
import sys

os.environ["SECRET_KEY"] = "a" * 32
os.environ["ENCRYPTION_KEY"] = "b" * 32
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test")
print(f"Before import: DATABASE_URL={os.environ.get('DATABASE_URL')}")

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.config import get_settings
get_settings.cache_clear()
s = get_settings()
print(f"From settings: {s.database_url}")
