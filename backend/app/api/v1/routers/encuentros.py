from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.encuentros import (
    EncuentroAdminListResponse,
    InstanciaListResponse,
    InstanciaResponse,
    InstanciaUpdate,
    SlotEncuentroCreate,
)
from app.services.encuentro_service import EncuentroService

router = APIRouter(prefix="/api/v1/encuentros", tags=["Encuentros"])


@router.post("/slots", status_code=201)
async def crear_slot(
    data: SlotEncuentroCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = EncuentroService(db, current_user.tenant_id)
    return await svc.crear_slot(
        data=data,
        actor_id=current_user.id,
    )


@router.get("/slots/{slot_id}/instancias", response_model=InstanciaListResponse)
async def listar_instancias_por_slot(
    slot_id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = EncuentroService(db, current_user.tenant_id)
    return await svc.listar_instancias_por_slot(slot_id=slot_id)


@router.patch("/instancias/{instancia_id}", response_model=InstanciaResponse)
async def editar_instancia(
    data: InstanciaUpdate,
    instancia_id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = EncuentroService(db, current_user.tenant_id)
    return await svc.editar_instancia(
        instancia_id=instancia_id,
        estado=data.estado,
        meet_url=data.meet_url,
        video_url=data.video_url,
        comentario=data.comentario,
        actor_id=current_user.id,
    )


@router.get("/admin", response_model=EncuentroAdminListResponse)
async def vista_admin_encuentros(
    materia_id: UUID | None = Query(None),
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    estado: str | None = Query(None),
    asignacion_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    # Solo COORDINADOR y ADMIN pueden acceder a vista admin
    if not any(r in current_user.roles for r in ("COORDINADOR", "ADMIN")):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo COORDINADOR o ADMIN pueden acceder a la vista admin",
        )

    svc = EncuentroService(db, current_user.tenant_id)
    return await svc.listar_admin(
        materia_id=materia_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        estado=estado,
        asignacion_id=asignacion_id,
        offset=offset,
        limit=limit,
    )


@router.get("/{materia_id}/exportar-html")
async def exportar_html_encuentros(
    materia_id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = EncuentroService(db, current_user.tenant_id)
    return await svc.exportar_html(materia_id=materia_id)
