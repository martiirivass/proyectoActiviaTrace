from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.fecha_academica import TipoFecha
from app.schemas.auth import CurrentUser
from app.schemas.fechas_academicas import (
    FechaAcademicaCreate,
    FechaAcademicaResponse,
    FechaAcademicaUpdate,
    FechasExportLMSResponse,
)
from app.services.fecha_academica_service import FechaAcademicaService

fechas_router = APIRouter(prefix="/api/v1/fechas-academicas", tags=["Fechas Académicas"])


def _to_dict(response: FechaAcademicaResponse) -> dict:
    """Serialize Pydantic response model to JSON-safe dict."""
    return response.model_dump(mode="json")


@fechas_router.get("")
async def list_fechas(
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    tipo: TipoFecha | None = Query(None),
    periodo: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = FechaAcademicaService(db, current_user.tenant_id)
    items = await svc.list(materia_id=materia_id, cohorte_id=cohorte_id, tipo=tipo, periodo=periodo)
    return [_to_dict(FechaAcademicaResponse.model_validate(item)) for item in items]


@fechas_router.post("", status_code=201)
async def create_fecha(
    data: FechaAcademicaCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = FechaAcademicaService(db, current_user.tenant_id)
    result = await svc.create(
        materia_id=data.materia_id,
        cohorte_id=data.cohorte_id,
        tipo=data.tipo,
        numero=data.numero,
        periodo=data.periodo,
        fecha=data.fecha,
        titulo=data.titulo,
        actor_id=current_user.id,
    )
    return _to_dict(FechaAcademicaResponse.model_validate(result))


@fechas_router.get("/exportar-lms", response_model=FechasExportLMSResponse)
async def exportar_lms(
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    periodo: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = FechaAcademicaService(db, current_user.tenant_id)
    contenido = await svc.exportar_lms(materia_id=materia_id, cohorte_id=cohorte_id, periodo=periodo)
    return FechasExportLMSResponse(contenido=contenido)


@fechas_router.get("/{id}")
async def get_fecha(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = FechaAcademicaService(db, current_user.tenant_id)
    result = await svc.get(id)
    return _to_dict(FechaAcademicaResponse.model_validate(result))


@fechas_router.put("/{id}")
async def update_fecha(
    id: UUID,
    data: FechaAcademicaUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = FechaAcademicaService(db, current_user.tenant_id)
    result = await svc.update(
        id=id,
        tipo=data.tipo,
        numero=data.numero,
        periodo=data.periodo,
        fecha=data.fecha,
        titulo=data.titulo,
        actor_id=current_user.id,
    )
    return _to_dict(FechaAcademicaResponse.model_validate(result))


@fechas_router.delete("/{id}", status_code=204)
async def delete_fecha(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = FechaAcademicaService(db, current_user.tenant_id)
    await svc.delete(id, actor_id=current_user.id)
