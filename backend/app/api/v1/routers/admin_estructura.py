from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.estructura import (
    CarreraCreate,
    CarreraList,
    CarreraResponse,
    CarreraUpdate,
    CohorteCreate,
    CohorteList,
    CohorteResponse,
    CohorteUpdate,
    DictadoCreate,
    DictadoList,
    DictadoResponse,
    DictadoUpdate,
    MateriaCreate,
    MateriaList,
    MateriaResponse,
    MateriaUpdate,
)
from app.schemas.padron import VaciarMateriaResponse
from app.services.estructura_service import (
    CarreraService,
    CohorteService,
    DictadoService,
    MateriaService,
)
from app.services.padron_service import PadronService

carreras_router = APIRouter(prefix="/api/v1/admin/carreras", tags=["Estructura - Carreras"])
cohortes_router = APIRouter(prefix="/api/v1/admin/cohortes", tags=["Estructura - Cohortes"])
materias_router = APIRouter(prefix="/api/v1/admin/materias", tags=["Estructura - Materias"])
dictados_router = APIRouter(prefix="/api/v1/admin/dictados", tags=["Estructura - Dictados"])


@carreras_router.post("/", response_model=CarreraResponse, status_code=201)
async def create_carrera(
    data: CarreraCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CarreraService(db, current_user.tenant_id)
    return await svc.create(codigo=data.codigo, nombre=data.nombre)


@carreras_router.get("/", response_model=list[CarreraResponse])
async def list_carreras(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CarreraService(db, current_user.tenant_id)
    return await svc.list(offset=offset, limit=limit)


@carreras_router.get("/{id}", response_model=CarreraResponse)
async def get_carrera(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CarreraService(db, current_user.tenant_id)
    return await svc.get(id)


@carreras_router.put("/{id}", response_model=CarreraResponse)
async def update_carrera(
    id: UUID,
    data: CarreraUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CarreraService(db, current_user.tenant_id)
    kwargs = {k: v for k, v in data.model_dump().items() if v is not None}
    return await svc.update(id, **kwargs)


@carreras_router.delete("/{id}", status_code=204)
async def delete_carrera(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CarreraService(db, current_user.tenant_id)
    await svc.delete(id)


@cohortes_router.post("/", response_model=CohorteResponse, status_code=201)
async def create_cohorte(
    data: CohorteCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CohorteService(db, current_user.tenant_id)
    return await svc.create(
        carrera_id=data.carrera_id,
        nombre=data.nombre,
        anio=data.anio,
        vig_desde=data.vig_desde,
        vig_hasta=data.vig_hasta,
    )


@cohortes_router.get("/", response_model=list[CohorteResponse])
async def list_cohortes(
    carrera_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CohorteService(db, current_user.tenant_id)
    return await svc.list(carrera_id=carrera_id, offset=offset, limit=limit)


@cohortes_router.get("/{id}", response_model=CohorteResponse)
async def get_cohorte(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CohorteService(db, current_user.tenant_id)
    return await svc.get(id)


@cohortes_router.put("/{id}", response_model=CohorteResponse)
async def update_cohorte(
    id: UUID,
    data: CohorteUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CohorteService(db, current_user.tenant_id)
    kwargs = {k: v for k, v in data.model_dump().items() if v is not None}
    return await svc.update(id, **kwargs)


@cohortes_router.delete("/{id}", status_code=204)
async def delete_cohorte(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = CohorteService(db, current_user.tenant_id)
    await svc.delete(id)


@materias_router.post("/", response_model=MateriaResponse, status_code=201)
async def create_materia(
    data: MateriaCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = MateriaService(db, current_user.tenant_id)
    return await svc.create(codigo=data.codigo, nombre=data.nombre)


@materias_router.get("/", response_model=list[MateriaResponse])
async def list_materias(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = MateriaService(db, current_user.tenant_id)
    return await svc.list(offset=offset, limit=limit)


@materias_router.get("/{id}", response_model=MateriaResponse)
async def get_materia(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = MateriaService(db, current_user.tenant_id)
    return await svc.get(id)


@materias_router.put("/{id}", response_model=MateriaResponse)
async def update_materia(
    id: UUID,
    data: MateriaUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = MateriaService(db, current_user.tenant_id)
    kwargs = {k: v for k, v in data.model_dump().items() if v is not None}
    return await svc.update(id, **kwargs)


@materias_router.delete("/{id}", status_code=204)
async def delete_materia(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = MateriaService(db, current_user.tenant_id)
    await svc.delete(id)


@materias_router.delete("/{id}/vaciar", response_model=VaciarMateriaResponse, status_code=200)
async def vaciar_materia(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("padron:vaciar")),
    db: AsyncSession = Depends(get_db),
):
    svc = PadronService(db, current_user.tenant_id)
    result = await svc.vaciar_materia(id, current_user.id)
    return VaciarMateriaResponse(
        materia_id=result["materia_id"],
        versiones_afectadas=result["versiones_afectadas"],
    )


@dictados_router.post("/", response_model=DictadoResponse, status_code=201)
async def create_dictado(
    data: DictadoCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = DictadoService(db, current_user.tenant_id)
    return await svc.create(
        materia_id=data.materia_id,
        carrera_id=data.carrera_id,
        cohorte_id=data.cohorte_id,
        nombre=data.nombre,
    )


@dictados_router.get("/", response_model=list[DictadoResponse])
async def list_dictados(
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = DictadoService(db, current_user.tenant_id)
    return await svc.list(materia_id=materia_id, cohorte_id=cohorte_id, offset=offset, limit=limit)


@dictados_router.get("/{id}", response_model=DictadoResponse)
async def get_dictado(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = DictadoService(db, current_user.tenant_id)
    return await svc.get(id)


@dictados_router.put("/{id}", response_model=DictadoResponse)
async def update_dictado(
    id: UUID,
    data: DictadoUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = DictadoService(db, current_user.tenant_id)
    kwargs = {k: v for k, v in data.model_dump().items() if v is not None}
    return await svc.update(id, **kwargs)


@dictados_router.delete("/{id}", status_code=204)
async def delete_dictado(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = DictadoService(db, current_user.tenant_id)
    await svc.delete(id)
