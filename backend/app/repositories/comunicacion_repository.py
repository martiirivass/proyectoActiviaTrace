from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.lote_comunicacion import EstadoLote, LoteComunicacion
from app.repositories.base import TenantScopedRepository


class ComunicacionRepository(TenantScopedRepository[Comunicacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Comunicacion, session, tenant_id)

    async def create_comunicacion(self, **kwargs) -> Comunicacion:
        obj = Comunicacion(tenant_id=self.tenant_id, **kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def bulk_create_comunicaciones(self, entries: list[dict]) -> list[Comunicacion]:
        objs = []
        for entry in entries:
            obj = Comunicacion(tenant_id=self.tenant_id, **entry)
            self.session.add(obj)
            objs.append(obj)
        await self.session.flush()
        for obj in objs:
            await self.session.refresh(obj)
        return objs

    async def list_by_lote(self, lote_id: UUID) -> list[Comunicacion]:
        stmt = (
            select(Comunicacion)
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.lote_id == lote_id,
                Comunicacion.is_deleted == False,
            )
            .order_by(Comunicacion.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_materia(
        self, materia_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Comunicacion]:
        stmt = (
            select(Comunicacion)
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.materia_id == materia_id,
                Comunicacion.is_deleted == False,
            )
            .order_by(Comunicacion.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_materia(self, materia_id: UUID) -> int:
        stmt = (
            select(Comunicacion)
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.materia_id == materia_id,
                Comunicacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))

    async def count_by_estado(self, materia_id: UUID) -> dict[str, int]:
        from sqlalchemy import func

        stmt = (
            select(Comunicacion.estado, func.count(Comunicacion.id))
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.materia_id == materia_id,
                Comunicacion.is_deleted == False,
            )
            .group_by(Comunicacion.estado)
        )
        result = await self.session.execute(stmt)
        counts = {"Pendiente": 0, "Enviando": 0, "Enviado": 0, "Error": 0, "Cancelado": 0}
        for row in result.all():
            counts[row.estado.value] = row[1]
        return counts

    async def find_pendientes_para_procesar(self, limit: int = 20) -> list[Comunicacion]:
        """Find Pendiente comunicaciones that are ready for processing:
        - No lote_id (individual), OR
        - lote_id IS NOT NULL AND the lote is Aprobado
        """
        lote_subquery = (
            select(LoteComunicacion.id)
            .where(
                LoteComunicacion.estado == EstadoLote.APROBADO,
                LoteComunicacion.is_deleted == False,
            )
        ).subquery()

        stmt = (
            select(Comunicacion)
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.estado == EstadoComunicacion.PENDIENTE,
                Comunicacion.is_deleted == False,
                (
                    (Comunicacion.lote_id.is_(None))
                    | (Comunicacion.lote_id.in_(select(lote_subquery.c.id)))
                ),
            )
            .limit(limit)
            .order_by(Comunicacion.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def actualizar_estado(
        self,
        comunicacion_id: UUID,
        estado: EstadoComunicacion,
        error_msg: str | None = None,
        enviado_at: datetime | None = None,
    ) -> Comunicacion | None:
        stmt = (
            select(Comunicacion)
            .where(
                Comunicacion.id == comunicacion_id,
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            return None
        obj.estado = estado
        if error_msg is not None:
            obj.error_msg = error_msg
        if enviado_at is not None:
            obj.enviado_at = enviado_at
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def cancelar_por_lote(self, lote_id: UUID) -> int:
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.lote_id == lote_id,
                Comunicacion.estado == EstadoComunicacion.PENDIENTE,
                Comunicacion.is_deleted == False,
            )
            .values(
                estado=EstadoComunicacion.CANCELADO,
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount
