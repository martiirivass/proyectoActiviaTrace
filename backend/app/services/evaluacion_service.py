from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import (
    COLOQUIO_CERRAR,
    COLOQUIO_CREAR,
    COLOQUIO_EDITAR,
)
from app.models import Role, User, UserRole
from app.models.evaluacion import DiaConvocatoria, Evaluacion, EvaluacionAlumnoConvocado, TipoEvaluacion
from app.repositories.evaluacion_repository import (
    DiaConvocatoriaRepository,
    EvaluacionAlumnoRepository,
    EvaluacionRepository,
)
from app.schemas.evaluaciones import (
    AlumnoConvocadoResponse,
    DiaConvocatoriaResponse,
    EvaluacionCreate,
    EvaluacionDetailResponse,
    EvaluacionListItem,
    EvaluacionListResponse,
    EvaluacionResponse,
    EvaluacionUpdate,
)
from app.services.audit_service import AuditService


class EvaluacionService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.eval_repo = EvaluacionRepository(session, tenant_id)
        self.dia_repo = DiaConvocatoriaRepository(session, tenant_id)
        self.alumno_repo = EvaluacionAlumnoRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.audit = AuditService(session)

    async def crear_convocatoria(
        self,
        data: EvaluacionCreate,
        actor_id: UUID,
    ) -> EvaluacionResponse:
        ev_data = data.model_dump(exclude={"dias"})
        ev = await self.eval_repo.create(**ev_data)

        dias_data = [
            {"evaluacion_id": ev.id, "fecha": d.fecha, "cupo_maximo": d.cupo_maximo}
            for d in data.dias
        ]
        await self.dia_repo.bulk_create(dias_data)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=COLOQUIO_CREAR,
            materia_id=data.materia_id,
            detalle={
                "evaluacion_id": str(ev.id),
                "tipo": data.tipo,
                "instancia": data.instancia,
                "dias_count": len(data.dias),
            },
        )

        await self.session.refresh(ev)
        return EvaluacionResponse.model_validate(ev)

    async def editar_convocatoria(
        self,
        evaluacion_id: UUID,
        data: EvaluacionUpdate,
        actor_id: UUID,
    ) -> EvaluacionResponse:
        ev = await self.eval_repo.get(evaluacion_id)
        if not ev:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )

        if ev.activa:
            from app.models.reserva_evaluacion import EstadoReserva, ReservaEvaluacion
            stmt = select(ReservaEvaluacion).where(
                ReservaEvaluacion.evaluacion_id == ev.id,
                ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
                ReservaEvaluacion.is_deleted == False,
            ).limit(1)
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No se puede editar una convocatoria con reservas activas",
                )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return EvaluacionResponse.model_validate(ev)

        for key, value in update_data.items():
            setattr(ev, key, value)
        await self.session.flush()
        await self.session.refresh(ev)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=COLOQUIO_EDITAR,
            detalle={
                "evaluacion_id": str(evaluacion_id),
                "cambios": update_data,
            },
        )

        return EvaluacionResponse.model_validate(ev)

    async def cerrar_convocatoria(
        self,
        evaluacion_id: UUID,
        actor_id: UUID,
    ) -> dict:
        ev = await self.eval_repo.get(evaluacion_id)
        if not ev:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )

        if not ev.activa:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La convocatoria ya está cerrada",
            )

        ev.activa = False

        from app.models.reserva_evaluacion import EstadoReserva, ReservaEvaluacion
        stmt = select(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == ev.id,
            ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
            ReservaEvaluacion.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        reservas = list(result.scalars().all())
        for r in reservas:
            r.estado = EstadoReserva.CANCELADA

        await self.session.flush()

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=COLOQUIO_CERRAR,
            detalle={
                "evaluacion_id": str(evaluacion_id),
                "reservas_canceladas": len(reservas),
            },
        )

        return {"message": "Convocatoria cerrada exitosamente", "reservas_canceladas": len(reservas)}

    async def importar_convocados(
        self,
        evaluacion_id: UUID,
        alumno_ids: list[UUID],
        actor_id: UUID,
    ) -> dict:
        ev = await self.eval_repo.get(evaluacion_id)
        if not ev:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )

        alumnos_role = await self.session.execute(
            select(Role).where(Role.name == "ALUMNO", Role.tenant_id == self.tenant_id)
        )
        role_alumno = alumnos_role.scalar_one_or_none()
        if not role_alumno:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No existe el rol ALUMNO en este tenant",
            )

        from sqlalchemy import select as sa_select
        validos = []
        invalidos = []
        for aid in alumno_ids:
            ur_stmt = sa_select(UserRole).where(
                UserRole.user_id == aid,
                UserRole.role_id == role_alumno.id,
                UserRole.tenant_id == self.tenant_id,
            )
            ur_result = await self.session.execute(ur_stmt)
            ur = ur_result.scalar_one_or_none()
            if ur is not None:
                validos.append(aid)
            else:
                invalidos.append(aid)

        if invalidos:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Los siguientes UUIDs no son alumnos válidos en el tenant: {[str(i) for i in invalidos]}",
            )

        convocados = await self.alumno_repo.reemplazar_convocados(evaluacion_id, validos)

        return {
            "message": f"Padrón actualizado: {len(convocados)} alumnos convocados",
            "total_convocados": len(convocados),
        }

    async def listar_convocatorias(
        self,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        activa: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> EvaluacionListResponse:
        items, total = await self.eval_repo.list_with_metrics(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            activa=activa,
            offset=offset,
            limit=limit,
        )

        result_items = []
        for item in items:
            ev = item["evaluacion"]
            result_items.append(EvaluacionListItem(
                id=ev.id,
                materia_id=ev.materia_id,
                cohorte_id=ev.cohorte_id,
                tipo=ev.tipo.value if hasattr(ev.tipo, "value") else str(ev.tipo),
                instancia=ev.instancia,
                activa=ev.activa,
                total_convocados=item["total_convocados"],
                reservas_activas=item["reservas_activas"],
                cupos_libres=item["cupos_libres"],
                created_at=ev.created_at,
                updated_at=ev.updated_at,
            ))

        return EvaluacionListResponse(items=result_items, total=total)

    async def obtener_detalle(self, evaluacion_id: UUID) -> EvaluacionDetailResponse:
        detail = await self.eval_repo.get_detail(evaluacion_id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )

        ev = detail["evaluacion"]
        return EvaluacionDetailResponse(
            id=ev.id,
            materia_id=ev.materia_id,
            cohorte_id=ev.cohorte_id,
            tipo=ev.tipo.value if hasattr(ev.tipo, "value") else str(ev.tipo),
            instancia=ev.instancia,
            activa=ev.activa,
            dias=[DiaConvocatoriaResponse.model_validate(d) for d in detail["dias"]],
            convocados=[AlumnoConvocadoResponse.model_validate(c) for c in detail["convocados"]],
            total_convocados=detail["total_convocados"],
            reservas_activas=detail["reservas_activas"],
            cupos_libres=detail["cupos_libres"],
            created_at=ev.created_at,
            updated_at=ev.updated_at,
        )

    async def listar_convocados(self, evaluacion_id: UUID) -> list[AlumnoConvocadoResponse]:
        ev = await self.eval_repo.get(evaluacion_id)
        if not ev:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )

        convocados = await self.alumno_repo.list_by_evaluacion(evaluacion_id)
        return [AlumnoConvocadoResponse.model_validate(c) for c in convocados]
