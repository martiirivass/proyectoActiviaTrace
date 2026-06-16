import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.audit import AuditLogResponse, DashboardResponse
from app.schemas.auth import CurrentUser
from app.services.audit_service import AuditService

router = APIRouter(tags=["audit"])


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    if value is None:
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid UUID format: {value}",
        )


@router.get("/log", response_model=list[AuditLogResponse])
async def get_audit_log(
    accion: str | None = Query(None),
    actor_id: str | None = Query(None),
    materia_id: str | None = Query(None),
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: None = Depends(require_permission("auditoria:ver")),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AuditService(db)
    actor_uuid = _parse_uuid(actor_id)
    materia_uuid = _parse_uuid(materia_id)
    desde_dt = _parse_iso_datetime(desde)
    hasta_dt = _parse_iso_datetime(hasta)
    logs = await svc.get_log(
        tenant_id=current_user.tenant_id,
        accion=accion,
        actor_id=actor_uuid,
        materia_id=materia_uuid,
        desde=desde_dt,
        hasta=hasta_dt,
        offset=offset,
        limit=limit,
        current_user=current_user,
    )
    return logs


@router.get("/dashboard", response_model=DashboardResponse)
async def get_audit_dashboard(
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    materia_id: str | None = Query(None),
    limit: int = Query(200, ge=1, le=200),
    _: None = Depends(require_permission("auditoria:ver")),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AuditService(db)
    desde_dt = _parse_iso_datetime(desde)
    hasta_dt = _parse_iso_datetime(hasta)
    materia_uuid = _parse_uuid(materia_id)
    dashboard = await svc.get_dashboard(
        tenant_id=current_user.tenant_id,
        current_user=current_user,
        materia_id=materia_uuid,
        desde=desde_dt,
        hasta=hasta_dt,
        limit=limit,
    )
    return dashboard
