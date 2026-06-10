from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AuditLogRepository(session)

    async def log(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        accion: str,
        detalle: dict | None = None,
        impersonado_id: UUID | None = None,
        materia_id: UUID | None = None,
        filas_afectadas: int = 0,
        ip: str | None = None,
        user_agent: str | None = None,
    ):
        return await self.repo.create(
            tenant_id=tenant_id,
            actor_id=actor_id,
            accion=accion,
            detalle=detalle,
            impersonado_id=impersonado_id,
            materia_id=materia_id,
            filas_afectadas=filas_afectadas,
            ip=ip,
            user_agent=user_agent,
        )

    async def get_log(
        self,
        *,
        tenant_id: UUID,
        accion: str | None = None,
        actor_id: UUID | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ):
        return await self.repo.find(
            tenant_id=tenant_id,
            accion=accion,
            actor_id=actor_id,
            desde=desde,
            hasta=hasta,
            offset=offset,
            limit=limit,
        )
