import csv
import io
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardia import Guardia
from app.repositories.base import TenantScopedRepository


class GuardiaRepository(TenantScopedRepository[Guardia]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Guardia, session, tenant_id)

    async def list_with_filters(
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
    ) -> tuple[list[Guardia], int]:
        """List guardias with filters, return (items, total)."""
        base_where = [
            Guardia.tenant_id == self.tenant_id,
            Guardia.is_deleted == False,
        ]
        if materia_id:
            base_where.append(Guardia.materia_id == materia_id)
        if carrera_id:
            base_where.append(Guardia.carrera_id == carrera_id)
        if cohorte_id:
            base_where.append(Guardia.cohorte_id == cohorte_id)
        if dia:
            base_where.append(Guardia.dia == dia)
        if estado:
            base_where.append(Guardia.estado == estado)
        if fecha_desde:
            base_where.append(Guardia.creada_at >= fecha_desde)
        if fecha_hasta:
            base_where.append(Guardia.creada_at <= fecha_hasta)

        # Count
        count_q = select(func.count(Guardia.id)).where(*base_where)
        count_result = await self.session.execute(count_q)
        total = count_result.scalar() or 0

        # Data
        data_q = (
            select(Guardia)
            .where(*base_where)
            .order_by(Guardia.creada_at.desc())
            .offset(offset)
            .limit(limit)
        )
        data_result = await self.session.execute(data_q)
        items = list(data_result.scalars().all())
        return items, total

    async def export_csv(
        self,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        dia: str | None = None,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> str:
        """Export guardias to CSV string."""
        from app.models.asignacion import Asignacion
        from app.models.materia import Materia
        from app.models.carrera import Carrera
        from app.models.cohorte import Cohorte
        from app.models.user import User

        base_where = [
            Guardia.tenant_id == self.tenant_id,
            Guardia.is_deleted == False,
        ]
        if materia_id:
            base_where.append(Guardia.materia_id == materia_id)
        if carrera_id:
            base_where.append(Guardia.carrera_id == carrera_id)
        if cohorte_id:
            base_where.append(Guardia.cohorte_id == cohorte_id)
        if dia:
            base_where.append(Guardia.dia == dia)
        if estado:
            base_where.append(Guardia.estado == estado)
        if fecha_desde:
            base_where.append(Guardia.creada_at >= fecha_desde)
        if fecha_hasta:
            base_where.append(Guardia.creada_at <= fecha_hasta)

        stmt = (
            select(
                Guardia,
                Materia.nombre.label("materia_nombre"),
                Carrera.nombre.label("carrera_nombre"),
                Cohorte.nombre.label("cohorte_nombre"),
                User.nombre.label("user_nombre"),
                User.apellido.label("user_apellido"),
            )
            .join(Materia, Guardia.materia_id == Materia.id)
            .join(Carrera, Guardia.carrera_id == Carrera.id)
            .join(Cohorte, Guardia.cohorte_id == Cohorte.id)
            .join(Asignacion, Guardia.asignacion_id == Asignacion.id)
            .join(User, Asignacion.usuario_id == User.id)
            .where(*base_where)
            .order_by(Guardia.creada_at.desc())
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Materia", "Carrera", "Cohorte", "Día", "Horario", "Tutor", "Estado", "Comentarios", "Creada"])
        for row in rows:
            g = row[0]
            writer.writerow([
                row.materia_nombre,
                row.carrera_nombre,
                row.cohorte_nombre,
                g.dia.value if hasattr(g.dia, "value") else str(g.dia),
                g.horario,
                f"{row.user_nombre} {row.user_apellido}",
                g.estado.value if hasattr(g.estado, "value") else str(g.estado),
                g.comentarios or "",
                g.creada_at.strftime("%Y-%m-%d %H:%M") if g.creada_at else "",
            ])
        return output.getvalue()
