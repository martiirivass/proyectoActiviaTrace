from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, get_rate_limiter
from app.core.rate_limiter import RateLimiter
from app.schemas.auth import (
    CurrentUser,
    ForgotRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    ResetRequest,
    TwoFADisableRequest,
    TwoFAEnrolResponse,
    TwoFAVerifyRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post("/login", response_model=LoginResponse, response_model_exclude_none=True)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
):
    ip = _client_ip(request)
    if not rate_limiter.is_allowed(ip, body.email):
        retry_after = rate_limiter.get_retry_after(ip, body.email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
    svc = AuthService(db)
    result = await svc.authenticate(body.email, body.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if result.get("requires_2fa"):
        return LoginResponse(
            requires_2fa=True,
            two_fa_token=result["2fa_token"],
        )
    session = await svc.create_session(result["user_id"], result["tenant_id"])
    return LoginResponse(
        access_token=session["access_token"],
        refresh_token=session["refresh_token"],
        token_type=session["token_type"],
        expires_in=session["expires_in"],
        requires_2fa=False,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    result = await svc.refresh_session(body.refresh_token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )
    return RefreshResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    await svc.revoke_session(body.refresh_token)
    return None


@router.post("/2fa/enrol", response_model=TwoFAEnrolResponse)
async def enrol_2fa(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models import User
    stmt = select(User).where(User.id == current_user.id)
    rows = await db.execute(stmt)
    user = rows.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    svc = AuthService(db)
    try:
        result = await svc.enrol_2fa(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return TwoFAEnrolResponse(
        secret=result["secret"],
        uri=result["uri"],
        qr_code=result["qr_code"],
    )


@router.post("/2fa/verify", response_model=LoginResponse)
async def verify_2fa(
    body: TwoFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import verify_token
    payload = verify_token(body.two_fa_token, "2fa")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification session expired, please log in again",
        )
    from uuid import UUID
    user_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tenant_id"])
    svc = AuthService(db)
    valid = await svc.verify_2fa(user_id, body.totp_code)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code",
        )
    session = await svc.create_session(user_id, tenant_id)
    return LoginResponse(
        access_token=session["access_token"],
        refresh_token=session["refresh_token"],
        token_type=session["token_type"],
        expires_in=session["expires_in"],
    )


@router.post("/2fa/disable")
async def disable_2fa(
    body: TwoFADisableRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models import User
    stmt = select(User).where(User.id == current_user.id)
    rows = await db.execute(stmt)
    user = rows.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    svc = AuthService(db)
    try:
        await svc.disable_2fa(user, body.password)
    except ValueError as e:
        if "Invalid password" in str(e):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"message": "2FA disabled successfully"}


@router.post("/forgot")
async def forgot(
    body: ForgotRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    token = await svc.create_recovery_token(body.email)
    if token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    return {"token": token}


@router.post("/reset")
async def reset(
    body: ResetRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    success = await svc.reset_password(body.token, body.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    return {"message": "Password reset successfully"}


@router.get("/me")
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
):
    return {"id": str(current_user.id), "email": current_user.email, "roles": current_user.roles}
