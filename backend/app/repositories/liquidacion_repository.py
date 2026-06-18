from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.liquidacion import Liquidacion
from app.repositories.base import TenantScopedRepository


class LiquidacionRepository(TenantScopedRepository[Liquidacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Liquidacion, session, tenant_id)

    async def find_by_cohorte_periodo(
        self, cohorte_id: UUID, periodo: str,
    ) -> list[Liquidacion]:
        stmt = select(Liquidacion).where(
            Liquidacion.tenant_id == self.tenant_id,
            Liquidacion.is_deleted == False,
            Liquidacion.cohorte_id == cohorte_id,
            Liquidacion.periodo == periodo,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_usuario_cohorte_periodo(
        self, usuario_id: UUID, cohorte_id: UUID, periodo: str,
    ) -> Liquidacion | None:
        stmt = select(Liquidacion).where(
            Liquidacion.tenant_id == self.tenant_id,
            Liquidacion.is_deleted == False,
            Liquidacion.usuario_id == usuario_id,
            Liquidacion.cohorte_id == cohorte_id,
            Liquidacion.periodo == periodo,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_filters(
        self,
        filtros: dict,
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[list[Liquidacion], int]:
        base_conditions = [
            Liquidacion.tenant_id == self.tenant_id,
            Liquidacion.is_deleted == False,
        ]

        filterable_fields = {
            "cohorte_id": Liquidacion.cohorte_id,
            "periodo": Liquidacion.periodo,
            "usuario_id": Liquidacion.usuario_id,
            "rol": Liquidacion.rol,
            "estado": Liquidacion.estado,
            "es_nexo": Liquidacion.es_nexo,
            "excluido_por_factura": Liquidacion.excluido_por_factura,
        }

        for key, column in filterable_fields.items():
            value = filtros.get(key)
            if value is not None:
                base_conditions.append(column == value)

        # Count
        count_stmt = select(func.count()).select_from(Liquidacion).where(*base_conditions)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Results
        stmt = select(Liquidacion).where(*base_conditions)
        if limit is not None:
            stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def kpi_aggregation(
        self,
        periodo: str,
        cohorte_id: UUID | None = None,
    ) -> dict:
        base_conditions = [
            Liquidacion.tenant_id == self.tenant_id,
            Liquidacion.is_deleted == False,
            Liquidacion.periodo == periodo,
        ]
        if cohorte_id is not None:
            base_conditions.append(Liquidacion.cohorte_id == cohorte_id)

        stmt = select(
            Liquidacion.excluido_por_factura,
            func.count().label("count"),
            func.sum(Liquidacion.total).label("total_sum"),
        ).where(*base_conditions).group_by(Liquidacion.excluido_por_factura)

        result = await self.session.execute(stmt)
        rows = result.all()

        aggregation = {
            "total_facturantes_count": 0,
            "total_facturantes_sum": Decimal("0.00"),
            "total_no_facturantes_count": 0,
            "total_no_facturantes_sum": Decimal("0.00"),
        }

        for row in rows:
            total_sum = row.total_sum if row.total_sum is not None else Decimal("0.00")
            if row.excluido_por_factura:
                aggregation["total_facturantes_count"] = row.count
                aggregation["total_facturantes_sum"] = total_sum
            else:
                aggregation["total_no_facturantes_count"] = row.count
                aggregation["total_no_facturantes_sum"] = total_sum

        return aggregation
