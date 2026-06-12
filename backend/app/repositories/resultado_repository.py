from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion, EvaluacionAlumnoConvocado
from app.models.materia import Materia
from app.models.resultado_evaluacion import EstadoResultado, ResultadoEvaluacion
from app.models.user import User
from app.repositories.base import TenantScopedRepository


class ResultadoRepository(TenantScopedRepository[ResultadoEvaluacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(ResultadoEvaluacion, session, tenant_id)

    async def list_with_filters(
        self,
        evaluacion_id: UUID | None = None,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        base_where = [
            ResultadoEvaluacion.tenant_id == self.tenant_id,
            ResultadoEvaluacion.is_deleted == False,
        ]
        if evaluacion_id:
            base_where.append(ResultadoEvaluacion.evaluacion_id == evaluacion_id)
        if estado:
            base_where.append(ResultadoEvaluacion.estado == estado)

        join_evaluacion = materia_id is not None or cohorte_id is not None

        count_q = select(func.count(ResultadoEvaluacion.id)).where(*base_where)
        if join_evaluacion:
            count_q = count_q.join(Evaluacion, ResultadoEvaluacion.evaluacion_id == Evaluacion.id)
            if materia_id:
                count_q = count_q.where(Evaluacion.materia_id == materia_id)
            if cohorte_id:
                count_q = count_q.where(Evaluacion.cohorte_id == cohorte_id)
        count_result = await self.session.execute(count_q)
        total = count_result.scalar() or 0

        data_q = (
            select(
                ResultadoEvaluacion,
                User.nombre.label("alumno_nombre"),
                User.apellido.label("alumno_apellido"),
                Evaluacion.instancia.label("evaluacion_instancia"),
                Materia.nombre.label("materia_nombre"),
            )
            .join(User, ResultadoEvaluacion.alumno_id == User.id)
            .join(Evaluacion, ResultadoEvaluacion.evaluacion_id == Evaluacion.id)
            .join(Materia, Evaluacion.materia_id == Materia.id)
            .where(*base_where)
            .order_by(ResultadoEvaluacion.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if join_evaluacion:
            if materia_id:
                data_q = data_q.where(Evaluacion.materia_id == materia_id)
            if cohorte_id:
                data_q = data_q.where(Evaluacion.cohorte_id == cohorte_id)
        data_result = await self.session.execute(data_q)
        rows = data_result.all()

        items = []
        for row in rows:
            resultado = row[0]
            items.append({
                "resultado": resultado,
                "alumno_nombre": row.alumno_nombre,
                "alumno_apellido": row.alumno_apellido,
                "evaluacion_instancia": row.evaluacion_instancia,
                "materia_nombre": row.materia_nombre,
            })

        return items, total

    async def get_by_alumno_y_evaluacion(self, evaluacion_id: UUID, alumno_id: UUID) -> ResultadoEvaluacion | None:
        stmt = (
            select(ResultadoEvaluacion)
            .where(
                ResultadoEvaluacion.evaluacion_id == evaluacion_id,
                ResultadoEvaluacion.alumno_id == alumno_id,
                ResultadoEvaluacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_metricas(self) -> dict:
        total_alumnos_cargados_q = select(func.count(func.distinct(EvaluacionAlumnoConvocado.alumno_id))).where(
            EvaluacionAlumnoConvocado.tenant_id == self.tenant_id,
            EvaluacionAlumnoConvocado.is_deleted == False,
            EvaluacionAlumnoConvocado.evaluacion_id.in_(
                select(Evaluacion.id).where(
                    Evaluacion.tenant_id == self.tenant_id,
                    Evaluacion.activa == True,
                    Evaluacion.is_deleted == False,
                )
            ),
        )
        total_alumnos_cargados = (await self.session.execute(total_alumnos_cargados_q)).scalar() or 0

        instancias_activas_q = select(func.count(Evaluacion.id)).where(
            Evaluacion.tenant_id == self.tenant_id,
            Evaluacion.activa == True,
            Evaluacion.is_deleted == False,
        )
        instancias_activas = (await self.session.execute(instancias_activas_q)).scalar() or 0

        from app.models.reserva_evaluacion import EstadoReserva, ReservaEvaluacion
        reservas_activas_q = select(func.count(ReservaEvaluacion.id)).where(
            ReservaEvaluacion.tenant_id == self.tenant_id,
            ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
            ReservaEvaluacion.is_deleted == False,
        )
        reservas_activas = (await self.session.execute(reservas_activas_q)).scalar() or 0

        notas_registradas_q = select(func.count(ResultadoEvaluacion.id)).where(
            ResultadoEvaluacion.tenant_id == self.tenant_id,
            ResultadoEvaluacion.estado == EstadoResultado.DEFINITIVO,
            ResultadoEvaluacion.is_deleted == False,
        )
        notas_registradas = (await self.session.execute(notas_registradas_q)).scalar() or 0

        return {
            "total_alumnos_cargados": total_alumnos_cargados,
            "instancias_activas": instancias_activas,
            "reservas_activas": reservas_activas,
            "notas_registradas": notas_registradas,
        }
