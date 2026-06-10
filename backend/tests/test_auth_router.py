import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.dependencies import get_db, get_rate_limiter
from app.core.rate_limiter import RateLimiter
from app.core.security import PasswordService, create_access_token, create_2fa_token, hash_token
from app.main import app
from app.models import RefreshToken, Tenant, User, UserTenant, RecoveryToken, Role, UserRole

pytestmark = pytest.mark.asyncio

settings = get_settings()


async def _create_user_with_tenant(db_session, email="test@example.com", password="SecurePass123!"):
    tenant = Tenant(name="Test Tenant", code="TST")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        email=email,
        legajo="LEG-INT",
        nombre="Integration",
        apellido="Test",
        password_hash=PasswordService.hash(password),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name="user", tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    return user, tenant


class TestLogin:
    async def test_login_success(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 900
            assert data.get("requires_2fa") is False

        app.dependency_overrides.clear()

    async def test_login_invalid_password(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "WrongPass123!",
            })
            assert resp.status_code == 401
            assert "Invalid email or password" in resp.text

        app.dependency_overrides.clear()

    async def test_login_non_existent_email(self, db_session, test_engine):
        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "nobody@example.com",
                "password": "AnyPass123!",
            })
            assert resp.status_code == 401
            assert "Invalid email or password" in resp.text

        app.dependency_overrides.clear()

    async def test_login_soft_deleted_user(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        user.soft_delete()
        await db_session.flush()

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            })
            assert resp.status_code == 401

        app.dependency_overrides.clear()

    async def test_login_requires_2fa(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        user.is_2fa_enabled = True
        await db_session.flush()

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("requires_2fa") is True
            assert "two_fa_token" in data
            assert "access_token" not in data
            assert "refresh_token" not in data

        app.dependency_overrides.clear()


class TestRefresh:
    async def test_refresh_success(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            })
            refresh_token = login_resp.json()["refresh_token"]

            resp = await client.post("/api/v1/auth/refresh", json={
                "refresh_token": refresh_token,
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["refresh_token"] != refresh_token

        app.dependency_overrides.clear()

    async def test_refresh_reuse_detection(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            })
            refresh_token = login_resp.json()["refresh_token"]

            await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

            resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
            assert resp.status_code == 401

        app.dependency_overrides.clear()

    async def test_refresh_expired_token(self, db_session, test_engine):
        from datetime import datetime, timedelta, timezone
        user, tenant = await _create_user_with_tenant(db_session)
        from app.core.security import create_refresh_token
        raw_token = create_refresh_token(user.id, tenant.id, [])
        token_hash = hash_token(raw_token)
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        rt = RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=past)
        db_session.add(rt)
        await db_session.flush()

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": raw_token})
            assert resp.status_code == 401

        app.dependency_overrides.clear()


class TestLogout:
    async def test_logout_success(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            })
            access_token = login_resp.json()["access_token"]
            refresh_token = login_resp.json()["refresh_token"]

            resp = await client.post("/api/v1/auth/logout", json={
                "refresh_token": refresh_token,
            }, headers={"Authorization": f"Bearer {access_token}"})
            assert resp.status_code == 204

            token_hash = hash_token(refresh_token)
            stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            rows = await db_session.execute(stmt)
            stored = rows.scalar_one()
            assert stored.revoked_at is not None

        app.dependency_overrides.clear()

    async def test_logout_unauthenticated(self, db_session, test_engine):
        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/logout", json={"refresh_token": "some-token"})
            assert resp.status_code == 401

        app.dependency_overrides.clear()


class TestTwoFA:
    async def test_enrol_2fa(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        access_token = create_access_token(user.id, tenant.id, ["user"])

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/2fa/enrol", headers={
                "Authorization": f"Bearer {access_token}",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "secret" in data
            assert "uri" in data
            assert "qr_code" in data
            assert "otpauth://" in data["uri"]

        app.dependency_overrides.clear()

    async def test_enrol_2fa_already_enabled(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        user.is_2fa_enabled = True
        await db_session.flush()
        access_token = create_access_token(user.id, tenant.id, ["user"])

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/2fa/enrol", headers={
                "Authorization": f"Bearer {access_token}",
            })
            assert resp.status_code == 409

        app.dependency_overrides.clear()

    async def test_verify_2fa_and_complete_login(self, db_session, test_engine):
        import pyotp
        user, tenant = await _create_user_with_tenant(db_session)
        user.is_2fa_enabled = True
        from app.core.security import EncryptionService
        enc = EncryptionService.from_settings_key(settings.encryption_key)
        secret = pyotp.random_base32()
        user.totp_secret = enc.encrypt(secret)
        await db_session.flush()
        two_fa_token = create_2fa_token(user.id, tenant.id)
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/2fa/verify", json={
                "two_fa_token": two_fa_token,
                "totp_code": valid_code,
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

        app.dependency_overrides.clear()

    async def test_verify_2fa_invalid_code(self, db_session, test_engine):
        import pyotp
        user, tenant = await _create_user_with_tenant(db_session)
        user.is_2fa_enabled = True
        from app.core.security import EncryptionService
        enc = EncryptionService.from_settings_key(settings.encryption_key)
        secret = pyotp.random_base32()
        user.totp_secret = enc.encrypt(secret)
        await db_session.flush()
        two_fa_token = create_2fa_token(user.id, tenant.id)

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/2fa/verify", json={
                "two_fa_token": two_fa_token,
                "totp_code": "000000",
            })
            assert resp.status_code == 401

        app.dependency_overrides.clear()

    async def test_disable_2fa(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        user.is_2fa_enabled = True
        from app.core.security import EncryptionService
        import pyotp
        enc = EncryptionService.from_settings_key(settings.encryption_key)
        user.totp_secret = enc.encrypt(pyotp.random_base32())
        await db_session.flush()
        access_token = create_access_token(user.id, tenant.id, ["user"])

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/2fa/disable", json={
                "password": "SecurePass123!",
            }, headers={"Authorization": f"Bearer {access_token}"})
            assert resp.status_code == 200
            await db_session.refresh(user)
            assert user.is_2fa_enabled is False

        app.dependency_overrides.clear()

    async def test_disable_2fa_wrong_password(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        user.is_2fa_enabled = True
        access_token = create_access_token(user.id, tenant.id, ["user"])

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/2fa/disable", json={
                "password": "WrongPass123!",
            }, headers={"Authorization": f"Bearer {access_token}"})
            assert resp.status_code == 401

        app.dependency_overrides.clear()

    async def test_enrol_unauthenticated(self, db_session, test_engine):
        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/2fa/enrol")
            assert resp.status_code == 401

        app.dependency_overrides.clear()


