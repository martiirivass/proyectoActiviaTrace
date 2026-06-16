from datetime import datetime
from uuid import UUID

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.comunicacion import Comunicacion


class AuditLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> AuditLog:
        obj = AuditLog(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def find(
        self,
        *,
        tenant_id: UUID,
        accion: str | None = None,
        actor_id: UUID | None = None,
        materia_id: UUID | None = None,
        materia_ids: list[UUID] | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).where(
            AuditLog.tenant_id == tenant_id
        )
        if accion is not None:
            stmt = stmt.where(AuditLog.accion == accion)
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if materia_id is not None:
            stmt = stmt.where(AuditLog.materia_id == materia_id)
        if materia_ids is not None:
            stmt = stmt.where(AuditLog.materia_id.in_(materia_ids))
        if desde is not None:
            stmt = stmt.where(AuditLog.fecha_hora >= desde)
        if hasta is not None:
            stmt = stmt.where(AuditLog.fecha_hora <= hasta)
        stmt = stmt.order_by(AuditLog.fecha_hora.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_actions_by_day(
        self,
        *,
        tenant_id: UUID,
        materia_ids: list[UUID] | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[dict]:
        date_col = cast(func.date_trunc("day", AuditLog.fecha_hora), Date).label("fecha")
        stmt = (
            select(date_col, func.count().label("total"))
            .where(AuditLog.tenant_id == tenant_id)
            .group_by(date_col)
            .order_by(date_col)
        )
        if materia_ids is not None:
            stmt = stmt.where(AuditLog.materia_id.in_(materia_ids))
        if desde is not None:
            stmt = stmt.where(AuditLog.fecha_hora >= desde)
        if hasta is not None:
            stmt = stmt.where(AuditLog.fecha_hora <= hasta)
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "fecha": row.fecha,
                "total": row.total,
            }
            for row in rows
        ]

    async def count_comms_by_docente(
        self,
        *,
        tenant_id: UUID,
        materia_ids: list[UUID] | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[dict]:
        stmt = (
            select(
                Comunicacion.enviado_por.label("docente_id"),
                Comunicacion.estado,
                func.count().label("total"),
            )
            .where(Comunicacion.tenant_id == tenant_id)
            .where(Comunicacion.is_deleted == False)
            .group_by(Comunicacion.enviado_por, Comunicacion.estado)
        )
        if materia_ids is not None:
            stmt = stmt.where(Comunicacion.materia_id.in_(materia_ids))
        if desde is not None:
            stmt = stmt.where(Comunicacion.created_at >= desde)
        if hasta is not None:
            stmt = stmt.where(Comunicacion.created_at <= hasta)
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "docente_id": row.docente_id,
                "estado": row.estado,
                "total": row.total,
            }
            for row in rows
        ]

    async def count_interactions_by_docente_materia(
        self,
        *,
        tenant_id: UUID,
        materia_ids: list[UUID] | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[dict]:
        stmt = (
            select(
                AuditLog.actor_id.label("actor_id"),
                AuditLog.materia_id.label("materia_id"),
                AuditLog.accion,
                func.count().label("total"),
            )
            .where(AuditLog.tenant_id == tenant_id)
            .where(AuditLog.materia_id.isnot(None))
            .group_by(AuditLog.actor_id, AuditLog.materia_id, AuditLog.accion)
        )
        if materia_ids is not None:
            stmt = stmt.where(AuditLog.materia_id.in_(materia_ids))
        if desde is not None:
            stmt = stmt.where(AuditLog.fecha_hora >= desde)
        if hasta is not None:
            stmt = stmt.where(AuditLog.fecha_hora <= hasta)
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "actor_id": row.actor_id,
                "materia_id": row.materia_id,
                "accion": row.accion,
                "total": row.total,
            }
            for row in rows
        ]

    async def find_recent(
        self,
        *,
        tenant_id: UUID,
        materia_ids: list[UUID] | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        limit: int = 200,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        if materia_ids is not None:
            stmt = stmt.where(AuditLog.materia_id.in_(materia_ids))
        if desde is not None:
            stmt = stmt.where(AuditLog.fecha_hora >= desde)
        if hasta is not None:
            stmt = stmt.where(AuditLog.fecha_hora <= hasta)
        stmt = stmt.order_by(AuditLog.fecha_hora.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
