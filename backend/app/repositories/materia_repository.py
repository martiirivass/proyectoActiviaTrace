from sqlalchemy import select

from app.models.materia import Materia
from app.repositories.base import TenantScopedRepository


class MateriaRepository(TenantScopedRepository[Materia]):
    async def find_by_codigo(self, codigo: str) -> Materia | None:
        stmt = select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.codigo == codigo,
            self.model.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
