from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.avisos import (
    AckResponse,
    AckUserListResponse,
    AvisoCreate,
    AvisoListResponse,
    AvisoResponse,
    AvisoStatsResponse,
    AvisoUpdate,
)
from app.services.aviso_service import AvisoService

router = APIRouter(prefix="/api/v1/avisos", tags=["Avisos"])


@router.get("/", response_model=AvisoListResponse)
async def listar_avisos(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:ver")),
    db: AsyncSession = Depends(get_db),
):
    """List active avisos visible for the current user."""
    svc = AvisoService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.listar_avisos_activos(offset=offset, limit=limit)


@router.get("/{aviso_id}", response_model=AvisoResponse)
async def obtener_aviso(
    aviso_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:ver")),
    db: AsyncSession = Depends(get_db),
):
    """Get detail of an aviso if visible for the current user."""
    svc = AvisoService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.obtener_detalle(aviso_id)


@router.post("/", response_model=AvisoResponse, status_code=201)
async def crear_aviso(
    data: AvisoCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:publicar")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new aviso (requires avisos:publicar)."""
    svc = AvisoService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.crear_aviso(data=data, actor_id=current_user.id)


@router.put("/{aviso_id}", response_model=AvisoResponse)
async def editar_aviso(
    aviso_id: UUID,
    data: AvisoUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:publicar")),
    db: AsyncSession = Depends(get_db),
):
    """Edit an existing aviso (requires avisos:publicar)."""
    svc = AvisoService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.editar_aviso(aviso_id=aviso_id, data=data, actor_id=current_user.id)


@router.delete("/{aviso_id}", status_code=204)
async def eliminar_aviso(
    aviso_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:publicar")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an aviso (requires avisos:publicar)."""
    svc = AvisoService(db, current_user.tenant_id, current_user.id, current_user.roles)
    await svc.eliminar_aviso(aviso_id=aviso_id, actor_id=current_user.id)


@router.post("/{aviso_id}/ack", response_model=AckResponse)
async def confirmar_lectura(
    aviso_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:ver")),
    db: AsyncSession = Depends(get_db),
):
    """Confirm reading of an aviso (idempotent)."""
    svc = AvisoService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.confirmar_lectura(aviso_id=aviso_id, actor_id=current_user.id)


@router.get("/{aviso_id}/stats", response_model=AvisoStatsResponse)
async def obtener_stats(
    aviso_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:publicar")),
    db: AsyncSession = Depends(get_db),
):
    """Get acknowledgment stats for an aviso (requires avisos:publicar)."""
    svc = AvisoService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.obtener_stats(aviso_id=aviso_id)


@router.get("/{aviso_id}/acks", response_model=AckUserListResponse)
async def listar_acks(
    aviso_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("avisos:publicar")),
    db: AsyncSession = Depends(get_db),
):
    """List users who confirmed reading an aviso (requires avisos:publicar)."""
    svc = AvisoService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.listar_acks(aviso_id=aviso_id, offset=offset, limit=limit)
