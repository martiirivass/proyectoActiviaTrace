from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lote_comunicacion import EstadoLote, LoteComunicacion
from app.repositories.base import TenantScopedRepository


class LoteComunicacionRepository(TenantScopedRepository[LoteComunicacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(LoteComunicacion, session, tenant_id)

    async def create_lote(self, **kwargs) -> LoteComunicacion:
        obj = LoteComunicacion(tenant_id=self.tenant_id, **kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def get_by_id(self, lote_id: UUID) -> LoteComunicacion | None:
        stmt = (
            select(LoteComunicacion)
            .where(
                LoteComunicacion.id == lote_id,
                LoteComunicacion.tenant_id == self.tenant_id,
                LoteComunicacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pendientes(self) -> list[LoteComunicacion]:
        stmt = (
            select(LoteComunicacion)
            .where(
                LoteComunicacion.tenant_id == self.tenant_id,
                LoteComunicacion.estado == EstadoLote.PENDIENTE,
                LoteComunicacion.is_deleted == False,
            )
            .order_by(LoteComunicacion.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def aprobar(self, lote_id: UUID, aprobado_por: UUID) -> LoteComunicacion | None:
        stmt = (
            select(LoteComunicacion)
            .where(
                LoteComunicacion.id == lote_id,
                LoteComunicacion.tenant_id == self.tenant_id,
                LoteComunicacion.estado == EstadoLote.PENDIENTE,
                LoteComunicacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            return None
        obj.estado = EstadoLote.APROBADO
        obj.aprobado_por = aprobado_por
        obj.aprobado_en = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def rechazar(self, lote_id: UUID) -> LoteComunicacion | None:
        stmt = (
            select(LoteComunicacion)
            .where(
                LoteComunicacion.id == lote_id,
                LoteComunicacion.tenant_id == self.tenant_id,
                LoteComunicacion.estado == EstadoLote.PENDIENTE,
                LoteComunicacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            return None
        obj.estado = EstadoLote.RECHAZADO
        obj.rechazado_en = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj
