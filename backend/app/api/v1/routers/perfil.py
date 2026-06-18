from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.schemas.auth import CurrentUser
from app.schemas.usuarios import PerfilResponse, PerfilUpdate
from app.services.usuario_service import UsuarioService

perfil_router = APIRouter(prefix="/api/v1/perfil", tags=["Perfil"])


@perfil_router.get("/", response_model=PerfilResponse)
async def leer_perfil(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = UsuarioService(db, current_user.tenant_id)
    user = await svc.get(current_user.id)
    return user


@perfil_router.put("/", response_model=PerfilResponse)
async def actualizar_perfil(
    data: PerfilUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = UsuarioService(db, current_user.tenant_id)
    user = await svc.update_own_profile(current_user.id, data)
    return user
