from datetime import date
from uuid import UUID

from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardia import EstadoGuardia
from app.repositories.guardia_repository import GuardiaRepository
from app.schemas.guardias import GuardiaCreate, GuardiaListResponse, GuardiaResponse, GuardiaUpdate
from app.services.audit_service import AuditService


class GuardiaService:
    def __init__(self, session: AsyncSession, tenant_id: UUID, current_user_id: UUID, roles: list[str]):
        self.repo = GuardiaRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.roles = roles
        self.audit = AuditService(session)

    async def registrar_guardia(
        self,
        data: GuardiaCreate,
        actor_id: UUID,
    ) -> GuardiaResponse:
        """Register a new guardia."""
        from app.models.asignacion import Asignacion
        from sqlalchemy import select

        # Verify asignacion exists and belongs to tenant
        stmt = (
            select(Asignacion)
            .where(
                Asignacion.id == data.asignacion_id,
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        asignacion = result.scalar_one_or_none()

        if not asignacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación no encontrada",
            )

        # TUTOR solo puede registrar para su propia asignación
        if "TUTOR" in self.roles:
            if asignacion.usuario_id != self.current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puede registrar una guardia para una asignación que no le pertenece",
                )

        guardia = await self.repo.create(
            asignacion_id=data.asignacion_id,
            materia_id=data.materia_id,
            carrera_id=data.carrera_id,
            cohorte_id=data.cohorte_id,
            dia=data.dia,
            horario=data.horario,
            estado=EstadoGuardia.PENDIENTE,
            comentarios=data.comentarios,
        )

        # Audit
        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion="GUARDIA_REGISTRAR",
            materia_id=data.materia_id,
            detalle={
                "guardia_id": str(guardia.id),
                "asignacion_id": str(data.asignacion_id),
                "dia": data.dia,
                "horario": data.horario,
            },
        )

        return GuardiaResponse.model_validate(guardia)

    async def actualizar_estado_guardia(
        self,
        guardia_id: UUID,
        data: GuardiaUpdate,
    ) -> GuardiaResponse:
        """Update guardia estado. Only the owning TUTOR or COORDINADOR can update."""
        guardia = await self.repo.get(guardia_id)
        if not guardia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardia no encontrada",
            )

        # Validate ownership or role
        from app.models.asignacion import Asignacion
        from sqlalchemy import select

        stmt = (
            select(Asignacion)
            .where(
                Asignacion.id == guardia.asignacion_id,
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        asignacion = result.scalar_one_or_none()

        is_owner = asignacion and asignacion.usuario_id == self.current_user_id
        is_coordinador = "COORDINADOR" in self.roles or "ADMIN" in self.roles

        if not is_owner and not is_coordinador:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para modificar esta guardia",
            )

        # Validate estado transition
        nuevo_estado = EstadoGuardia(data.estado)
        guardia.estado = nuevo_estado

        if data.comentarios is not None:
            guardia.comentarios = data.comentarios

        await self.session.flush()
        await self.session.refresh(guardia)

        return GuardiaResponse.model_validate(guardia)

    async def listar_guardias(
        self,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        dia: str | None = None,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> GuardiaListResponse:
        items, total = await self.repo.list_with_filters(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            dia=dia,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            offset=offset,
            limit=limit,
        )
        return GuardiaListResponse(
            items=[GuardiaResponse.model_validate(i) for i in items],
            total=total,
        )

    async def exportar_csv(
        self,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        dia: str | None = None,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> Response:
        csv_content = await self.repo.export_csv(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            dia=dia,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=guardias.csv"},
        )
