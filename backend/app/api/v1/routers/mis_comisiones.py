from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.asignacion import Asignacion
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.schemas.auth import CurrentUser
from app.schemas.comisiones import ComisionResponse

router = APIRouter(prefix="/api/v1/materias", tags=["Mis Comisiones"])


DOCENTE_ROLES = {"PROFESOR", "COORDINADOR", "ADMIN", "NEXO"}


@router.get("/mis-comisiones", response_model=list[ComisionResponse])
async def mis_comisiones(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna las comisiones (materia + cohorte) asignadas al usuario actual
    en roles docentes, con la cantidad de alumnos inscriptos en cada una.
    """
    # Subconsulta: materias-cohortes donde el usuario tiene rol docente
    subquery = (
        select(
            Asignacion.materia_id,
            Asignacion.cohorte_id,
        )
        .where(
            Asignacion.tenant_id == current_user.tenant_id,
            Asignacion.usuario_id == current_user.id,
            Asignacion.rol.in_(DOCENTE_ROLES),
            Asignacion.is_deleted == False,
            Asignacion.materia_id.isnot(None),
            Asignacion.cohorte_id.isnot(None),
        )
        .distinct()
        .subquery()
    )

    # Consulta principal: datos de la comisión + conteo de alumnos
    # Subconsulta para contar alumnos por (materia_id, cohorte_id)
    alumnos_count = (
        select(
            Asignacion.materia_id,
            Asignacion.cohorte_id,
            func.count(Asignacion.id).label("alumnos_count"),
        )
        .where(
            Asignacion.rol == "ALUMNO",
            Asignacion.is_deleted == False,
            Asignacion.tenant_id == current_user.tenant_id,
        )
        .group_by(Asignacion.materia_id, Asignacion.cohorte_id)
        .subquery()
    )

    query = (
        select(
            subquery.c.materia_id,
            subquery.c.cohorte_id,
            Materia.nombre.label("materia_nombre"),
            Cohorte.nombre.label("cohorte_nombre"),
            func.coalesce(alumnos_count.c.alumnos_count, 0).label("alumnos_count"),
        )
        .join(Materia, subquery.c.materia_id == Materia.id)
        .join(Cohorte, subquery.c.cohorte_id == Cohorte.id)
        .outerjoin(
            alumnos_count,
            (subquery.c.materia_id == alumnos_count.c.materia_id)
            & (subquery.c.cohorte_id == alumnos_count.c.cohorte_id),
        )
        .where(Materia.is_deleted == False, Cohorte.is_deleted == False)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        ComisionResponse(
            materia_id=row.materia_id,
            cohorte_id=row.cohorte_id,
            materia_nombre=row.materia_nombre,
            cohorte_nombre=row.cohorte_nombre,
            alumnos_count=row.alumnos_count,
        )
        for row in rows
    ]
