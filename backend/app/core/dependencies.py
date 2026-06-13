from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


# RESERVADO para C-03: get_current_user - resolución del usuario actual desde JWT
# RESERVADO para C-02: get_tenant - resolución y aislamiento de tenant
# RESERVADO para C-04: require_permission - verificación de permisos RBAC fino