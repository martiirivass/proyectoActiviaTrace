from uuid import UUID

from sqlalchemy import select

from app.models.dictado import Dictado
from app.repositories.base import TenantScopedRepository


class DictadoRepository(TenantScopedRepository[Dictado]):
    async def find_by_materia_and_cohorte(self, materia_id: UUID, cohorte_id: UUID) -> Dictado | None:
        stmt = select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.materia_id == materia_id,
            self.model.cohorte_id == cohorte_id,
            self.model.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_materia(self, materia_id: UUID, offset: int = 0, limit: int | None = None) -> list[Dictado]:
        return await self.list(materia_id=materia_id, offset=offset, limit=limit)

    async def list_by_cohorte(self, cohorte_id: UUID, offset: int = 0, limit: int | None = None) -> list[Dictado]:
        return await self.list(cohorte_id=cohorte_id, offset=offset, limit=limit)
