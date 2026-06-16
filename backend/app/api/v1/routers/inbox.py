from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.schemas.auth import CurrentUser
from app.schemas.mensajes import (
    HiloResponse,
    MensajeCreateRequest,
    MensajeResponderRequest,
    MensajeResponse,
)
from app.services.mensaje_service import MensajeService

inbox_router = APIRouter(prefix="/api/v1/inbox", tags=["Inbox"])


@inbox_router.get("/", response_model=list[HiloResponse])
async def listar_inbox(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MensajeService(db, current_user.tenant_id)
    return await svc.get_inbox(current_user.id, offset=offset, limit=limit)


@inbox_router.get("/{hilo_id}", response_model=list[MensajeResponse])
async def leer_hilo(
    hilo_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MensajeService(db, current_user.tenant_id)
    return await svc.get_hilo(hilo_id, current_user.id)


@inbox_router.post("/", response_model=MensajeResponse, status_code=201)
async def enviar_mensaje(
    data: MensajeCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MensajeService(db, current_user.tenant_id)
    return await svc.send_message(
        remitente_id=current_user.id,
        destinatario_id=data.destinatario_id,
        asunto=data.asunto,
        cuerpo=data.cuerpo,
    )


@inbox_router.post("/{hilo_id}/responder", response_model=MensajeResponse, status_code=201)
async def responder_hilo(
    hilo_id: UUID,
    data: MensajeResponderRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MensajeService(db, current_user.tenant_id)
    return await svc.respond_to_hilo(
        hilo_id=hilo_id,
        remitente_id=current_user.id,
        cuerpo=data.cuerpo,
    )
