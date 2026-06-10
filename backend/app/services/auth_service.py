import base64
import io
import uuid
from datetime import datetime, timedelta, timezone

import pyotp
import qrcode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    EncryptionService,
    PasswordService,
    create_access_token,
    create_refresh_token,
    create_2fa_token,
    hash_token,
    verify_token,
)
from app.models import RecoveryToken, RefreshToken, Role, Tenant, User, UserRole, UserTenant

settings = get_settings()
encryption_service = EncryptionService.from_settings_key(settings.encryption_key)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def authenticate(self, email: str, password: str) -> dict | None:
        stmt = select(User).where(User.email == email)
        rows = await self.session.execute(stmt)
        user = rows.scalar_one_or_none()
        if user is None or user.is_deleted:
            return None
        if not PasswordService.verify(password, user.password_hash):
            return None
        stmt = select(UserTenant).where(UserTenant.user_id == user.id, UserTenant.is_active == True)
        rows = await self.session.execute(stmt)
        user_tenant = rows.scalar_one_or_none()
        if user_tenant is None:
            return None
        tenant_id = user_tenant.tenant_id
        stmt = select(Role.name).join(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.tenant_id == tenant_id,
        )
        rows = await self.session.execute(stmt)
        roles = [r[0] for r in rows.all()]
        if user.is_2fa_enabled:
            two_fa_token = create_2fa_token(user_id=user.id, tenant_id=tenant_id)
            return {
                "requires_2fa": True,
                "2fa_token": two_fa_token,
                "user_id": user.id,
                "tenant_id": tenant_id,
                "roles": roles,
            }
        return {
            "requires_2fa": False,
            "user_id": user.id,
            "tenant_id": tenant_id,
            "roles": roles,
        }

    async def create_session(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> dict:
        stmt = select(Role.name).join(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.tenant_id == tenant_id,
        )
        rows = await self.session.execute(stmt)
        roles = [r[0] for r in rows.all()]
        access_token = create_access_token(user_id=user_id, tenant_id=tenant_id, roles=roles)
        refresh_token = create_refresh_token(user_id=user_id, tenant_id=tenant_id, roles=roles)
        token_hash = hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.session.add(rt)
        await self.session.flush()
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    async def refresh_session(self, refresh_token: str) -> dict | None:
        token_hash = hash_token(refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        rows = await self.session.execute(stmt)
        stored = rows.scalar_one_or_none()
        if stored is None:
            return None
        if stored.revoked_at is not None:
            stmt_all = select(RefreshToken).where(
                RefreshToken.user_id == stored.user_id,
                RefreshToken.revoked_at.is_(None),
            )
            rows_all = await self.session.execute(stmt_all)
            for rt in rows_all.scalars().all():
                rt.revoked_at = datetime.now(timezone.utc)
            await self.session.flush()
            return None
        if stored.expires_at < datetime.now(timezone.utc):
            return None
        stored.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()
        user_id = stored.user_id
        stmt = select(UserTenant).where(
            UserTenant.user_id == user_id,
            UserTenant.is_active == True,
        )
        rows = await self.session.execute(stmt)
        ut = rows.scalar_one_or_none()
        if ut is None:
            return None
        tenant_id = ut.tenant_id
        return await self.create_session(user_id=user_id, tenant_id=tenant_id)

    async def revoke_session(self, refresh_token: str) -> bool:
        token_hash = hash_token(refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        rows = await self.session.execute(stmt)
        stored = rows.scalar_one_or_none()
        if stored is None:
            return False
        stored.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True

    async def enrol_2fa(self, user: User) -> dict:
        if user.is_2fa_enabled:
            raise ValueError("2FA already configured")
        secret = pyotp.random_base32()
        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="Activia Trace",
        )
        qr = qrcode.make(uri)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        encrypted_secret = encryption_service.encrypt(secret)
        user.totp_secret = encrypted_secret
        user.is_2fa_enabled = True
        await self.session.flush()
        return {
            "secret": secret,
            "uri": uri,
            "qr_code": qr_b64,
        }

    async def verify_2fa(self, user_id: uuid.UUID, totp_code: str) -> bool:
        stmt = select(User).where(User.id == user_id)
        rows = await self.session.execute(stmt)
        user = rows.scalar_one_or_none()
        if user is None or not user.is_2fa_enabled or user.totp_secret is None:
            return False
        plain_secret = encryption_service.decrypt(user.totp_secret)
        totp = pyotp.TOTP(plain_secret)
        return totp.verify(totp_code)

    async def disable_2fa(self, user: User, password: str) -> bool:
        if not user.is_2fa_enabled:
            raise ValueError("2FA is not enabled")
        if not PasswordService.verify(password, user.password_hash):
            raise ValueError("Invalid password")
        user.totp_secret = None
        user.is_2fa_enabled = False
        await self.session.flush()
        return True

    async def create_recovery_token(self, email: str) -> str | None:
        stmt = select(User).where(User.email == email)
        rows = await self.session.execute(stmt)
        user = rows.scalar_one_or_none()
        if user is None or user.is_deleted:
            return None
        raw_token = create_refresh_token(user_id=user.id, tenant_id=uuid.UUID(int=0), roles=[])
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        rt = RecoveryToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        self.session.add(rt)
        await self.session.flush()
        return raw_token

    async def reset_password(self, token: str, new_password: str) -> bool:
        token_hash = hash_token(token)
        stmt = select(RecoveryToken).where(RecoveryToken.token_hash == token_hash)
        rows = await self.session.execute(stmt)
        stored = rows.scalar_one_or_none()
        if stored is None:
            return False
        if stored.used_at is not None:
            return False
        if stored.expires_at < datetime.now(timezone.utc):
            return False
        stmt = select(User).where(User.id == stored.user_id)
        rows = await self.session.execute(stmt)
        user = rows.scalar_one_or_none()
        if user is None or user.is_deleted:
            return False
        user.password_hash = PasswordService.hash(new_password)
        stored.used_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True
