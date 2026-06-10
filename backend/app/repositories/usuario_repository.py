from uuid import UUID

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import TenantScopedRepository


class UsuarioRepository(TenantScopedRepository[User]):
    async def find_by_email(self, email: str) -> User | None:
        stmt = select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.email == email,
            self.model.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
