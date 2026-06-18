from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_base import SalarioBase
from app.models.salario_plus import SalarioPlus
from app.repositories.base import TenantScopedRepository


class SalarioBaseRepository(TenantScopedRepository[SalarioBase]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(SalarioBase, session, tenant_id)

    async def create_base(self, **kwargs) -> SalarioBase:
        return await self.create(**kwargs)

    async def get_base(self, id: UUID) -> SalarioBase | None:
        return await self.get(id)

    async def list_base(
        self,
        offset: int = 0,
        limit: int | None = None,
        **filters,
    ) -> list[SalarioBase]:
        return await self.list(offset=offset, limit=limit, **filters)

    async def update_base(self, id: UUID, **kwargs) -> SalarioBase:
        return await self.update(id, **kwargs)

    async def soft_delete_base(self, id: UUID) -> None:
        return await self.soft_delete(id)

    async def find_vigente_base_by_rol(self, rol: str, fecha: date) -> SalarioBase | None:
        stmt = select(SalarioBase).where(
            SalarioBase.tenant_id == self.tenant_id,
            SalarioBase.is_deleted == False,
            SalarioBase.rol == rol,
            SalarioBase.desde <= fecha,
            or_(
                SalarioBase.hasta.is_(None),
                SalarioBase.hasta >= fecha,
            ),
        ).order_by(SalarioBase.desde.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_vigente_base_by_rol_periodo(self, rol: str, periodo: str) -> SalarioBase | None:
        year, month = map(int, periodo.split("-"))
        fecha = date(year, month, 1)
        return await self.find_vigente_base_by_rol(rol, fecha)


class SalarioPlusRepository(TenantScopedRepository[SalarioPlus]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(SalarioPlus, session, tenant_id)

    async def create_plus(self, **kwargs) -> SalarioPlus:
        return await self.create(**kwargs)

    async def get_plus(self, id: UUID) -> SalarioPlus | None:
        return await self.get(id)

    async def list_plus(
        self,
        offset: int = 0,
        limit: int | None = None,
        **filters,
    ) -> list[SalarioPlus]:
        return await self.list(offset=offset, limit=limit, **filters)

    async def update_plus(self, id: UUID, **kwargs) -> SalarioPlus:
        return await self.update(id, **kwargs)

    async def soft_delete_plus(self, id: UUID) -> None:
        return await self.soft_delete(id)

    async def find_vigente_plus_by_grupo_rol(
        self, grupo: str, rol: str, fecha: date,
    ) -> SalarioPlus | None:
        stmt = select(SalarioPlus).where(
            SalarioPlus.tenant_id == self.tenant_id,
            SalarioPlus.is_deleted == False,
            SalarioPlus.grupo == grupo,
            SalarioPlus.rol == rol,
            SalarioPlus.desde <= fecha,
            or_(
                SalarioPlus.hasta.is_(None),
                SalarioPlus.hasta >= fecha,
            ),
        ).order_by(SalarioPlus.desde.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_vigentes_plus_by_rol(self, rol: str, fecha: date) -> list[SalarioPlus]:
        stmt = select(SalarioPlus).where(
            SalarioPlus.tenant_id == self.tenant_id,
            SalarioPlus.is_deleted == False,
            SalarioPlus.rol == rol,
            SalarioPlus.desde <= fecha,
            or_(
                SalarioPlus.hasta.is_(None),
                SalarioPlus.hasta >= fecha,
            ),
        ).order_by(SalarioPlus.desde.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
