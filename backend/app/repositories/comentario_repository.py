from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comentario_tarea import ComentarioTarea
from app.repositories.base import TenantScopedRepository


class ComentarioTareaRepository(TenantScopedRepository[ComentarioTarea]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(ComentarioTarea, session, tenant_id)

    async def list_by_tarea(
        self,
        tarea_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[ComentarioTarea], int]:
        """List comments for a tarea, ordered by creado_at ascending, scoped by tenant.

        Returns (items, total_count).
        Excludes soft-deleted comments.
        """
        stmt = (
            select(ComentarioTarea)
            .where(
                ComentarioTarea.tenant_id == self.tenant_id,
                ComentarioTarea.tarea_id == tarea_id,
                ComentarioTarea.is_deleted == False,
            )
        )

        # Count total
        count_q = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_q)
        total = count_result.scalar() or 0

        # Get items ordered by creado_at asc
        data_q = (
            stmt
            .order_by(ComentarioTarea.creado_at.asc())
            .offset(offset)
            .limit(limit)
        )
        data_result = await self.session.execute(data_q)
        items = list(data_result.scalars().all())
        return items, total
