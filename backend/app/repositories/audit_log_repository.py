from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


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
        if desde is not None:
            stmt = stmt.where(AuditLog.fecha_hora >= desde)
        if hasta is not None:
            stmt = stmt.where(AuditLog.fecha_hora <= hasta)
        stmt = stmt.order_by(AuditLog.fecha_hora.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
