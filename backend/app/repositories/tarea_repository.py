from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tarea import EstadoTarea, Tarea
from app.repositories.base import TenantScopedRepository


class TareaRepository(TenantScopedRepository[Tarea]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Tarea, session, tenant_id)

    async def list(
        self,
        include_deleted: bool = False,
        offset: int = 0,
        limit: int = 50,
        estado: str | None = None,
        asignado_a: UUID | None = None,
        asignado_por: UUID | None = None,
        materia_id: UUID | None = None,
        q: str | None = None,
    ) -> tuple[list[Tarea], int]:
        """List tareas with filters, scoped by tenant.

        Returns (items, total_count).
        Always excludes soft-deleted unless include_deleted=True.
        """
        stmt = select(Tarea).where(Tarea.tenant_id == self.tenant_id)

        if not include_deleted:
            stmt = stmt.where(Tarea.is_deleted == False)

        if estado is not None:
            stmt = stmt.where(Tarea.estado == EstadoTarea(estado))

        if asignado_a is not None:
            stmt = stmt.where(Tarea.asignado_a == asignado_a)

        if asignado_por is not None:
            stmt = stmt.where(Tarea.asignado_por == asignado_por)

        if materia_id is not None:
            stmt = stmt.where(Tarea.materia_id == materia_id)

        if q is not None:
            stmt = stmt.where(Tarea.descripcion.ilike(f"%{q}%"))

        # Count total
        count_q = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_q)
        total = count_result.scalar() or 0

        # Get items with ordering
        data_q = (
            stmt
            .order_by(Tarea.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        data_result = await self.session.execute(data_q)
        items = list(data_result.scalars().all())
        return items, total
