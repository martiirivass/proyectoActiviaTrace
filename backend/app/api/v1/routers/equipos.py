import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import ASIGNACION_MODIFICAR
from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.asignaciones import (
    AsignacionConDictadoResponse,
    AsignacionMasivaRequest,
    AsignacionResponse,
    ClonarEquipoRequest,
    DictadoInfoResponse,
    VigenciaUpdateRequest,
    VigenciaUpdateResponse,
)
from app.schemas.auth import CurrentUser
from app.services.asignacion_service import AsignacionService, compute_estado_vigencia
from app.services.audit_service import AuditService

equipos_router = APIRouter(prefix="/api/v1/equipos", tags=["Equipos"])


def _enrich_with_dictado(asignacion, dictado_info: dict | None = None) -> dict:
    """Build an AsignacionConDictadoResponse dict with estado_vigencia and optional dictado info."""
    data = AsignacionConDictadoResponse.model_validate(asignacion).model_dump()
    data["estado_vigencia"] = compute_estado_vigencia(asignacion)
    if dictado_info:
        data["dictado"] = DictadoInfoResponse(**dictado_info).model_dump()
    return data


def _simple_response(asignacion) -> dict:
    data = AsignacionResponse.model_validate(asignacion).model_dump()
    data["estado_vigencia"] = compute_estado_vigencia(asignacion)
    return data


@equipos_router.get("/mis-equipos")
async def mis_equipos(
    estado: str | None = Query(None),
    rol: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve las asignaciones del usuario autenticado. No requiere permiso especial."""
    svc = AsignacionService(db, current_user.tenant_id)
    asignaciones = await svc.mis_equipos(
        usuario_id=current_user.id,
        estado=estado,
        rol=rol,
    )
    result = []
    for a in asignaciones:
        dictado_info = None
        if a.dictado_id:
            dictado_info = await svc.get_dictado_info(a.dictado_id)
        result.append(_enrich_with_dictado(a, dictado_info))
    return result


@equipos_router.get("/asignaciones")
async def list_asignaciones_equipos(
    dictado_id: UUID | None = Query(None),
    carrera_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    rol: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AsignacionService(db, current_user.tenant_id)
    asignaciones = await svc.list(
        dictado_id=dictado_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        rol=rol,
        offset=offset,
        limit=limit,
    )
    result = []
    for a in asignaciones:
        dictado_info = None
        if a.dictado_id:
            dictado_info = await svc.get_dictado_info(a.dictado_id)
        result.append(_enrich_with_dictado(a, dictado_info))
    return result


@equipos_router.post("/masiva", status_code=201)
async def asignacion_masiva(
    data: AsignacionMasivaRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AsignacionService(db, current_user.tenant_id)
    asignaciones = await svc.asignar_masivo(
        dictado_id=data.dictado_id,
        rol=data.rol,
        desde=data.desde,
        hasta=data.hasta,
        usuario_ids=data.usuario_ids,
    )

    # Audit
    audit_svc = AuditService(db)
    await audit_svc.log(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        accion=ASIGNACION_MODIFICAR,
        detalle={
            "operacion": "asignacion_masiva",
            "dictado_id": str(data.dictado_id),
            "rol": data.rol,
            "cantidad": len(asignaciones),
        },
        filas_afectadas=len(asignaciones),
    )

    return [_simple_response(a) for a in asignaciones]


@equipos_router.post("/clonar", status_code=201)
async def clonar_equipo(
    data: ClonarEquipoRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AsignacionService(db, current_user.tenant_id)
    asignaciones = await svc.clonar_equipo(
        dictado_origen_id=data.dictado_origen_id,
        dictado_destino_id=data.dictado_destino_id,
        force=data.force,
    )

    # Audit
    audit_svc = AuditService(db)
    await audit_svc.log(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        accion=ASIGNACION_MODIFICAR,
        detalle={
            "operacion": "clonar_equipo",
            "dictado_origen_id": str(data.dictado_origen_id),
            "dictado_destino_id": str(data.dictado_destino_id),
            "cantidad": len(asignaciones),
        },
        filas_afectadas=len(asignaciones),
    )

    return [_simple_response(a) for a in asignaciones]


@equipos_router.put("/{dictado_id}/vigencia")
async def modificar_vigencia(
    dictado_id: UUID,
    data: VigenciaUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AsignacionService(db, current_user.tenant_id)
    actualizadas = await svc.modificar_vigencia_general(
        dictado_id=dictado_id,
        desde=data.desde,
        hasta=data.hasta,
    )

    # Audit
    audit_svc = AuditService(db)
    await audit_svc.log(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        accion=ASIGNACION_MODIFICAR,
        detalle={
            "operacion": "modificar_vigencia",
            "dictado_id": str(dictado_id),
            "desde": str(data.desde),
            "hasta": str(data.hasta) if data.hasta else None,
            "actualizadas": actualizadas,
        },
        filas_afectadas=actualizadas,
    )

    return VigenciaUpdateResponse(actualizadas=actualizadas)


@equipos_router.get("/{dictado_id}/exportar")
async def exportar_equipo(
    dictado_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi.responses import StreamingResponse

    svc = AsignacionService(db, current_user.tenant_id)
    rows = await svc.exportar_equipo(dictado_id)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "docente_id", "rol", "materia_id", "carrera_id", "cohorte_id",
        "desde", "hasta", "estado_vigencia",
    ])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=equipo_{dictado_id}.csv"},
    )
