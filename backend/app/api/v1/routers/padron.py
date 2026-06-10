from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.padron import (
    MoodleSyncRequest,
    MoodleSyncResponse,
    PadronConfirmRequest,
    PadronConfirmResponse,
    PadronPreviewResponse,
    VersionPadronListResponse,
    VaciarMateriaResponse,
)
from app.services.padron_service import PadronService

router = APIRouter(prefix="/api/v1/padron", tags=["Padrón"])


@router.post("/preview", response_model=PadronPreviewResponse)
async def preview_padron(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("padron:cargar")),
    db: AsyncSession = Depends(get_db),
):
    svc = PadronService(db, current_user.tenant_id)
    return await svc.preview_import(file)


@router.post("/confirm", response_model=PadronConfirmResponse, status_code=201)
async def confirm_padron(
    data: PadronConfirmRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("padron:cargar")),
    db: AsyncSession = Depends(get_db),
):
    svc = PadronService(db, current_user.tenant_id)
    entries_dicts = [e.model_dump() for e in data.entries]
    return await svc.confirm_import(
        materia_id=data.materia_id,
        cohorte_id=data.cohorte_id,
        entries=entries_dicts,
        actor_id=current_user.id,
    )


@router.get("/versions", response_model=VersionPadronListResponse)
async def list_versions(
    materia_id: UUID = Query(...),
    cohorte_id: UUID = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("padron:ver")),
    db: AsyncSession = Depends(get_db),
):
    svc = PadronService(db, current_user.tenant_id)
    return await svc.list_versions(materia_id, cohorte_id)


@router.post("/sync-moodle", response_model=MoodleSyncResponse, status_code=202)
async def sync_moodle(
    data: MoodleSyncRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("moodle:sync")),
    db: AsyncSession = Depends(get_db),
):
    svc = PadronService(db, current_user.tenant_id)
    result = await svc.sync_from_moodle(
        materia_id=data.materia_id,
        cohorte_id=data.cohorte_id,
        actor_id=current_user.id,
    )
    return MoodleSyncResponse(
        status="accepted",
        message="Sincronización completada",
        version_id=result.version_id,
    )
