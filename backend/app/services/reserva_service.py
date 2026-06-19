from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import RESERVA_CANCELAR, RESERVA_CREAR
from app.models.evaluacion import DiaConvocatoria, Evaluacion
from app.models.reserva_evaluacion import EstadoReserva, ReservaEvaluacion
from app.repositories.evaluacion_repository import (
    DiaConvocatoriaRepository,
    EvaluacionAlumnoRepository,
    EvaluacionRepository,
)
from app.repositories.reserva_repository import ReservaRepository
from app.schemas.evaluaciones import (
    ReservaAgendaResponse,
    ReservaListItem,
    ReservaResponse,
)
from app.services.audit_service import AuditService


class ReservaService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.reserva_repo = ReservaRepository(session, tenant_id)
        self.eval_repo = EvaluacionRepository(session, tenant_id)
        self.dia_repo = DiaConvocatoriaRepository(session, tenant_id)
        self.alumno_repo = EvaluacionAlumnoRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.audit = AuditService(session)

    async def reservar_turno(
        self,
        evaluacion_id: UUID,
        dia_convocatoria_id: UUID,
        alumno_id: UUID,
        actor_id: UUID,
    ) -> ReservaResponse:
        # Validate evaluacion exists and is active
        ev = await self.eval_repo.get(evaluacion_id)
        if not ev:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )
        if not ev.activa:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La convocatoria no está activa",
            )

        # Validate alumno is convocado
        es_convocado = await self.alumno_repo.alumno_esta_convocado(evaluacion_id, alumno_id)
        if not es_convocado:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El alumno no está convocado a esta evaluación",
            )

        # Validate no duplicate active reservation
        existing = await self.reserva_repo.get_activa_by_alumno_y_evaluacion(evaluacion_id, alumno_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El alumno ya tiene una reserva activa en esta convocatoria",
            )

        # FOR UPDATE on DiaConvocatoria
        dia = await self.dia_repo.get_by_id_with_lock(dia_convocatoria_id)
        if not dia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Día de convocatoria no encontrado",
            )

        if dia.evaluacion_id != evaluacion_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El día no pertenece a esta convocatoria",
            )

        if dia.cupos_ocupados >= dia.cupo_maximo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Sin cupo disponible",
            )

        dia.cupos_ocupados += 1

        reserva = await self.reserva_repo.create(
            evaluacion_id=evaluacion_id,
            dia_convocatoria_id=dia_convocatoria_id,
            alumno_id=alumno_id,
            estado=EstadoReserva.ACTIVA,
        )

        await self.session.flush()

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=RESERVA_CREAR,
            detalle={
                "reserva_id": str(reserva.id),
                "evaluacion_id": str(evaluacion_id),
                "dia_convocatoria_id": str(dia_convocatoria_id),
            },
        )

        await self.session.refresh(reserva)
        return ReservaResponse.model_validate(reserva)

    async def cancelar_reserva(
        self,
        reserva_id: UUID,
        alumno_id: UUID,
        actor_id: UUID,
    ) -> dict:
        reserva = await self.reserva_repo.get(reserva_id)
        if not reserva:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada",
            )

        if reserva.alumno_id != alumno_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes cancelar una reserva que no te pertenece",
            )

        if reserva.estado == EstadoReserva.CANCELADA:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La reserva ya está cancelada",
            )

        reserva.estado = EstadoReserva.CANCELADA

        dia = await self.dia_repo.get_by_id_with_lock(reserva.dia_convocatoria_id)
        if dia and dia.cupos_ocupados > 0:
            dia.cupos_ocupados -= 1

        await self.session.flush()

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=RESERVA_CANCELAR,
            detalle={
                "reserva_id": str(reserva_id),
                "evaluacion_id": str(reserva.evaluacion_id),
            },
        )

        return {"message": "Reserva cancelada exitosamente"}

    async def listar_agenda(
        self,
        evaluacion_id: UUID | None = None,
        materia_id: UUID | None = None,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        estado: str | None = None,
        alumno_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ReservaAgendaResponse:
        from datetime import date

        fecha_desde_date = date.fromisoformat(fecha_desde) if fecha_desde else None
        fecha_hasta_date = date.fromisoformat(fecha_hasta) if fecha_hasta else None

        items, total = await self.reserva_repo.list_with_filters(
            evaluacion_id=evaluacion_id,
            materia_id=materia_id,
            fecha_desde=fecha_desde_date,
            fecha_hasta=fecha_hasta_date,
            estado=estado,
            alumno_id=alumno_id,
            offset=offset,
            limit=limit,
        )

        result_items = []
        for item in items:
            r = item["reserva"]
            result_items.append(ReservaListItem(
                id=r.id,
                evaluacion_id=r.evaluacion_id,
                dia_convocatoria_id=r.dia_convocatoria_id,
                alumno_id=r.alumno_id,
                fecha_hora=r.fecha_hora,
                estado=r.estado.value if hasattr(r.estado, "value") else str(r.estado),
                alumno_nombre=item.get("alumno_nombre", ""),
                alumno_apellido=item.get("alumno_apellido", ""),
                evaluacion_instancia=item.get("evaluacion_instancia", ""),
                materia_nombre=item.get("materia_nombre", ""),
            ))

        return ReservaAgendaResponse(items=result_items, total=total)

    async def mis_reservas(
        self,
        alumno_id: UUID,
    ) -> ReservaAgendaResponse:
        items, total = await self.reserva_repo.list_with_filters(
            alumno_id=alumno_id,
            offset=0,
            limit=200,
        )

        result_items = []
        for item in items:
            r = item["reserva"]
            result_items.append(ReservaListItem(
                id=r.id,
                evaluacion_id=r.evaluacion_id,
                dia_convocatoria_id=r.dia_convocatoria_id,
                alumno_id=r.alumno_id,
                fecha_hora=r.fecha_hora,
                estado=r.estado.value if hasattr(r.estado, "value") else str(r.estado),
                alumno_nombre=item.get("alumno_nombre", ""),
                alumno_apellido=item.get("alumno_apellido", ""),
                evaluacion_instancia=item.get("evaluacion_instancia", ""),
                materia_nombre=item.get("materia_nombre", ""),
            ))

        return ReservaAgendaResponse(items=result_items, total=total)
