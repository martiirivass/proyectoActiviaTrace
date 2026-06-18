from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.calificaciones import (
    CalificacionConfirmRequest,
    CalificacionConfirmResponse,
    CalificacionPreviewResponse,
    ReporteFinalizacionResponse,
    UmbralMateriaRequest,
    UmbralMateriaResponse,
)
from app.services.calificacion_service import CalificacionService
from app.services.reporte_finalizacion_service import ReporteFinalizacionService

router = APIRouter(prefix="/api/v1/calificaciones", tags=["Calificaciones"])


@router.post("/preview", response_model=CalificacionPreviewResponse)
async def preview_calificaciones(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CalificacionService(db, current_user.tenant_id)
    return await svc.preview_import(file)


@router.post("/confirm", response_model=CalificacionConfirmResponse, status_code=201)
async def confirm_calificaciones(
    data: CalificacionConfirmRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CalificacionService(db, current_user.tenant_id)
    return await svc.confirm_import(
        materia_id=data.materia_id,
        cohorte_id=data.cohorte_id,
        actividades_seleccionadas=data.actividades_seleccionadas,
        entries=data.entries,
        actor_id=current_user.id,
    )


@router.post("/reporte-finalizacion", response_model=ReporteFinalizacionResponse)
async def procesar_reporte_finalizacion(
    file: UploadFile = File(...),
    materia_id: UUID = Form(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ReporteFinalizacionService(db, current_user.tenant_id)
    return await svc.procesar_reporte(file, materia_id)


@router.get("/umbral")
async def get_umbral(
    materia_id: UUID | None = Query(None),
    asignacion_id: UUID | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    from app.models import Asignacion, Materia, Dictado
    from sqlalchemy import select, and_

    if asignacion_id:
        resolved = asignacion_id
    elif materia_id:
        # Resolve the first active ASIGNACION for this user + materia
        stmt = (
            select(Asignacion.id)
            .join(Dictado, Asignacion.dictado_id == Dictado.id)
            .where(
                and_(
                    Asignacion.tenant_id == current_user.tenant_id,
                    Asignacion.usuario_id == current_user.id,
                    Asignacion.rol.in_(["PROFESOR", "COORDINADOR", "ADMIN"]),
                    Materia.id == materia_id,
                    Asignacion.is_deleted == False,
                )
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="No se encontró una asignación activa para esta materia")
        resolved = row
    else:
        raise HTTPException(status_code=422, detail="Debe proporcionar materia_id o asignacion_id")

    svc = CalificacionService(db, current_user.tenant_id)
    return await svc.get_umbral(resolved)


@router.put("/umbral", response_model=UmbralMateriaResponse)
async def configurar_umbral(
    data: UmbralMateriaRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    from app.models import Asignacion
    from sqlalchemy import select, and_

    # Resolve asignacion_id from materia_id if not provided
    asignacion_id = data.asignacion_id
    if not asignacion_id:
        stmt = select(Asignacion.id).where(
            and_(
                Asignacion.tenant_id == current_user.tenant_id,
                Asignacion.usuario_id == current_user.id,
                Asignacion.materia_id == data.materia_id,
                Asignacion.is_deleted == False,
            )
        ).limit(1)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="No se encontró una asignación activa para esta materia")
        asignacion_id = row

    svc = CalificacionService(db, current_user.tenant_id)
    return await svc.configurar_umbral(
        asignacion_id=asignacion_id,
        materia_id=data.materia_id,
        umbral_pct=data.umbral_pct,
        valores_aprobatorios=data.valores_aprobatorios,
        actor_id=current_user.id,
    )


@router.post("/umbral/recalcular")
async def recalcular_aprobados(
    materia_id: UUID | None = Query(None),
    asignacion_id: UUID | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    from app.models import Asignacion
    from sqlalchemy import select, and_

    if asignacion_id:
        resolved = asignacion_id
    elif materia_id:
        stmt = select(Asignacion.id).where(
            and_(
                Asignacion.tenant_id == current_user.tenant_id,
                Asignacion.usuario_id == current_user.id,
                Asignacion.materia_id == materia_id,
                Asignacion.is_deleted == False,
            )
        ).limit(1)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="No se encontró una asignación activa para esta materia")
        resolved = row
    else:
        raise HTTPException(status_code=422, detail="Debe proporcionar materia_id o asignacion_id")

    svc = CalificacionService(db, current_user.tenant_id)
    return await svc.recalcular_aprobados(resolved)
