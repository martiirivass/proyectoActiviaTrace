from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import DiaConvocatoria, Evaluacion, EvaluacionAlumnoConvocado
from app.models.reserva_evaluacion import EstadoReserva, ReservaEvaluacion
from app.repositories.base import TenantScopedRepository


class EvaluacionRepository(TenantScopedRepository[Evaluacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Evaluacion, session, tenant_id)

    async def list_with_metrics(
        self,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        activa: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        base_where = [
            Evaluacion.tenant_id == self.tenant_id,
            Evaluacion.is_deleted == False,
        ]
        if materia_id:
            base_where.append(Evaluacion.materia_id == materia_id)
        if cohorte_id:
            base_where.append(Evaluacion.cohorte_id == cohorte_id)
        if activa is not None:
            base_where.append(Evaluacion.activa == activa)

        count_q = select(func.count(Evaluacion.id)).where(*base_where)
        count_result = await self.session.execute(count_q)
        total = count_result.scalar() or 0

        data_q = (
            select(Evaluacion)
            .where(*base_where)
            .order_by(Evaluacion.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        data_result = await self.session.execute(data_q)
        items_raw = list(data_result.scalars().all())

        items = []
        for ev in items_raw:
            total_convocados_q = select(func.count(EvaluacionAlumnoConvocado.id)).where(
                EvaluacionAlumnoConvocado.evaluacion_id == ev.id,
                EvaluacionAlumnoConvocado.is_deleted == False,
            )
            total_convocados = (await self.session.execute(total_convocados_q)).scalar() or 0

            reservas_activas_q = select(func.count(ReservaEvaluacion.id)).where(
                ReservaEvaluacion.evaluacion_id == ev.id,
                ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
                ReservaEvaluacion.is_deleted == False,
            )
            reservas_activas = (await self.session.execute(reservas_activas_q)).scalar() or 0

            cupos_totales_q = select(func.coalesce(func.sum(DiaConvocatoria.cupo_maximo), 0)).where(
                DiaConvocatoria.evaluacion_id == ev.id,
                DiaConvocatoria.is_deleted == False,
            )
            cupos_ocupados_q = select(func.coalesce(func.sum(DiaConvocatoria.cupos_ocupados), 0)).where(
                DiaConvocatoria.evaluacion_id == ev.id,
                DiaConvocatoria.is_deleted == False,
            )
            cupos_totales = (await self.session.execute(cupos_totales_q)).scalar() or 0
            cupos_ocupados = (await self.session.execute(cupos_ocupados_q)).scalar() or 0
            cupos_libres = cupos_totales - cupos_ocupados

            items.append({
                "evaluacion": ev,
                "total_convocados": total_convocados,
                "reservas_activas": reservas_activas,
                "cupos_libres": cupos_libres,
            })

        return items, total

    async def get_detail(self, id: UUID) -> dict | None:
        ev = await self.get(id)
        if not ev:
            return None

        dias_q = select(DiaConvocatoria).where(
            DiaConvocatoria.evaluacion_id == ev.id,
            DiaConvocatoria.is_deleted == False,
        ).order_by(DiaConvocatoria.fecha.asc())
        dias_result = await self.session.execute(dias_q)
        dias = list(dias_result.scalars().all())

        convocados_q = select(EvaluacionAlumnoConvocado).where(
            EvaluacionAlumnoConvocado.evaluacion_id == ev.id,
            EvaluacionAlumnoConvocado.is_deleted == False,
        )
        convocados_result = await self.session.execute(convocados_q)
        convocados = list(convocados_result.scalars().all())

        total_convocados = len(convocados)
        reservas_activas_q = select(func.count(ReservaEvaluacion.id)).where(
            ReservaEvaluacion.evaluacion_id == ev.id,
            ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
            ReservaEvaluacion.is_deleted == False,
        )
        reservas_activas = (await self.session.execute(reservas_activas_q)).scalar() or 0

        cupos_totales_q = select(func.coalesce(func.sum(DiaConvocatoria.cupo_maximo), 0)).where(
            DiaConvocatoria.evaluacion_id == ev.id,
            DiaConvocatoria.is_deleted == False,
        )
        cupos_ocupados_q = select(func.coalesce(func.sum(DiaConvocatoria.cupos_ocupados), 0)).where(
            DiaConvocatoria.evaluacion_id == ev.id,
            DiaConvocatoria.is_deleted == False,
        )
        cupos_totales = (await self.session.execute(cupos_totales_q)).scalar() or 0
        cupos_ocupados = (await self.session.execute(cupos_ocupados_q)).scalar() or 0
        cupos_libres = cupos_totales - cupos_ocupados

        return {
            "evaluacion": ev,
            "dias": dias,
            "convocados": convocados,
            "total_convocados": total_convocados,
            "reservas_activas": reservas_activas,
            "cupos_libres": cupos_libres,
        }


class DiaConvocatoriaRepository(TenantScopedRepository[DiaConvocatoria]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(DiaConvocatoria, session, tenant_id)

    async def get_by_id_with_lock(self, id: UUID) -> DiaConvocatoria | None:
        stmt = (
            select(DiaConvocatoria)
            .where(
                DiaConvocatoria.id == id,
                DiaConvocatoria.tenant_id == self.tenant_id,
                DiaConvocatoria.is_deleted == False,
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_create(self, entries: list[dict]) -> list[DiaConvocatoria]:
        objs = []
        for entry in entries:
            obj = DiaConvocatoria(tenant_id=self.tenant_id, **entry)
            self.session.add(obj)
            objs.append(obj)
        await self.session.flush()
        for obj in objs:
            await self.session.refresh(obj)
        return objs

    async def get_by_evaluacion(self, evaluacion_id: UUID) -> list[DiaConvocatoria]:
        stmt = (
            select(DiaConvocatoria)
            .where(
                DiaConvocatoria.evaluacion_id == evaluacion_id,
                DiaConvocatoria.is_deleted == False,
            )
            .order_by(DiaConvocatoria.fecha.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class EvaluacionAlumnoRepository(TenantScopedRepository[EvaluacionAlumnoConvocado]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(EvaluacionAlumnoConvocado, session, tenant_id)

    async def reemplazar_convocados(self, evaluacion_id: UUID, alumno_ids: list[UUID]) -> list[EvaluacionAlumnoConvocado]:
        await self.session.execute(
            EvaluacionAlumnoConvocado.__table__.update()
            .where(
                EvaluacionAlumnoConvocado.evaluacion_id == evaluacion_id,
                EvaluacionAlumnoConvocado.is_deleted == False,
            )
            .values(is_deleted=True)
        )

        objs = []
        for alumno_id in alumno_ids:
            obj = EvaluacionAlumnoConvocado(
                tenant_id=self.tenant_id,
                evaluacion_id=evaluacion_id,
                alumno_id=alumno_id,
            )
            self.session.add(obj)
            objs.append(obj)
        await self.session.flush()
        for obj in objs:
            await self.session.refresh(obj)
        return objs

    async def list_by_evaluacion(self, evaluacion_id: UUID) -> list[EvaluacionAlumnoConvocado]:
        stmt = (
            select(EvaluacionAlumnoConvocado)
            .where(
                EvaluacionAlumnoConvocado.evaluacion_id == evaluacion_id,
                EvaluacionAlumnoConvocado.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def alumno_esta_convocado(self, evaluacion_id: UUID, alumno_id: UUID) -> bool:
        stmt = select(EvaluacionAlumnoConvocado).where(
            EvaluacionAlumnoConvocado.evaluacion_id == evaluacion_id,
            EvaluacionAlumnoConvocado.alumno_id == alumno_id,
            EvaluacionAlumnoConvocado.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
