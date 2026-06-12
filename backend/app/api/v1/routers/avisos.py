from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.avisos import (
    AcknowledgmentResponse,
    AvisoCreate,
    AvisoDetailResponse,
    AvisoListResponse,
    AvisoResponse,
    AvisoUpdate,
    MetricasAvisoResponse,
)
from app.services.aviso_service import AvisoService

router = APIRouter(prefix="/api/v1/avisos", tags=["Avisos"])


@router.post("/", status_code=201, response_model=AvisoResponse)
async def crear_aviso(
    data: AvisoCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:publicar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AvisoService(db, current_user.tenant_id)
    return await svc.crear_aviso(data=data, actor_id=current_user.id)


@router.get("/", response_model=AvisoListResponse)
async def listar_avisos_visibles(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AvisoService(db, current_user.tenant_id)
    if "COORDINADOR" in current_user.roles or "ADMIN" in current_user.roles:
        return await svc.listar_avisos(offset=offset, limit=limit)
    return await svc.listar_avisos_visibles(
        usuario_id=current_user.id,
        roles=current_user.roles,
        offset=offset,
        limit=limit,
    )


@router.get("/{id}", response_model=AvisoDetailResponse)
async def obtener_detalle_aviso(
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:publicar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AvisoService(db, current_user.tenant_id)
    return await svc.obtener_detalle(aviso_id=id)


@router.patch("/{id}", response_model=AvisoResponse)
async def editar_aviso(
    data: AvisoUpdate,
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:publicar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AvisoService(db, current_user.tenant_id)
    return await svc.editar_aviso(aviso_id=id, data=data, actor_id=current_user.id)


@router.delete("/{id}", status_code=204)
async def eliminar_aviso(
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:publicar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AvisoService(db, current_user.tenant_id)
    await svc.eliminar_aviso(aviso_id=id, actor_id=current_user.id)


@router.post("/{id}/acknowledge", status_code=201, response_model=AcknowledgmentResponse)
async def acknowledge_aviso(
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AvisoService(db, current_user.tenant_id)
    return await svc.acknowledge_aviso(
        aviso_id=id,
        usuario_id=current_user.id,
        actor_id=current_user.id,
    )


@router.get("/{id}/metricas", response_model=MetricasAvisoResponse)
async def obtener_metricas_aviso(
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:publicar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AvisoService(db, current_user.tenant_id)
    return await svc.obtener_metricas(aviso_id=id)
