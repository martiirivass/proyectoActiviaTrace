from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factura import Factura
from app.repositories.base import TenantScopedRepository


class FacturaRepository(TenantScopedRepository[Factura]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Factura, session, tenant_id)

    async def list_by_filters(
        self,
        periodo: str | None = None,
        usuario_id: UUID | None = None,
        estado: str | None = None,
        materia_id: UUID | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[list[Factura], int]:
        base_conditions = [
            Factura.tenant_id == self.tenant_id,
            Factura.is_deleted == False,
        ]

        if periodo is not None:
            base_conditions.append(Factura.periodo == periodo)
        if usuario_id is not None:
            base_conditions.append(Factura.usuario_id == usuario_id)
        if estado is not None:
            base_conditions.append(Factura.estado == estado)
        if materia_id is not None:
            base_conditions.append(Factura.materia_id == materia_id)

        # Count
        count_stmt = select(func.count()).select_from(Factura).where(*base_conditions)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Results
        stmt = select(Factura).where(*base_conditions)
        if limit is not None:
            stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def find_by_periodo_usuario(
        self, periodo: str, usuario_id: UUID,
    ) -> list[Factura]:
        stmt = select(Factura).where(
            Factura.tenant_id == self.tenant_id,
            Factura.is_deleted == False,
            Factura.periodo == periodo,
            Factura.usuario_id == usuario_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
