from uuid import UUID

from sqlalchemy import select

from app.models.asignacion import Asignacion
from app.repositories.base import TenantScopedRepository


class AsignacionRepository(TenantScopedRepository[Asignacion]):
    async def list(
        self,
        include_deleted: bool = False,
        offset: int = 0,
        limit: int | None = None,
        **filters,
    ) -> list[Asignacion]:
        stmt = select(self.model).where(self.model.tenant_id == self.tenant_id)
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        if "usuario_id" in filters and filters["usuario_id"] is not None:
            stmt = stmt.where(self.model.usuario_id == filters["usuario_id"])
        if "materia_id" in filters and filters["materia_id"] is not None:
            stmt = stmt.where(self.model.materia_id == filters["materia_id"])
        if "rol" in filters and filters["rol"] is not None:
            stmt = stmt.where(self.model.rol == filters["rol"])
        if limit is not None:
            stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
