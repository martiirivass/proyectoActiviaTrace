from uuid import UUID

from sqlalchemy import select

from app.models.cohorte import Cohorte
from app.repositories.base import TenantScopedRepository


class CohorteRepository(TenantScopedRepository[Cohorte]):
    async def find_by_nombre_and_carrera(self, nombre: str, carrera_id: UUID) -> Cohorte | None:
        stmt = select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.nombre == nombre,
            self.model.carrera_id == carrera_id,
            self.model.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_carrera(self, carrera_id: UUID, offset: int = 0, limit: int | None = None) -> list[Cohorte]:
        return await self.list(carrera_id=carrera_id, offset=offset, limit=limit)
