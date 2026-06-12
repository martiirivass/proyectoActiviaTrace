from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.aviso import Aviso
from app.repositories.acknowledgment_repository import AcknowledgmentRepository
from app.repositories.aviso_repository import AvisoRepository
from app.schemas.avisos import (
    AckResponse,
    AckUserListResponse,
    AckUserResponse,
    AvisoCreate,
    AvisoListResponse,
    AvisoResponse,
    AvisoStatsResponse,
    AvisoUpdate,
)
from app.services.audit_service import AuditService


class AvisoService:
    def __init__(self, session: AsyncSession, tenant_id: UUID, current_user_id: UUID, roles: list[str]):
        self.repo = AvisoRepository(session, tenant_id)
        self.ack_repo = AcknowledgmentRepository(session)
        self.session = session
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.roles = roles
        self.audit = AuditService(session)

    async def _resolve_user_context(self) -> tuple[str, list[UUID], list[UUID]]:
        """Resolve current user's rol, cohorte_ids, and materia_ids."""
        # Determine effective role (first role)
        rol = self.roles[0] if self.roles else ""

        # Get materia_ids from active asignaciones
        stmt_m = (
            select(Asignacion.materia_id)
            .where(
                Asignacion.usuario_id == self.current_user_id,
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.is_deleted == False,
                Asignacion.materia_id.isnot(None),
            )
            .distinct()
        )
        result_m = await self.session.execute(stmt_m)
        materia_ids = [row[0] for row in result_m.all() if row[0]]

        # Get cohorte_ids from active asignaciones
        stmt_c = (
            select(Asignacion.cohorte_id)
            .where(
                Asignacion.usuario_id == self.current_user_id,
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.is_deleted == False,
                Asignacion.cohorte_id.isnot(None),
            )
            .distinct()
        )
        result_c = await self.session.execute(stmt_c)
        cohorte_ids = [row[0] for row in result_c.all() if row[0]]

        return rol, cohorte_ids, materia_ids

    async def _check_aviso_exists(self, aviso_id: UUID) -> Aviso:
        """Check aviso exists and belongs to tenant, return it or raise 404."""
        aviso = await self.repo.get(aviso_id)
        if not aviso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )
        return aviso

    async def crear_aviso(self, data: AvisoCreate, actor_id: UUID) -> AvisoResponse:
        """Create a new aviso."""
        aviso = await self.repo.create(
            alcance=data.alcance,
            materia_id=data.materia_id,
            cohorte_id=data.cohorte_id,
            rol_destino=data.rol_destino,
            severidad=data.severidad,
            titulo=data.titulo,
            cuerpo=data.cuerpo,
            inicio_en=data.inicio_en,
            fin_en=data.fin_en,
            orden=data.orden,
            activo=data.activo,
            requiere_ack=data.requiere_ack,
        )

        # Audit
        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion="AVISO_CREAR",
            materia_id=data.materia_id,
            detalle={
                "aviso_id": str(aviso.id),
                "titulo": data.titulo,
                "alcance": data.alcance,
                "severidad": data.severidad,
            },
        )

        return AvisoResponse.model_validate(aviso)

    async def editar_aviso(self, aviso_id: UUID, data: AvisoUpdate, actor_id: UUID) -> AvisoResponse:
        """Edit an existing aviso."""
        aviso = await self._check_aviso_exists(aviso_id)

        # Build update dict with only provided fields
        update_kwargs = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not update_kwargs:
            return AvisoResponse.model_validate(aviso)

        # Update fields
        for key, value in update_kwargs.items():
            if hasattr(aviso, key):
                setattr(aviso, key, value)

        await self.session.flush()
        await self.session.refresh(aviso)

        # Audit
        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion="AVISO_EDITAR",
            materia_id=aviso.materia_id,
            detalle={
                "aviso_id": str(aviso.id),
                "campos_actualizados": list(update_kwargs.keys()),
            },
        )

        return AvisoResponse.model_validate(aviso)

    async def eliminar_aviso(self, aviso_id: UUID, actor_id: UUID) -> None:
        """Soft delete an aviso."""
        aviso = await self._check_aviso_exists(aviso_id)

        aviso.soft_delete()
        await self.session.flush()

        # Audit
        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion="AVISO_ELIMINAR",
            detalle={"aviso_id": str(aviso.id)},
        )

    async def listar_avisos_activos(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> AvisoListResponse:
        """List active avisos visible for the current user."""
        rol, cohorte_ids, materia_ids = await self._resolve_user_context()

        items, total = await self.repo.list_activos_for_user(
            usuario_id=self.current_user_id,
            rol=rol,
            cohorte_ids=cohorte_ids,
            materia_ids=materia_ids,
            offset=offset,
            limit=limit,
        )

        # Enrich with acknowledged status
        aviso_responses = []
        for aviso in items:
            acknowledged = await self.ack_repo.has_acknowledged(aviso.id, self.current_user_id)
            aviso_responses.append(AvisoResponse.from_orm_with_ack(aviso, acknowledged=acknowledged))

        return AvisoListResponse(
            items=aviso_responses,
            total=total,
            offset=offset,
            limit=limit,
        )

    async def obtener_detalle(self, aviso_id: UUID) -> AvisoResponse:
        """Get aviso detail if visible for the current user."""
        rol, cohorte_ids, materia_ids = await self._resolve_user_context()

        aviso = await self.repo.get_by_id_if_visible(
            aviso_id=aviso_id,
            usuario_id=self.current_user_id,
            rol=rol,
            cohorte_ids=cohorte_ids,
            materia_ids=materia_ids,
        )
        if not aviso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )

        acknowledged = await self.ack_repo.has_acknowledged(aviso.id, self.current_user_id)
        return AvisoResponse.from_orm_with_ack(aviso, acknowledged=acknowledged)

    async def confirmar_lectura(self, aviso_id: UUID, actor_id: UUID) -> AckResponse:
        """Confirm reading of an aviso (idempotent)."""
        # First check aviso is visible
        await self.obtener_detalle(aviso_id)

        # Insert ack (idempotent via ON CONFLICT DO NOTHING)
        self.ack_repo.session = self.session  # Ensure same session
        await self.ack_repo.create_or_ignore(aviso_id, self.current_user_id)

        # Audit
        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion="AVISO_ACK",
            detalle={
                "aviso_id": str(aviso_id),
                "usuario_id": str(self.current_user_id),
            },
        )

        return AckResponse()

    async def obtener_stats(self, aviso_id: UUID) -> AvisoStatsResponse:
        """Get acknowledgment stats for an aviso."""
        aviso = await self._check_aviso_exists(aviso_id)

        total_usuarios = await self.repo.count_usuarios_alcanzados(aviso)
        total_acks = await self.ack_repo.count_by_aviso(aviso_id)

        porcentaje = 0.0
        if total_usuarios > 0:
            porcentaje = round((total_acks / total_usuarios) * 100, 2)

        return AvisoStatsResponse(
            aviso_id=aviso_id,
            total_usuarios_alcanzados=total_usuarios,
            total_acknowledgments=total_acks,
            porcentaje_confirmacion=porcentaje,
        )

    async def listar_acks(
        self,
        aviso_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> AckUserListResponse:
        """List users who confirmed reading an aviso."""
        # Verify aviso exists
        await self._check_aviso_exists(aviso_id)

        items, total = await self.ack_repo.list_users_by_aviso(
            aviso_id=aviso_id,
            offset=offset,
            limit=limit,
        )

        return AckUserListResponse(
            items=[AckUserResponse(**item) for item in items],
            total=total,
            offset=offset,
            limit=limit,
        )
