from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fecha_academica import FechaAcademica, TipoFecha
from app.repositories.base import TenantScopedRepository


class FechaAcademicaRepository(TenantScopedRepository[FechaAcademica]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(FechaAcademica, session, tenant_id)

    async def find_by_unique(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        tipo: TipoFecha,
        numero: int,
        periodo: str,
    ) -> FechaAcademica | None:
        stmt = (
            select(FechaAcademica)
            .where(
                FechaAcademica.tenant_id == self.tenant_id,
                FechaAcademica.materia_id == materia_id,
                FechaAcademica.cohorte_id == cohorte_id,
                FechaAcademica.tipo == tipo,
                FechaAcademica.numero == numero,
                FechaAcademica.periodo == periodo,
                FechaAcademica.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        tipo: TipoFecha | None = None,
        periodo: str | None = None,
        include_deleted: bool = False,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[FechaAcademica]:
        stmt = (
            select(FechaAcademica)
            .where(FechaAcademica.tenant_id == self.tenant_id)
            .order_by(FechaAcademica.fecha.asc())
        )
        if not include_deleted:
            stmt = stmt.where(FechaAcademica.is_deleted == False)
        if materia_id is not None:
            stmt = stmt.where(FechaAcademica.materia_id == materia_id)
        if cohorte_id is not None:
            stmt = stmt.where(FechaAcademica.cohorte_id == cohorte_id)
        if tipo is not None:
            stmt = stmt.where(FechaAcademica.tipo == tipo)
        if periodo is not None:
            stmt = stmt.where(FechaAcademica.periodo == periodo)
        if limit is not None:
            stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
