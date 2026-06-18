from sqlalchemy import select

from app.models.carrera import Carrera
from app.repositories.base import TenantScopedRepository


class CarreraRepository(TenantScopedRepository[Carrera]):
    async def find_by_codigo(self, codigo: str) -> Carrera | None:
        stmt = select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.codigo == codigo,
            self.model.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
