"""Router for analisis endpoints (F2.2–F2.9)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.analisis import (
    AtrasadosResponse,
    NotasFinalesResponse,
    RankingResponse,
    ReporteRapidoResponse,
)
from app.schemas.auth import CurrentUser
from app.services.analisis_service import AnalisisService

router = APIRouter(prefix="/api/v1/analisis", tags=["Análisis"])


@router.get("/atrasados", response_model=AtrasadosResponse)
async def alumnos_atrasados(
    materia_id: UUID = Query(...),
    busqueda: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db),
):
    """F2.2: Get alumnos atrasados for a materia (RN-06)."""
    svc = AnalisisService(db, current_user.tenant_id)
    es_scope_global = any(r in ("COORDINADOR", "ADMIN") for r in current_user.roles)
    return await svc.get_atrasados(
        materia_id=materia_id,
        current_user_id=current_user.id,
        busqueda=busqueda,
        es_scope_global=es_scope_global,
    )


@router.get("/ranking", response_model=RankingResponse)
async def ranking_aprobadas(
    materia_id: UUID = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db),
):
    """F2.3: Ranking de actividades aprobadas (RN-09)."""
    svc = AnalisisService(db, current_user.tenant_id)
    return await svc.get_ranking(materia_id=materia_id)


@router.get("/reportes-rapidos", response_model=ReporteRapidoResponse)
async def reportes_rapidos(
    materia_id: UUID = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db),
):
    """F2.4: Reporte rápido con métricas consolidadas por materia."""
    svc = AnalisisService(db, current_user.tenant_id)
    return await svc.get_reportes_rapidos(materia_id=materia_id)


@router.get("/notas-finales", response_model=NotasFinalesResponse)
async def notas_finales(
    materia_id: UUID = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db),
):
    """F2.5: Notas finales promedio por alumno."""
    svc = AnalisisService(db, current_user.tenant_id)
    return await svc.get_notas_finales(materia_id=materia_id)


@router.get("/exportar-tps-sin-corregir")
async def exportar_tps_sin_corregir(
    materia_id: UUID = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db),
):
    """F2.6: Exportar TPs sin corregir como CSV (RN-07/RN-08)."""
    svc = AnalisisService(db, current_user.tenant_id)
    csv_content = await svc.exportar_tps_sin_corregir(materia_id=materia_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="tps_sin_corregir_{materia_id}.csv"',
        },
    )


@router.get("/monitor-general")
async def monitor_general(
    materia_id: UUID | None = Query(None),
    regional: str | None = Query(None),
    comision: str | None = Query(None),
    busqueda: str | None = Query(None),
    estado: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db),
):
    """F2.7: Monitor general para COORDINADOR/ADMIN."""
    svc = AnalisisService(db, current_user.tenant_id)
    return await svc.get_monitor_general(
        materia_id=materia_id,
        regional=regional,
        comision=comision,
        busqueda=busqueda,
        estado=estado,
        page=page,
        page_size=page_size,
    )


@router.get("/monitor-seguimiento")
async def monitor_seguimiento(
    alumno_id: UUID | None = Query(None),
    email: str | None = Query(None),
    comision: str | None = Query(None),
    regional: str | None = Query(None),
    actividad: str | None = Query(None),
    min_actividades: int | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db),
):
    """F2.8: Monitor de seguimiento para TUTOR/PROFESOR (scope propio)."""
    svc = AnalisisService(db, current_user.tenant_id)
    return await svc.get_monitor_seguimiento(
        current_user_id=current_user.id,
        alumno_id=alumno_id,
        email=email,
        comision=comision,
        regional=regional,
        actividad=actividad,
        min_actividades=min_actividades,
    )


@router.get("/monitor-seguimiento-extendido")
async def monitor_seguimiento_extendido(
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    alumno_id: UUID | None = Query(None),
    email: str | None = Query(None),
    comision: str | None = Query(None),
    regional: str | None = Query(None),
    actividad: str | None = Query(None),
    min_actividades: int | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db),
):
    """F2.9: Monitor de seguimiento extendido para COORDINADOR/ADMIN (scope global + fechas)."""
    svc = AnalisisService(db, current_user.tenant_id)
    return await svc.get_monitor_seguimiento_extendido(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        alumno_id=alumno_id,
        email=email,
        comision=comision,
        regional=regional,
        actividad=actividad,
        min_actividades=min_actividades,
    )
