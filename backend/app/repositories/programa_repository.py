from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.programa_materia import ProgramaMateria
from app.repositories.base import TenantScopedRepository


class ProgramaMateriaRepository(TenantScopedRepository[ProgramaMateria]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(ProgramaMateria, session, tenant_id)

    async def find_by_materia_carrera_cohorte(
        self, materia_id: UUID, carrera_id: UUID, cohorte_id: UUID,
    ) -> ProgramaMateria | None:
        stmt = (
            select(ProgramaMateria)
            .where(
                ProgramaMateria.tenant_id == self.tenant_id,
                ProgramaMateria.materia_id == materia_id,
                ProgramaMateria.carrera_id == carrera_id,
                ProgramaMateria.cohorte_id == cohorte_id,
                ProgramaMateria.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        include_deleted: bool = False,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[ProgramaMateria]:
        stmt = select(ProgramaMateria).where(ProgramaMateria.tenant_id == self.tenant_id)
        if not include_deleted:
            stmt = stmt.where(ProgramaMateria.is_deleted == False)
        if materia_id is not None:
            stmt = stmt.where(ProgramaMateria.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(ProgramaMateria.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(ProgramaMateria.cohorte_id == cohorte_id)
        if limit is not None:
            stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
