from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.asignaciones import (
    AsignacionCreate,
    AsignacionResponse,
    AsignacionUpdate,
)
from app.schemas.auth import CurrentUser
from app.services.asignacion_service import AsignacionService, compute_estado_vigencia

asignaciones_router = APIRouter(prefix="/api/v1/admin/asignaciones", tags=["Asignaciones"])


def _enrich_with_vigencia(asignacion) -> dict:
    data = AsignacionResponse.model_validate(asignacion).model_dump()
    data["estado_vigencia"] = compute_estado_vigencia(asignacion)
    return data


@asignaciones_router.post("/", status_code=201)
async def create_asignacion(
    data: AsignacionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AsignacionService(db, current_user.tenant_id)
    asignacion = await svc.create(data)
    return _enrich_with_vigencia(asignacion)


@asignaciones_router.get("/")
async def list_asignaciones(
    usuario_id: UUID | None = Query(None),
    materia_id: UUID | None = Query(None),
    rol: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AsignacionService(db, current_user.tenant_id)
    asignaciones = await svc.list(
        usuario_id=usuario_id,
        materia_id=materia_id,
        rol=rol,
        offset=offset,
        limit=limit,
    )
    return [_enrich_with_vigencia(a) for a in asignaciones]


@asignaciones_router.get("/{id}")
async def get_asignacion(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AsignacionService(db, current_user.tenant_id)
    asignacion = await svc.get(id)
    return _enrich_with_vigencia(asignacion)


@asignaciones_router.put("/{id}")
async def update_asignacion(
    id: UUID,
    data: AsignacionUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AsignacionService(db, current_user.tenant_id)
    asignacion = await svc.update(id, data)
    return _enrich_with_vigencia(asignacion)


@asignaciones_router.delete("/{id}", status_code=204)
async def delete_asignacion(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    svc = AsignacionService(db, current_user.tenant_id)
    await svc.delete(id)
