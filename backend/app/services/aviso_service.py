from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AVISO_ACK, AVISO_CREAR, AVISO_EDITAR, AVISO_ELIMINAR
from app.models import Asignacion, UserRole
from app.repositories.aviso_repository import AcknowledgmentRepository, AvisoRepository
from app.schemas.avisos import (
    AcknowledgmentResponse,
    AvisoCreate,
    AvisoDetailResponse,
    AvisoListItem,
    AvisoListResponse,
    AvisoResponse,
    AvisoUpdate,
    ConfirmacionItem,
    MetricasAvisoResponse,
)
from app.services.audit_service import AuditService


class AvisoService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.aviso_repo = AvisoRepository(session, tenant_id)
        self.ack_repo = AcknowledgmentRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.audit = AuditService(session)

    async def crear_aviso(
        self,
        data: AvisoCreate,
        actor_id: UUID,
    ) -> AvisoResponse:
        if data.alcance == "PorMateria" and not data.materia_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="alcance PorMateria requiere materia_id",
            )
        if data.alcance == "PorCohorte" and not data.cohorte_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="alcance PorCohorte requiere cohorte_id",
            )

        aviso = await self.aviso_repo.create(**data.model_dump())

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=AVISO_CREAR,
            detalle={
                "aviso_id": str(aviso.id),
                "alcance": data.alcance,
                "severidad": data.severidad,
                "titulo": data.titulo,
                "requiere_ack": data.requiere_ack,
            },
        )

        await self.session.refresh(aviso)
        return AvisoResponse.model_validate(aviso)

    async def editar_aviso(
        self,
        aviso_id: UUID,
        data: AvisoUpdate,
        actor_id: UUID,
    ) -> AvisoResponse:
        aviso = await self.aviso_repo.get(aviso_id)
        if not aviso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return AvisoResponse.model_validate(aviso)

        for key, value in update_data.items():
            setattr(aviso, key, value)
        await self.session.flush()
        await self.session.refresh(aviso)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=AVISO_EDITAR,
            detalle={
                "aviso_id": str(aviso_id),
                "cambios": update_data,
            },
        )

        return AvisoResponse.model_validate(aviso)

    async def eliminar_aviso(
        self,
        aviso_id: UUID,
        actor_id: UUID,
    ) -> None:
        aviso = await self.aviso_repo.get(aviso_id)
        if not aviso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )

        await self.aviso_repo.soft_delete(aviso_id)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=AVISO_ELIMINAR,
            detalle={"aviso_id": str(aviso_id)},
        )

    async def listar_avisos(
        self,
        alcance: str | None = None,
        severidad: str | None = None,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        activo: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> AvisoListResponse:
        items, total = await self.aviso_repo.list_with_filters(
            alcance=alcance,
            severidad=severidad,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            activo=activo,
            offset=offset,
            limit=limit,
        )

        result_items = [
            AvisoListItem(
                id=av.id,
                alcance=av.alcance.value if hasattr(av.alcance, "value") else str(av.alcance),
                severidad=av.severidad.value if hasattr(av.severidad, "value") else str(av.severidad),
                titulo=av.titulo,
                cuerpo=av.cuerpo,
                inicio_en=av.inicio_en,
                fin_en=av.fin_en,
                orden=av.orden,
                activo=av.activo,
                requiere_ack=av.requiere_ack,
                created_at=av.created_at,
                updated_at=av.updated_at,
            )
            for av in items
        ]

        return AvisoListResponse(items=result_items, total=total)

    async def listar_avisos_visibles(
        self,
        usuario_id: UUID,
        roles: list[str],
        offset: int = 0,
        limit: int = 50,
    ) -> AvisoListResponse:
        asignaciones_q = select(Asignacion.materia_id, Asignacion.cohorte_id).where(
            Asignacion.usuario_id == usuario_id,
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.is_deleted == False,
        )
        asignaciones_result = await self.session.execute(asignaciones_q)
        asignaciones = list(asignaciones_result.all())

        materia_ids = list({a.materia_id for a in asignaciones if a.materia_id})
        cohorte_ids = list({a.cohorte_id for a in asignaciones if a.cohorte_id})

        items, total = await self.aviso_repo.list_visibles_para_usuario(
            materia_ids=materia_ids,
            cohorte_ids=cohorte_ids,
            roles=roles,
            usuario_id=usuario_id,
            offset=offset,
            limit=limit,
        )

        result_items = [
            AvisoListItem(
                id=av.id,
                alcance=av.alcance.value if hasattr(av.alcance, "value") else str(av.alcance),
                severidad=av.severidad.value if hasattr(av.severidad, "value") else str(av.severidad),
                titulo=av.titulo,
                cuerpo=av.cuerpo,
                inicio_en=av.inicio_en,
                fin_en=av.fin_en,
                orden=av.orden,
                activo=av.activo,
                requiere_ack=av.requiere_ack,
                created_at=av.created_at,
                updated_at=av.updated_at,
            )
            for av in items
        ]

        return AvisoListResponse(items=result_items, total=total)

    async def obtener_detalle(
        self,
        aviso_id: UUID,
    ) -> AvisoDetailResponse:
        detail = await self.aviso_repo.get_with_metrics(aviso_id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )

        av = detail["aviso"]
        return AvisoDetailResponse(
            id=av.id,
            tenant_id=av.tenant_id,
            alcance=av.alcance.value if hasattr(av.alcance, "value") else str(av.alcance),
            materia_id=av.materia_id,
            cohorte_id=av.cohorte_id,
            rol_destino=av.rol_destino,
            severidad=av.severidad.value if hasattr(av.severidad, "value") else str(av.severidad),
            titulo=av.titulo,
            cuerpo=av.cuerpo,
            inicio_en=av.inicio_en,
            fin_en=av.fin_en,
            orden=av.orden,
            activo=av.activo,
            requiere_ack=av.requiere_ack,
            is_deleted=av.is_deleted,
            created_at=av.created_at,
            updated_at=av.updated_at,
            total_vistos=detail["total_vistos"],
            total_confirmados=detail["total_confirmados"],
        )

    async def acknowledge_aviso(
        self,
        aviso_id: UUID,
        usuario_id: UUID,
        actor_id: UUID,
    ) -> AcknowledgmentResponse:
        aviso = await self.aviso_repo.get(aviso_id)
        if not aviso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )

        if not aviso.requiere_ack:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este aviso no requiere confirmación",
            )

        existing = await self.ack_repo.usuario_ya_ackeo(aviso_id, usuario_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya confirmaste este aviso",
            )

        ack = await self.ack_repo.create(
            aviso_id=aviso_id,
            usuario_id=usuario_id,
            confirmado_at=datetime.now(timezone.utc),
        )

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=AVISO_ACK,
            detalle={
                "aviso_id": str(aviso_id),
                "usuario_id": str(usuario_id),
            },
        )

        return AcknowledgmentResponse.model_validate(ack)

    async def obtener_metricas(
        self,
        aviso_id: UUID,
    ) -> MetricasAvisoResponse:
        detail = await self.aviso_repo.get_metricas(aviso_id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )

        return MetricasAvisoResponse(
            aviso_id=aviso_id,
            total_vistos=detail["total_vistos"],
            total_confirmados=detail["total_confirmados"],
            confirmaciones=[
                ConfirmacionItem(
                    usuario_id=ack.usuario_id,
                    confirmado_at=ack.confirmado_at,
                )
                for ack in detail["confirmaciones"]
            ],
        )
