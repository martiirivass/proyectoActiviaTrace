from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.umbral_materia import UmbralMateria
from app.repositories.base import TenantScopedRepository


class UmbralMateriaRepository(TenantScopedRepository[UmbralMateria]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(UmbralMateria, session, tenant_id)

    async def get_by_asignacion(self, asignacion_id: UUID) -> UmbralMateria | None:
        stmt = (
            select(UmbralMateria)
            .where(
                UmbralMateria.tenant_id == self.tenant_id,
                UmbralMateria.asignacion_id == asignacion_id,
                UmbralMateria.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        asignacion_id: UUID,
        materia_id: UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str] | None,
    ) -> UmbralMateria:
        existing = await self.get_by_asignacion(asignacion_id)
        if existing:
            existing.umbral_pct = umbral_pct
            existing.valores_aprobatorios = valores_aprobatorios
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        return await self.create(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios,
        )