class TestForgotReset:
    async def test_forgot_generates_token(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/forgot", json={
                "email": "test@example.com",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "token" in data
            assert len(data["token"]) > 20

        app.dependency_overrides.clear()

    async def test_forgot_nonexistent_email(self, db_session, test_engine):
        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/forgot", json={
                "email": "unknown@test.com",
            })
            assert resp.status_code == 404

        app.dependency_overrides.clear()

    async def test_reset_password_complete_flow(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            forgot_resp = await client.post("/api/v1/auth/forgot", json={
                "email": "test@example.com",
            })
            token = forgot_resp.json()["token"]

            resp = await client.post("/api/v1/auth/reset", json={
                "token": token,
                "new_password": "NewSecurePass456!",
            })
            assert resp.status_code == 200
            assert resp.json()["message"] == "Password reset successfully"

            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "NewSecurePass456!",
            })
            assert login_resp.status_code == 200
            assert "access_token" in login_resp.json()

        app.dependency_overrides.clear()

    async def test_reset_password_reuse_token(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            forgot_resp = await client.post("/api/v1/auth/forgot", json={
                "email": "test@example.com",
            })
            token = forgot_resp.json()["token"]

            await client.post("/api/v1/auth/reset", json={
                "token": token, "new_password": "NewPass456!",
            })

            resp = await client.post("/api/v1/auth/reset", json={
                "token": token, "new_password": "AnotherPass789!",
            })
            assert resp.status_code == 400

        app.dependency_overrides.clear()


class TestRateLimiting:
    async def test_rate_limit_exceeded(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        rl = RateLimiter(max_attempts=3, window_seconds=60)
        original_get_rl = get_rate_limiter

        from app.core.dependencies import get_rate_limiter as grl

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[grl] = lambda: rl

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for _ in range(3):
                resp = await client.post("/api/v1/auth/login", json={
                    "email": "ratelimit@test.com",
                    "password": "AnyPass123!",
                })
                assert resp.status_code == 401

            resp = await client.post("/api/v1/auth/login", json={
                "email": "ratelimit@test.com",
                "password": "AnyPass123!",
            })
            assert resp.status_code == 429

        app.dependency_overrides.clear()


class TestProtectedEndpoint:
    async def test_access_protected_endpoint(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        access_token = create_access_token(user.id, tenant.id, ["user"])

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/me", headers={
                "Authorization": f"Bearer {access_token}",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["email"] == "test@example.com"
            assert data["id"] == str(user.id)

        app.dependency_overrides.clear()

    async def test_access_protected_endpoint_no_auth(self, db_session, test_engine):
        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/me")
            assert resp.status_code == 401

        app.dependency_overrides.clear()


class TestFullIntegration:
    async def test_full_auth_flow(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            })
            assert login_resp.status_code == 200
            login_data = login_resp.json()
            access_token = login_data["access_token"]
            refresh_token = login_data["refresh_token"]

            me_resp = await client.get("/api/v1/auth/me", headers={
                "Authorization": f"Bearer {access_token}",
            })
            assert me_resp.status_code == 200
            assert me_resp.json()["email"] == "test@example.com"

            refresh_resp = await client.post("/api/v1/auth/refresh", json={
                "refresh_token": refresh_token,
            })
            assert refresh_resp.status_code == 200
            new_access = refresh_resp.json()["access_token"]
            new_refresh = refresh_resp.json()["refresh_token"]

            me2_resp = await client.get("/api/v1/auth/me", headers={
                "Authorization": f"Bearer {new_access}",
            })
            assert me2_resp.status_code == 200
            assert me2_resp.json()["email"] == "test@example.com"

            logout_resp = await client.post("/api/v1/auth/logout", json={
                "refresh_token": new_refresh,
            }, headers={"Authorization": f"Bearer {new_access}"})
            assert logout_resp.status_code == 204

            refresh_after_logout = await client.post("/api/v1/auth/refresh", json={
                "refresh_token": new_refresh,
            })
            assert refresh_after_logout.status_code == 401

        app.dependency_overrides.clear()
