from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro
from app.repositories.base import TenantScopedRepository


class SlotEncuentroRepository(TenantScopedRepository[SlotEncuentro]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(SlotEncuentro, session, tenant_id)


class InstanciaEncuentroRepository(TenantScopedRepository[InstanciaEncuentro]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(InstanciaEncuentro, session, tenant_id)

    async def bulk_create_instancias(self, entries: list[dict]) -> list[InstanciaEncuentro]:
        """Bulk insert multiple instancias at once."""
        objs = []
        for entry in entries:
            obj = InstanciaEncuentro(tenant_id=self.tenant_id, **entry)
            self.session.add(obj)
            objs.append(obj)
        await self.session.flush()
        for obj in objs:
            await self.session.refresh(obj)
        return objs

    async def list_by_slot(self, slot_id: UUID) -> list[InstanciaEncuentro]:
        stmt = (
            select(InstanciaEncuentro)
            .where(
                InstanciaEncuentro.tenant_id == self.tenant_id,
                InstanciaEncuentro.slot_id == slot_id,
                InstanciaEncuentro.is_deleted == False,
            )
            .order_by(InstanciaEncuentro.fecha.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_admin(
        self,
        materia_id: UUID | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        estado: str | None = None,
        asignacion_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[InstanciaEncuentro], int]:
        """List instancias with admin filters, return (items, total)."""
        from sqlalchemy import func

        base_where = [
            InstanciaEncuentro.tenant_id == self.tenant_id,
            InstanciaEncuentro.is_deleted == False,
        ]
        if materia_id:
            base_where.append(InstanciaEncuentro.materia_id == materia_id)
        if fecha_desde:
            base_where.append(InstanciaEncuentro.fecha >= fecha_desde)
        if fecha_hasta:
            base_where.append(InstanciaEncuentro.fecha <= fecha_hasta)
        if estado:
            base_where.append(InstanciaEncuentro.estado == estado)
        if asignacion_id:
            # Filter by slot's asignacion_id via join
            slot_alias = SlotEncuentro.__table__.alias()
            base_where.append(slot_alias.c.asignacion_id == asignacion_id)
            count_q = (
                select(func.count(InstanciaEncuentro.id))
                .join(slot_alias, InstanciaEncuentro.slot_id == slot_alias.c.id)
                .where(*base_where)
            )
            count_result = await self.session.execute(count_q)
            total = count_result.scalar() or 0

            data_q = (
                select(InstanciaEncuentro)
                .join(slot_alias, InstanciaEncuentro.slot_id == slot_alias.c.id)
                .where(*base_where)
                .order_by(InstanciaEncuentro.fecha.desc())
                .offset(offset)
                .limit(limit)
            )
        else:
            count_q = (
                select(func.count(InstanciaEncuentro.id))
                .where(*base_where)
            )
            count_result = await self.session.execute(count_q)
            total = count_result.scalar() or 0

            data_q = (
                select(InstanciaEncuentro)
                .where(*base_where)
                .order_by(InstanciaEncuentro.fecha.desc())
                .offset(offset)
                .limit(limit)
            )

        data_result = await self.session.execute(data_q)
        items = list(data_result.scalars().all())
        return items, total
