import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.audit import AuditLogResponse
from app.schemas.auth import CurrentUser
from app.services.audit_service import AuditService

router = APIRouter(tags=["audit"])


@router.get("/log", response_model=list[AuditLogResponse])
async def get_audit_log(
    accion: str | None = Query(None),
    actor_id: str | None = Query(None),
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: None = Depends(require_permission("auditoria:ver")),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AuditService(db)
    actor_uuid = uuid.UUID(actor_id) if actor_id else None
    desde_dt = datetime.fromisoformat(desde) if desde else None
    hasta_dt = datetime.fromisoformat(hasta) if hasta else None
    logs = await svc.get_log(
        tenant_id=current_user.tenant_id,
        accion=accion,
        actor_id=actor_uuid,
        desde=desde_dt,
        hasta=hasta_dt,
        offset=offset,
        limit=limit,
    )
    return logs
