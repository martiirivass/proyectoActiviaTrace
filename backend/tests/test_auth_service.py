import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.security import (
    PasswordService,
    create_access_token,
    create_refresh_token,
    create_2fa_token,
    hash_token,
    verify_token,
)
from app.models import RecoveryToken, RefreshToken, Tenant, User, UserRole, UserTenant, Role
from app.services.auth_service import AuthService


pytestmark = pytest.mark.asyncio

settings = get_settings()


async def _create_tenant_and_user(db_session, email="test@example.com", password="securepass123"):
    tenant = Tenant(name="Test Tenant", code="TST")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        email=email,
        legajo="LEG-AUTH",
        nombre="Test",
        apellido="User",
        password_hash=PasswordService.hash(password),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    return user, tenant


class TestAuthenticate:
    async def test_authenticate_valid_credentials(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        result = await svc.authenticate(email="test@example.com", password="securepass123")
        assert result is not None
        assert result["user_id"] == user.id
        assert result["tenant_id"] == tenant.id
        assert "roles" in result

    async def test_authenticate_invalid_password(self, db_session, test_engine):
        await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        result = await svc.authenticate(email="test@example.com", password="wrongpass")
        assert result is None

    async def test_authenticate_non_existent_email(self, db_session, test_engine):
        svc = AuthService(db_session)
        result = await svc.authenticate(email="nobody@test.com", password="anypass")
        assert result is None

    async def test_authenticate_soft_deleted_user(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        user.soft_delete()
        await db_session.flush()
        svc = AuthService(db_session)
        result = await svc.authenticate(email="test@example.com", password="securepass123")
        assert result is None

    async def test_authenticate_with_2fa_enabled(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        user.is_2fa_enabled = True
        await db_session.flush()
        svc = AuthService(db_session)
        result = await svc.authenticate(email="test@example.com", password="securepass123")
        assert result is not None
        assert "2fa_token" in result
        assert result.get("requires_2fa") is True


class TestCreateSession:
    async def test_create_session_returns_tokens(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        result = await svc.create_session(user_id=user.id, tenant_id=tenant.id)
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 900

    async def test_create_session_stores_refresh_token(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        result = await svc.create_session(user_id=user.id, tenant_id=tenant.id)
        token_hash = hash_token(result["refresh_token"])
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        rows = await db_session.execute(stmt)
        stored = rows.scalar_one_or_none()
        assert stored is not None
        assert stored.user_id == user.id
        assert stored.revoked_at is None

    async def test_create_session_with_roles(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        role = Role(name="admin", tenant_id=tenant.id)
        db_session.add(role)
        await db_session.flush()
        ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
        db_session.add(ur)
        await db_session.flush()
        svc = AuthService(db_session)
        result = await svc.create_session(user_id=user.id, tenant_id=tenant.id)
        assert "access_token" in result


class TestRefreshSession:
    async def test_refresh_success(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        session = await svc.create_session(user_id=user.id, tenant_id=tenant.id)
        result = await svc.refresh_session(session["refresh_token"])
        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["refresh_token"] != session["refresh_token"]

    async def test_refresh_revokes_old_token(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        session = await svc.create_session(user_id=user.id, tenant_id=tenant.id)
        old_hash = hash_token(session["refresh_token"])
        await svc.refresh_session(session["refresh_token"])
        stmt = select(RefreshToken).where(RefreshToken.token_hash == old_hash)
        rows = await db_session.execute(stmt)
        old_token = rows.scalar_one()
        assert old_token.revoked_at is not None

    async def test_refresh_reuse_detection(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        session = await svc.create_session(user_id=user.id, tenant_id=tenant.id)
        await svc.refresh_session(session["refresh_token"])
        result = await svc.refresh_session(session["refresh_token"])
        assert result is None

    async def test_refresh_expired_token(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        expired_token = create_refresh_token(user.id, tenant.id, [])
        expired_hash = hash_token(expired_token)
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        rt = RefreshToken(user_id=user.id, token_hash=expired_hash, expires_at=past)
        db_session.add(rt)
        await db_session.flush()
        result = await svc.refresh_session(expired_token)
        assert result is None

    async def test_refresh_invalid_token(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        result = await svc.refresh_session("nonexistent-token-12345")
        assert result is None


class TestRevokeSession:
    async def test_logout_revokes_token(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        session = await svc.create_session(user_id=user.id, tenant_id=tenant.id)
        await svc.revoke_session(session["refresh_token"])
        token_hash = hash_token(session["refresh_token"])
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        rows = await db_session.execute(stmt)
        stored = rows.scalar_one()
        assert stored.revoked_at is not None

    async def test_logout_invalid_token(self, db_session, test_engine):
        svc = AuthService(db_session)
        result = await svc.revoke_session("bogus-token")
        assert result is False


class TestEnrol2FA:
    async def test_enrol_returns_secret_and_uri(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        result = await svc.enrol_2fa(user)
        assert "secret" in result
        assert "uri" in result
        assert "qr_code" in result
        assert result["secret"] is not None
        assert "otpauth://" in result["uri"]

    async def test_enrol_stores_encrypted_secret(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        result = await svc.enrol_2fa(user)
        await db_session.refresh(user)
        assert user.totp_secret is not None
        assert user.is_2fa_enabled is True

    async def test_enrol_when_already_configured(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        await svc.enrol_2fa(user)
        with pytest.raises(ValueError, match="2FA already configured"):
            await svc.enrol_2fa(user)


class TestVerify2FA:
    async def test_verify_valid_code(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        enrol = await svc.enrol_2fa(user)
        import pyotp
        totp = pyotp.TOTP(enrol["secret"])
        valid_code = totp.now()
        result = await svc.verify_2fa(user_id=user.id, totp_code=valid_code)
        assert result is True

    async def test_verify_invalid_code(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        await svc.enrol_2fa(user)
        result = await svc.verify_2fa(user_id=user.id, totp_code="000000")
        assert result is False

    async def test_verify_no_2fa_enabled(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        result = await svc.verify_2fa(user_id=user.id, totp_code="123456")
        assert result is False


class TestDisable2FA:
    async def test_disable_with_correct_password(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        await svc.enrol_2fa(user)
        result = await svc.disable_2fa(user, "securepass123")
        assert result is True
        await db_session.refresh(user)
        assert user.is_2fa_enabled is False
        assert user.totp_secret is None

    async def test_disable_with_incorrect_password(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        await svc.enrol_2fa(user)
        with pytest.raises(ValueError, match="Invalid password"):
            await svc.disable_2fa(user, "wrongpassword")

    async def test_disable_when_2fa_not_enabled(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        with pytest.raises(ValueError, match="2FA is not enabled"):
            await svc.disable_2fa(user, "securepass123")


class TestRecoveryToken:
    async def test_create_recovery_token(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        token = await svc.create_recovery_token("test@example.com")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    async def test_create_recovery_token_stores_in_db(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        token = await svc.create_recovery_token("test@example.com")
        token_hash = hash_token(token)
        stmt = select(RecoveryToken).where(RecoveryToken.token_hash == token_hash)
        rows = await db_session.execute(stmt)
        stored = rows.scalar_one()
        assert stored.user_id == user.id
        assert stored.used_at is None

    async def test_create_recovery_token_nonexistent_email(self, db_session, test_engine):
        svc = AuthService(db_session)
        token = await svc.create_recovery_token("unknown@test.com")
        assert token is None

    async def test_reset_password_success(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        token = await svc.create_recovery_token("test@example.com")
        new_password = "newpass456"
        result = await svc.reset_password(token, new_password)
        assert result is True
        assert PasswordService.verify("newpass456", user.password_hash) is True

    async def test_reset_password_reuse_token_fails(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        token = await svc.create_recovery_token("test@example.com")
        await svc.reset_password(token, "newpass456")
        result = await svc.reset_password(token, "anotherpass")
        assert result is False

    async def test_reset_password_expired_token(self, db_session, test_engine):
        user, tenant = await _create_tenant_and_user(db_session)
        svc = AuthService(db_session)
        token = await svc.create_recovery_token("test@example.com")
        token_hash = hash_token(token)
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        stored = await db_session.execute(
            select(RecoveryToken).where(RecoveryToken.token_hash == token_hash)
        )
        rt = stored.scalar_one()
        rt.expires_at = past
        await db_session.flush()
        result = await svc.reset_password(token, "newpass")
        assert result is False

    async def test_reset_password_invalid_token(self, db_session, test_engine):
        svc = AuthService(db_session)
        result = await svc.reset_password("invalid-token-value", "newpass")
        assert result is False
