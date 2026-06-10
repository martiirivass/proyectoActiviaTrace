from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select, update, func

from app.models.asignacion import Asignacion
from app.models.dictado import Dictado
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
        if "dictado_id" in filters and filters["dictado_id"] is not None:
            stmt = stmt.where(self.model.dictado_id == filters["dictado_id"])
        if "carrera_id" in filters and filters["carrera_id"] is not None:
            stmt = stmt.where(self.model.carrera_id == filters["carrera_id"])
        if "cohorte_id" in filters and filters["cohorte_id"] is not None:
            stmt = stmt.where(self.model.cohorte_id == filters["cohorte_id"])
        if limit is not None:
            stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_dictado(self, dictado_id: UUID) -> list[Asignacion]:
        return await self.list(dictado_id=dictado_id)

    async def bulk_create(self, asignaciones: list[dict]) -> list[Asignacion]:
        objs = [self.model(**a, tenant_id=self.tenant_id) for a in asignaciones]
        self.session.add_all(objs)
        await self.session.flush()
        for o in objs:
            await self.session.refresh(o)
        return objs

    async def update_vigencia(self, dictado_id: UUID, desde: date, hasta: date | None) -> int:
        stmt = (
            update(self.model)
            .where(
                self.model.tenant_id == self.tenant_id,
                self.model.dictado_id == dictado_id,
                self.model.is_deleted == False,
            )
            .values(desde=desde, hasta=hasta)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def count_by_dictado(self, dictado_id: UUID) -> int:
        stmt = select(func.count()).select_from(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.dictado_id == dictado_id,
            self.model.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
