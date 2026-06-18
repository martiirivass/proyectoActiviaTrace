from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.guardias import GuardiaCreate, GuardiaListResponse, GuardiaResponse, GuardiaUpdate
from app.services.guardia_service import GuardiaService

router = APIRouter(prefix="/api/v1/guardias", tags=["Guardias"])


@router.post("/", response_model=GuardiaResponse, status_code=201)
async def registrar_guardia(
    data: GuardiaCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = GuardiaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.registrar_guardia(
        data=data,
        actor_id=current_user.id,
    )


@router.patch("/{guardia_id}", response_model=GuardiaResponse)
async def actualizar_estado_guardia(
    guardia_id: UUID,
    data: GuardiaUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = GuardiaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.actualizar_estado_guardia(
        guardia_id=guardia_id,
        data=data,
    )


@router.get("/", response_model=GuardiaListResponse)
async def listar_guardias(
    materia_id: UUID | None = Query(None),
    carrera_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    dia: str | None = Query(None),
    estado: str | None = Query(None),
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = GuardiaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.listar_guardias(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        dia=dia,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        offset=offset,
        limit=limit,
    )


@router.get("/exportar")
async def exportar_guardias_csv(
    materia_id: UUID | None = Query(None),
    carrera_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    dia: str | None = Query(None),
    estado: str | None = Query(None),
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = GuardiaService(db, current_user.tenant_id, current_user.id, current_user.roles)
    return await svc.exportar_csv(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        dia=dia,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
