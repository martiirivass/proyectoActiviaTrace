from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion
from app.models.materia import Materia
from app.models.reserva_evaluacion import EstadoReserva, ReservaEvaluacion
from app.models.user import User
from app.repositories.base import TenantScopedRepository


class ReservaRepository(TenantScopedRepository[ReservaEvaluacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(ReservaEvaluacion, session, tenant_id)

    async def list_with_filters(
        self,
        evaluacion_id: UUID | None = None,
        materia_id: UUID | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        estado: str | None = None,
        alumno_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        from sqlalchemy import join as sa_join

        base_where = [
            ReservaEvaluacion.tenant_id == self.tenant_id,
            ReservaEvaluacion.is_deleted == False,
        ]
        if evaluacion_id:
            base_where.append(ReservaEvaluacion.evaluacion_id == evaluacion_id)
        if estado:
            base_where.append(ReservaEvaluacion.estado == estado)
        if alumno_id:
            base_where.append(ReservaEvaluacion.alumno_id == alumno_id)
        if fecha_desde:
            base_where.append(ReservaEvaluacion.fecha_hora >= fecha_desde)
        if fecha_hasta:
            base_where.append(ReservaEvaluacion.fecha_hora <= fecha_hasta)

        join_evaluacion = materia_id is not None

        count_q = select(func.count(ReservaEvaluacion.id)).where(*base_where)
        if join_evaluacion:
            count_q = count_q.join(Evaluacion, ReservaEvaluacion.evaluacion_id == Evaluacion.id)
            count_q = count_q.where(Evaluacion.materia_id == materia_id)
        count_result = await self.session.execute(count_q)
        total = count_result.scalar() or 0

        data_q = (
            select(
                ReservaEvaluacion,
                User.nombre.label("alumno_nombre"),
                User.apellido.label("alumno_apellido"),
                Evaluacion.instancia.label("evaluacion_instancia"),
                Materia.nombre.label("materia_nombre"),
            )
            .join(User, ReservaEvaluacion.alumno_id == User.id)
            .join(Evaluacion, ReservaEvaluacion.evaluacion_id == Evaluacion.id)
            .join(Materia, Evaluacion.materia_id == Materia.id)
            .where(*base_where)
            .order_by(ReservaEvaluacion.fecha_hora.desc())
            .offset(offset)
            .limit(limit)
        )
        if join_evaluacion:
            data_q = data_q.where(Evaluacion.materia_id == materia_id)
        data_result = await self.session.execute(data_q)
        rows = data_result.all()

        items = []
        for row in rows:
            reserva = row[0]
            items.append({
                "reserva": reserva,
                "alumno_nombre": row.alumno_nombre,
                "alumno_apellido": row.alumno_apellido,
                "evaluacion_instancia": row.evaluacion_instancia,
                "materia_nombre": row.materia_nombre,
            })

        return items, total

    async def get_activa_by_alumno_y_evaluacion(self, evaluacion_id: UUID, alumno_id: UUID) -> ReservaEvaluacion | None:
        stmt = (
            select(ReservaEvaluacion)
            .where(
                ReservaEvaluacion.evaluacion_id == evaluacion_id,
                ReservaEvaluacion.alumno_id == alumno_id,
                ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
                ReservaEvaluacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_agenda_admin(
        self,
        evaluacion_id: UUID | None = None,
        materia_id: UUID | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        estado: str | None = None,
        alumno_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        return await self.list_with_filters(
            evaluacion_id=evaluacion_id,
            materia_id=materia_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            estado=estado,
            alumno_id=alumno_id,
            offset=offset,
            limit=limit,
        )
