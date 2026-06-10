from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_session_factory

settings = get_settings()
from app.core.rate_limiter import RateLimiter
from app.core.security import verify_token
from app.models import Tenant, User
from app.schemas.auth import CurrentUser
from app.services.permission_service import PermissionService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = verify_token(token, "access")
    if payload is None:
        from jose import jwt as jose_jwt
        try:
            jose_jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        except jose_jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    from uuid import UUID
    user_id = UUID(payload["sub"])
    stmt = select(User).where(User.id == user_id)
    rows = await db.execute(stmt)
    user = rows.scalar_one_or_none()
    if user is None or user.is_deleted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or deleted")
    return CurrentUser(
        id=user.id,
        email=user.email,
        tenant_id=UUID(payload["tenant_id"]),
        roles=payload.get("roles", []),
    )


def require_permission(codename: str):
    async def _check_permission(
        current_user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        svc = PermissionService(db)
        permissions = await svc.get_effective_permissions(current_user.id)
        if codename not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {codename}",
            )
    return _check_permission


async def get_tenant(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    stmt = select(Tenant).where(Tenant.id == current_user.tenant_id)
    rows = await db.execute(stmt)
    tenant = rows.scalar_one_or_none()
    if tenant is None or tenant.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(max_attempts=5, window_seconds=60)
    return _rate_limiter


async def reset_rate_limiter() -> None:
    global _rate_limiter
    _rate_limiter = None