from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.tareas import (
    ComentarioCreate,
    ComentarioResponse,
    TareaCreate,
    TareaListResponse,
    TareaResponse,
    TareaUpdate,
)
from app.services.tarea_service import TareaService

router = APIRouter(prefix="/api/v1/tareas", tags=["Tareas"])


@router.get("/", response_model=TareaListResponse)
async def listar_tareas(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    estado: str | None = Query(None),
    asignado_a: UUID | None = Query(None),
    asignado_por: UUID | None = Query(None),
    materia_id: UUID | None = Query(None),
    q: str | None = Query(None, max_length=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    """List tareas. Admin sees all; others see only their own tareas."""
    svc = TareaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.list_tareas(
        offset=offset,
        limit=limit,
        estado=estado,
        asignado_a=asignado_a,
        asignado_por=asignado_por,
        materia_id=materia_id,
        q=q,
    )


@router.post("/", response_model=TareaResponse, status_code=201)
async def crear_tarea(
    data: TareaCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("tareas:admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tarea (requires tareas:admin)."""
    svc = TareaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.create_tarea(data)


@router.get("/{tarea_id}", response_model=TareaResponse)
async def obtener_tarea(
    tarea_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    """Get tarea detail. Admin sees any; others see only own."""
    svc = TareaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.get_tarea(tarea_id)


@router.put("/{tarea_id}", response_model=TareaResponse)
async def actualizar_tarea(
    tarea_id: UUID,
    data: TareaUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    """Update tarea (estado, reassign, descripcion). Admin can update any. Own updates only for gestionar."""
    svc = TareaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.update_tarea(tarea_id, data)


@router.delete("/{tarea_id}", status_code=204)
async def eliminar_tarea(
    tarea_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("tareas:admin")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a tarea (requires tareas:admin)."""
    svc = TareaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    await svc.delete_tarea(tarea_id)


@router.post("/{tarea_id}/comentarios", response_model=ComentarioResponse, status_code=201)
async def agregar_comentario(
    tarea_id: UUID,
    data: ComentarioCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    """Add a comment to a tarea (user must have access to the tarea)."""
    svc = TareaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.add_comentario(tarea_id, data)


@router.get("/{tarea_id}/comentarios", response_model=list[ComentarioResponse])
async def listar_comentarios(
    tarea_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    """List comments for a tarea (user must have access to the tarea)."""
    svc = TareaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.list_comentarios(tarea_id)
