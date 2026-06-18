from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
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
    asignacion_id: UUID = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CalificacionService(db, current_user.tenant_id)
    return await svc.get_umbral(asignacion_id)


@router.put("/umbral", response_model=UmbralMateriaResponse)
async def configurar_umbral(
    data: UmbralMateriaRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CalificacionService(db, current_user.tenant_id)
    return await svc.configurar_umbral(
        asignacion_id=data.asignacion_id,
        materia_id=data.materia_id,
        umbral_pct=data.umbral_pct,
        valores_aprobatorios=data.valores_aprobatorios,
        actor_id=current_user.id,
    )


@router.post("/umbral/recalcular")
async def recalcular_aprobados(
    asignacion_id: UUID = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CalificacionService(db, current_user.tenant_id)
    return await svc.recalcular_aprobados(asignacion_id)
