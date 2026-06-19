from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comentario_tarea import ComentarioTarea
from app.models.tarea import EstadoTarea, Tarea
from app.repositories.comentario_repository import ComentarioTareaRepository
from app.repositories.tarea_repository import TareaRepository
from app.schemas.tareas import (
    ComentarioCreate,
    ComentarioResponse,
    TareaCreate,
    TareaListResponse,
    TareaResponse,
    TareaUpdate,
)
from app.services.audit_service import AuditService

# Valid state transitions: current -> allowed next states
_VALID_TRANSITIONS: dict[EstadoTarea, set[EstadoTarea]] = {
    EstadoTarea.Pendiente: {EstadoTarea.EnProgreso, EstadoTarea.Cancelada},
    EstadoTarea.EnProgreso: {EstadoTarea.Resuelta, EstadoTarea.Cancelada},
    EstadoTarea.Resuelta: {EstadoTarea.Cancelada},
    EstadoTarea.Cancelada: set(),
}

# States that only tareas:admin can set
_ADMIN_ONLY_STATES: set[EstadoTarea] = {EstadoTarea.Cancelada}


class TareaService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        current_user_id: UUID,
        roles: list[str],
    ):
        self.repo = TareaRepository(session, tenant_id)
        self.comentario_repo = ComentarioTareaRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.roles = roles
        self.audit = AuditService(session)
        self.is_admin = any(r in ("COORDINADOR", "ADMIN") for r in roles)

    async def _get_tarea_or_404(self, tarea_id: UUID) -> Tarea:
        """Get tarea by id, raise 404 if not found."""
        tarea = await self.repo.get(tarea_id)
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        return tarea

    async def _check_tarea_access(self, tarea: Tarea) -> None:
        """Check if current user can access the tarea.
        
        Admin can access any tarea. Others can only access tareas assigned to them.
        Raises 404 (not 403) to avoid revealing existence of other tareas.
        """
        if self.is_admin:
            return
        if tarea.asignado_a != self.current_user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )

    async def create_tarea(self, data: TareaCreate) -> TareaResponse:
        """Create a new tarea. Requires tareas:admin (enforced at router level)."""
        tarea = await self.repo.create(
            materia_id=data.materia_id,
            asignado_a=data.asignado_a,
            asignado_por=self.current_user_id,
            estado=EstadoTarea.Pendiente,
            descripcion=data.descripcion,
            contexto_id=data.contexto_id,
        )

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.current_user_id,
            accion="TAREA_CREAR",
            detalle={
                "tarea_id": str(tarea.id),
                "asignado_a": str(data.asignado_a),
                "descripcion": data.descripcion[:100],
            },
        )

        return TareaResponse.model_validate(tarea)

    async def get_tarea(self, tarea_id: UUID) -> TareaResponse:
        """Get tarea detail. Admin sees any; gestionar sees only own."""
        tarea = await self._get_tarea_or_404(tarea_id)
        await self._check_tarea_access(tarea)
        return TareaResponse.model_validate(tarea)

    async def list_tareas(
        self,
        offset: int = 0,
        limit: int = 50,
        estado: str | None = None,
        asignado_a: UUID | None = None,
        asignado_por: UUID | None = None,
        materia_id: UUID | None = None,
        q: str | None = None,
    ) -> TareaListResponse:
        """List tareas with filters. Admin sees all; gestionar sees only own.

        For non-admin users, the asignado_a filter is always overridden to
        the current user's id (they can only see their own tareas).
        """
        effective_asignado_a = asignado_a
        if not self.is_admin:
            effective_asignado_a = self.current_user_id

        items, total = await self.repo.list(
            offset=offset,
            limit=limit,
            estado=estado,
            asignado_a=effective_asignado_a,
            asignado_por=asignado_por,
            materia_id=materia_id,
            q=q,
        )

        return TareaListResponse(
            items=[TareaResponse.model_validate(t) for t in items],
            total=total,
            offset=offset,
            limit=limit,
        )

    async def update_tarea(self, tarea_id: UUID, data: TareaUpdate) -> TareaResponse:
        """Update tarea (estado, reassign, descripcion).

        Admin can update any tarea. Gestionar can only update own tarea,
        and only forward state transitions (not cancel, not reassign).
        """
        tarea = await self._get_tarea_or_404(tarea_id)

        # Check access: non-admin can only update own tareas
        if not self.is_admin and tarea.asignado_a != self.current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar esta tarea",
            )

        # Track what changed for audit
        cambios: dict[str, object] = {}

        # Validate and apply estado transition
        if data.estado is not None:
            nuevo_estado = self._validate_estado_value(data.estado)
            self._validate_transition(tarea.estado, nuevo_estado)
            cambios["estado_anterior"] = tarea.estado.value
            cambios["estado_nuevo"] = nuevo_estado.value
            tarea.estado = nuevo_estado

        # Reassign: only admin can reassign
        if data.asignado_a is not None:
            if not self.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para reasignar tareas",
                )
            cambios["asignado_a_anterior"] = str(tarea.asignado_a)
            cambios["asignado_a_nuevo"] = str(data.asignado_a)
            tarea.asignado_a = data.asignado_a

        # Update descripcion
        if data.descripcion is not None:
            cambios["descripcion_actualizada"] = True
            tarea.descripcion = data.descripcion

        await self.session.flush()
        await self.session.refresh(tarea)

        # Audit
        audit_accion = "TAREA_REASIGNAR" if "asignado_a_nuevo" in cambios else "TAREA_EDITAR"
        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.current_user_id,
            accion=audit_accion,
            detalle={
                "tarea_id": str(tarea_id),
                "cambios": cambios,
            },
        )

        return TareaResponse.model_validate(tarea)

    async def delete_tarea(self, tarea_id: UUID) -> None:
        """Soft delete a tarea. Requires tareas:admin (enforced at router level)."""
        tarea = await self._get_tarea_or_404(tarea_id)
        tarea.soft_delete()
        await self.session.flush()

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.current_user_id,
            accion="TAREA_ELIMINAR",
            detalle={"tarea_id": str(tarea_id)},
        )

    async def add_comentario(self, tarea_id: UUID, data: ComentarioCreate) -> ComentarioResponse:
        """Add a comment to a tarea. User must have access to the tarea."""
        tarea = await self._get_tarea_or_404(tarea_id)
        await self._check_tarea_access(tarea)

        comentario = await self.comentario_repo.create(
            tarea_id=tarea_id,
            autor_id=self.current_user_id,
            texto=data.texto,
        )

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.current_user_id,
            accion="COMENTARIO_CREAR",
            detalle={
                "tarea_id": str(tarea_id),
                "comentario_id": str(comentario.id),
            },
        )

        return ComentarioResponse.model_validate(comentario)

    async def list_comentarios(
        self,
        tarea_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ComentarioResponse]:
        """List comments for a tarea. User must have access to the tarea."""
        tarea = await self._get_tarea_or_404(tarea_id)
        await self._check_tarea_access(tarea)

        items, _total = await self.comentario_repo.list_by_tarea(
            tarea_id=tarea_id,
            offset=offset,
            limit=limit,
        )

        return [ComentarioResponse.model_validate(c) for c in items]

    # ---- Private helpers ----

    def _validate_estado_value(self, estado_str: str) -> EstadoTarea:
        """Convert string to EstadoTarea enum, raise 422 if invalid."""
        try:
            return EstadoTarea(estado_str)
        except ValueError:
            validos = [e.value for e in EstadoTarea]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Estado inválido: '{estado_str}'. Valores permitidos: {', '.join(validos)}",
            )

    def _validate_transition(self, estado_actual: EstadoTarea, nuevo_estado: EstadoTarea) -> None:
        """Validate state transition rules.

        Rules:
        1. Forward-only transitions (no going back)
        2. Cancelada is admin-only (enforced by caller for non-admin users)
        """
        allowed = _VALID_TRANSITIONS.get(estado_actual, set())

        if nuevo_estado not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Transición inválida: {estado_actual.value} → {nuevo_estado.value}. "
                    f"Solo se permite: {', '.join(a.value for a in allowed) if allowed else 'ninguna'}"
                ),
            )

        # Non-admin users cannot set admin-only states
        if not self.is_admin and nuevo_estado in _ADMIN_ONLY_STATES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Solo coordinación puede cambiar estado a '{nuevo_estado.value}'",
            )
