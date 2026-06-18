from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion
from app.repositories.base import TenantScopedRepository


class CalificacionRepository(TenantScopedRepository[Calificacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Calificacion, session, tenant_id)

    async def bulk_create_calificaciones(self, entries: list[dict]) -> list[Calificacion]:
        objs = []
        for entry in entries:
            obj = Calificacion(tenant_id=self.tenant_id, **entry)
            self.session.add(obj)
            objs.append(obj)
        await self.session.flush()
        for obj in objs:
            await self.session.refresh(obj)
        return objs

    async def list_by_materia(self, materia_id: UUID) -> list[Calificacion]:
        stmt = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_asignacion(
        self, materia_id: UUID, entrada_padron_ids: list[UUID]
    ) -> list[Calificacion]:
        stmt = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.entrada_padron_id.in_(entrada_padron_ids),
                Calificacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_sin_calificar(
        self, materia_id: UUID, entrada_padron_ids: list[UUID], actividades_textuales: list[str]
    ) -> list[dict]:
        """Find entries that have no calificacion record for the given textual activities."""
        from app.models.entrada_padron import EntradaPadron

        stmt = (
            select(EntradaPadron.id, EntradaPadron.nombre, EntradaPadron.apellidos)
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.id.in_(entrada_padron_ids),
                EntradaPadron.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        alumnos = {row.id: f"{row.nombre} {row.apellidos}" for row in result.all()}

        # Find existing calificaciones for these alumnos and textual activities
        existing_stmt = (
            select(Calificacion.entrada_padron_id, Calificacion.actividad)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.entrada_padron_id.in_(entrada_padron_ids),
                Calificacion.actividad.in_(actividades_textuales),
                Calificacion.is_deleted == False,
            )
        )
        existing_result = await self.session.execute(existing_stmt)
        existing = set()
        for row in existing_result.all():
            existing.add((row.entrada_padron_id, row.actividad))

        # Return entries that don't have calificaciones
        sin_calificar = []
        for entrada_id, alumno_nombre in alumnos.items():
            for actividad in actividades_textuales:
                if (entrada_id, actividad) not in existing:
                    sin_calificar.append({
                        "alumno_nombre": alumno_nombre,
                        "actividad": actividad,
                    })

        return sin_calificar

    async def recalcular_aprobados(
        self, asignacion_id: UUID, umbral_pct: int, valores_aprobatorios: list[str] | None
    ) -> int:
        """Recalculate aprobado for all calificaciones of a given asignacion's materia."""
        from app.models.asignacion import Asignacion

        # Get materia_id from asignacion
        asig_stmt = (
            select(Asignacion.materia_id)
            .where(
                Asignacion.id == asignacion_id,
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.is_deleted == False,
            )
        )
        result = await self.session.execute(asig_stmt)
        row = result.one_or_none()
        if row is None:
            return 0

        materia_id = row.materia_id

        # Get all calificaciones for this materia
        stmt = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        calificaciones = list(result.scalars().all())

        if not calificaciones:
            return 0

        valores_set = set(v.lower() for v in (valores_aprobatorios or ["Satisfactorio", "Supera lo esperado"]))

        for cal in calificaciones:
            if cal.nota_numerica is not None:
                cal.aprobado = cal.nota_numerica >= umbral_pct
            elif cal.nota_textual is not None:
                cal.aprobado = cal.nota_textual.lower() in valores_set
            else:
                cal.aprobado = False

        now = datetime.now(timezone.utc)
        for cal in calificaciones:
            cal.updated_at = now

        await self.session.flush()
        return len(calificaciones)

    async def get_actividades_by_materia(self, materia_id: UUID) -> list[str]:
        """Get distinct actividad names for a materia."""
        stmt = (
            select(Calificacion.actividad)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.is_deleted == False,
            )
            .distinct()
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_calificaciones_with_alumno(self, materia_id: UUID) -> list[dict]:
        """Get calificaciones joined with EntradaPadron data."""
        from app.models.entrada_padron import EntradaPadron

        stmt = (
            select(
                Calificacion,
                EntradaPadron.nombre,
                EntradaPadron.apellidos,
                EntradaPadron.email,
                EntradaPadron.comision,
                EntradaPadron.regional,
            )
            .join(
                EntradaPadron,
                Calificacion.entrada_padron_id == EntradaPadron.id,
            )
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.is_deleted == False,
                EntradaPadron.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        rows = []
        for row in result.all():
            cal = row[0]
            rows.append({
                "entrada_padron_id": cal.entrada_padron_id,
                "materia_id": cal.materia_id,
                "actividad": cal.actividad,
                "nota_numerica": cal.nota_numerica,
                "nota_textual": cal.nota_textual,
                "aprobado": cal.aprobado,
                "alumno_nombre": f"{row.nombre} {row.apellidos}",
                "email": row.email,
                "comision": row.comision,
                "regional": row.regional,
            })
        return rows

    async def get_aggregated_by_materia(self, materia_id: UUID) -> dict:
        """Get aggregated metrics (count, avg, min, max) for numeric notas."""
        from sqlalchemy import func

        stmt = (
            select(
                func.count(Calificacion.id).label("count"),
                func.avg(Calificacion.nota_numerica).label("avg"),
                func.min(Calificacion.nota_numerica).label("min"),
                func.max(Calificacion.nota_numerica).label("max"),
            )
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        row = result.one()
        return {
            "count": row.count or 0,
            "avg": float(row.avg) if row.avg is not None else None,
            "min": float(row.min) if row.min is not None else None,
            "max": float(row.max) if row.max is not None else None,
        }

    async def count_aprobados_desaprobados(self, materia_id: UUID) -> tuple[int, int]:
        """Count aprobados and desaprobados for a materia."""
        from sqlalchemy import func

        stmt = (
            select(Calificacion.aprobado, func.count(Calificacion.id))
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.is_deleted == False,
            )
            .group_by(Calificacion.aprobado)
        )
        result = await self.session.execute(stmt)
        aprobados = 0
        desaprobados = 0
        for row in result.all():
            if row.aprobado:
                aprobados = row[1]
            else:
                desaprobados = row[1]
        return aprobados, desaprobados

    async def get_all_calificaciones_with_alumno(self) -> list[dict]:
        """Get ALL calificaciones joined with EntradaPadron data (no materia filter)."""
        from app.models.entrada_padron import EntradaPadron

        stmt = (
            select(
                Calificacion,
                EntradaPadron.nombre,
                EntradaPadron.apellidos,
                EntradaPadron.email,
                EntradaPadron.comision,
                EntradaPadron.regional,
            )
            .join(
                EntradaPadron,
                Calificacion.entrada_padron_id == EntradaPadron.id,
            )
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.is_deleted == False,
                EntradaPadron.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        rows = []
        for row in result.all():
            cal = row[0]
            rows.append({
                "entrada_padron_id": cal.entrada_padron_id,
                "materia_id": cal.materia_id,
                "actividad": cal.actividad,
                "nota_numerica": cal.nota_numerica,
                "nota_textual": cal.nota_textual,
                "aprobado": cal.aprobado,
                "alumno_nombre": f"{row.nombre} {row.apellidos}",
                "email": row.email,
                "comision": row.comision,
                "regional": row.regional,
            })
        return rows

    async def get_alumnos_en_padron(self, materia_id: UUID) -> list:
        """Get EntradaPadron entries for alumnos in the materia's active padron version."""
        from app.models.entrada_padron import EntradaPadron
        from app.models.version_padron import VersionPadron

        stmt = (
            select(EntradaPadron)
            .join(
                VersionPadron,
                EntradaPadron.version_id == VersionPadron.id,
            )
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.activa == True,
                VersionPadron.is_deleted == False,
                EntradaPadron.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
