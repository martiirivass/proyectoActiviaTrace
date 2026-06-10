from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.usuarios import UserCreate, UserList, UserResponse, UserUpdate
from app.services.usuario_service import UsuarioService

usuarios_router = APIRouter(prefix="/api/v1/admin/usuarios", tags=["Usuarios"])


@usuarios_router.post("/", response_model=UserResponse, status_code=201)
async def create_usuario(
    data: UserCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = UsuarioService(db, current_user.tenant_id)
    return await svc.create(data)


@usuarios_router.get("/", response_model=list[UserResponse])
async def list_usuarios(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = UsuarioService(db, current_user.tenant_id)
    return await svc.list(offset=offset, limit=limit)


@usuarios_router.get("/{id}", response_model=UserResponse)
async def get_usuario(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = UsuarioService(db, current_user.tenant_id)
    return await svc.get(id)


@usuarios_router.put("/{id}", response_model=UserResponse)
async def update_usuario(
    id: UUID,
    data: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = UsuarioService(db, current_user.tenant_id)
    return await svc.update(id, data)


@usuarios_router.delete("/{id}", status_code=204)
async def delete_usuario(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = UsuarioService(db, current_user.tenant_id)
    await svc.delete(id)
