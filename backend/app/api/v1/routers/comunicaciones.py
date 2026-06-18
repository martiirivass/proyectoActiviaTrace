from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.comunicaciones import (
    AprobarLoteRequest,
    AprobarLoteResponse,
    ComunicacionDetalle,
    ComunicacionIndividualRequest,
    ComunicacionIndividualResponse,
    ComunicacionListResponse,
    ComunicacionMasivaRequest,
    ComunicacionMasivaResponse,
    ComunicacionPreviewRequest,
    ComunicacionPreviewResponse,
    DistribucionEstados,
    LoteDetalle,
    LotePendienteItem,
    RechazarLoteResponse,
)
from app.services.comunicacion_service import ComunicacionService

router = APIRouter(prefix="/api/v1/comunicaciones", tags=["Comunicaciones"])


@router.post("/preview", response_model=ComunicacionPreviewResponse)
async def preview_comunicacion(
    data: ComunicacionPreviewRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id)
    return await svc.preview(
        asunto=data.asunto,
        cuerpo=data.cuerpo,
        materia_id=data.materia_id,
        destinatarios=data.destinatarios,
    )


@router.post("/individual", response_model=ComunicacionIndividualResponse, status_code=201)
async def enviar_individual(
    data: ComunicacionIndividualRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id)
    return await svc.enviar_individual(
        asunto=data.asunto,
        cuerpo=data.cuerpo,
        materia_id=data.materia_id,
        destinatario_email=data.destinatario_email,
        actor_id=current_user.id,
    )


@router.post("/masivo", response_model=ComunicacionMasivaResponse, status_code=201)
async def enviar_masivo(
    data: ComunicacionMasivaRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id)
    return await svc.enviar_masivo(
        asunto=data.asunto,
        cuerpo=data.cuerpo,
        materia_id=data.materia_id,
        destinatarios=data.destinatarios,
        actor_id=current_user.id,
    )


@router.get("/lotes/pendientes", response_model=list[LotePendienteItem])
async def listar_lotes_pendientes(
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:aprobar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id)
    return await svc.listar_lotes_pendientes()


@router.post("/lotes/{lote_id}/aprobar", response_model=AprobarLoteResponse)
async def aprobar_lote(
    lote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:aprobar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id)
    return await svc.aprobar_lote(
        lote_id=lote_id,
        aprobado_por=current_user.id,
    )


@router.post("/lotes/{lote_id}/rechazar", response_model=RechazarLoteResponse)
async def rechazar_lote(
    lote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:aprobar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id)
    return await svc.rechazar_lote(lote_id=lote_id, actor_id=current_user.id)


@router.get("/lotes/{lote_id}", response_model=LoteDetalle)
async def detalle_lote(
    lote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id)
    return await svc.obtener_detalle_lote(lote_id=lote_id)


@router.get("", response_model=ComunicacionListResponse)
async def listar_comunicaciones(
    materia_id: UUID = Query(...),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id)
    return await svc.listar_por_materia(
        materia_id=materia_id,
        offset=offset,
        limit=limit,
    )


@router.get("/distribucion", response_model=DistribucionEstados)
async def distribucion_estados(
    materia_id: UUID = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id)
    return await svc.obtener_distribucion(materia_id=materia_id)


@router.get("/{comunicacion_id}", response_model=ComunicacionDetalle)
async def detalle_comunicacion(
    comunicacion_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id)
    return await svc.obtener_comunicacion(comunicacion_id=comunicacion_id)
