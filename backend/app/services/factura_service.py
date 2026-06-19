from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import FACTURA_ABONAR, FACTURA_CARGAR, FACTURA_ELIMINAR
from app.models.factura import Factura
from app.models.materia import Materia
from app.models.user import User
from app.repositories.factura_repository import FacturaRepository
from app.schemas.liquidaciones import (
    FacturaCreate,
    FacturaListResponse,
    FacturaResponse,
)
from app.services.audit_service import AuditService

import re


class FacturaService:
    def __init__(self, session: AsyncSession, tenant_id: UUID, actor_id: UUID):
        self.repo = FacturaRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.audit = AuditService(session)

    async def listar(
        self,
        periodo: str | None = None,
        usuario_id: UUID | None = None,
        estado: str | None = None,
        materia_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> FacturaListResponse:
        items, total = await self.repo.list_by_filters(
            periodo=periodo,
            usuario_id=usuario_id,
            estado=estado,
            materia_id=materia_id,
            offset=offset,
            limit=limit,
        )

        return FacturaListResponse(
            items=[FacturaResponse.model_validate(i) for i in items],
            total=total,
            offset=offset,
            limit=limit,
        )

    async def crear(self, data: FacturaCreate) -> FacturaResponse:
        # Validate periodo format
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", data.periodo):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Periodo debe tener formato AAAA-MM (ej: 2026-06)",
            )

        # Validate usuario exists in this tenant
        user = await self._get_user_or_404(data.usuario_id)

        # Validate materia_id if provided
        if data.materia_id is not None:
            materia = await self.session.get(Materia, data.materia_id)
            if not materia or materia.tenant_id != self.tenant_id or materia.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Materia {data.materia_id} no encontrada en el tenant",
                )

        factura = Factura(
            tenant_id=self.tenant_id,
            usuario_id=data.usuario_id,
            periodo=data.periodo,
            detalle=data.detalle,
            referencia_archivo=data.referencia_archivo,
            tamano_kb=data.tamano_kb,
            estado="Pendiente",
            materia_id=data.materia_id,
        )
        self.session.add(factura)
        await self.session.flush()
        await self.session.refresh(factura)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=FACTURA_CARGAR,
            detalle={
                "factura_id": str(factura.id),
                "usuario_id": str(data.usuario_id),
                "periodo": data.periodo,
            },
        )

        return FacturaResponse.model_validate(factura)

    async def obtener(self, id: UUID) -> FacturaResponse:
        factura = await self.repo.get(id)
        if not factura:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Factura no encontrada",
            )
        return FacturaResponse.model_validate(factura)

    async def abonar(self, id: UUID) -> FacturaResponse:
        factura = await self.repo.get(id)
        if not factura:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Factura no encontrada",
            )

        if factura.estado == "Abonada":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La factura ya está abonada",
            )

        factura.estado = "Abonada"
        factura.abonada_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(factura)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=FACTURA_ABONAR,
            detalle={
                "factura_id": str(id),
                "usuario_id": str(factura.usuario_id),
                "periodo": factura.periodo,
            },
        )

        return FacturaResponse.model_validate(factura)

    async def eliminar(self, id: UUID) -> None:
        factura = await self.repo.get(id)
        if not factura:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Factura no encontrada",
            )

        await self.repo.soft_delete(id)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=FACTURA_ELIMINAR,
            detalle={"factura_id": str(id)},
        )

    # ── Helpers ────────────────────────────────────────────────────────────

    async def _get_user_or_404(self, usuario_id: UUID) -> User:
        """Get user scoped to tenant or raise 404."""
        stmt = select(User).where(
            User.id == usuario_id,
            User.tenant_id == self.tenant_id,
            User.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario {usuario_id} no encontrado en el tenant",
            )
        return user
