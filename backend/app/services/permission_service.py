import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permission, RolePermission, UserRole


class PermissionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_effective_permissions(self, user_id: uuid.UUID) -> set[str]:
        stmt = (
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
        )
        rows = await self.session.execute(stmt)
        return {row[0] for row in rows.all()}

    async def get_effective_scope(self, codename: str, user_id: uuid.UUID) -> str | None:
        stmt = (
            select(RolePermission.scope)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(UserRole.user_id == user_id)
            .where(Permission.name == codename)
            .limit(1)
        )
        rows = await self.session.execute(stmt)
        row = rows.scalar_one_or_none()
        return row
