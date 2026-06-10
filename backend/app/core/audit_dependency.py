from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.schemas.auth import CurrentUser
from app.services.audit_service import AuditService


def audit_dependency(action_code: str):
    async def _log(
        request: Request,
        current_user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        ip = _client_ip(request)
        user_agent = request.headers.get("user-agent")
        svc = AuditService(db)
        await svc.log(
            tenant_id=current_user.tenant_id,
            actor_id=current_user.id,
            accion=action_code,
            ip=ip,
            user_agent=user_agent,
        )
    return _log


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"
