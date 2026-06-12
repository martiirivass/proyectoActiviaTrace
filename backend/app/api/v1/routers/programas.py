from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.programas import ProgramaCreate, ProgramaResponse, ProgramaUpdate
from app.services.programa_service import ProgramaService

programas_router = APIRouter(prefix="/api/v1/programas", tags=["Programas"])


@programas_router.get("", response_model=list[ProgramaResponse])
async def list_programas(
    materia_id: UUID | None = Query(None),
    carrera_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ProgramaService(db, current_user.tenant_id)
    return await svc.list(materia_id=materia_id, carrera_id=carrera_id, cohorte_id=cohorte_id)


@programas_router.post("", response_model=ProgramaResponse, status_code=201)
async def create_programa(
    data: ProgramaCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ProgramaService(db, current_user.tenant_id)
    return await svc.create(
        materia_id=data.materia_id,
        carrera_id=data.carrera_id,
        cohorte_id=data.cohorte_id,
        titulo=data.titulo,
        referencia_archivo=data.referencia_archivo,
        actor_id=current_user.id,
    )


@programas_router.get("/{id}", response_model=ProgramaResponse)
async def get_programa(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ProgramaService(db, current_user.tenant_id)
    return await svc.get(id)


@programas_router.put("/{id}", response_model=ProgramaResponse)
async def update_programa(
    id: UUID,
    data: ProgramaUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ProgramaService(db, current_user.tenant_id)
    return await svc.update(
        id=id,
        titulo=data.titulo,
        referencia_archivo=data.referencia_archivo,
        actor_id=current_user.id,
    )


@programas_router.delete("/{id}", status_code=204)
async def delete_programa(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ProgramaService(db, current_user.tenant_id)
    await svc.delete(id, actor_id=current_user.id)
