import uuid
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.dependencies import (
    get_current_user,
    get_db,
    get_rate_limiter,
    get_tenant,
)
from app.core.rate_limiter import RateLimiter
from app.core.security import PasswordService, create_access_token
from app.models import Tenant, User, UserTenant


settings = get_settings()


async def _create_user_with_tenant(db_session):
    tenant = Tenant(name="Test", code="TST")
    db_session.add(tenant)
    await db_session.flush()
    user = User(
        tenant_id=tenant.id,
        email="dep@test.com",
        legajo="LEG-DEP",
        nombre="Dep",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()
    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()
    return user, tenant


class TestGetCurrentUser:
    async def test_valid_token(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["admin"])

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/test")
        async def test_endpoint(current_user=Depends(get_current_user)):
            return {"id": str(current_user.id), "email": current_user.email}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/test", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == str(user.id)
            assert data["email"] == "dep@test.com"

        app.dependency_overrides.clear()

    async def test_expired_token(self, db_session, test_engine):
        import time
        import jwt

        user, tenant = await _create_user_with_tenant(db_session)
        payload = {
            "jti": str(uuid.uuid4()),
            "sub": str(user.id),
            "type": "access",
            "tenant_id": str(tenant.id),
            "roles": [],
            "iat": int(time.time()) - 7200,
            "exp": int(time.time()) - 3600,
        }
        expired_token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/test")
        async def test_endpoint(current_user=Depends(get_current_user)):
            return {"id": str(current_user.id)}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/test", headers={"Authorization": f"Bearer {expired_token}"})
            assert resp.status_code == 401
            assert "Token expired" in resp.text

        app.dependency_overrides.clear()

    async def test_missing_header(self, db_session, test_engine):
        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/test")
        async def test_endpoint(current_user=Depends(get_current_user)):
            return {"id": str(current_user.id)}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/test")
            assert resp.status_code == 401

        app.dependency_overrides.clear()

    async def test_invalid_token(self, db_session, test_engine):
        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/test")
        async def test_endpoint(current_user=Depends(get_current_user)):
            return {"id": str(current_user.id)}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/test", headers={"Authorization": "Bearer invalid.jwt.token"})
            assert resp.status_code == 401

        app.dependency_overrides.clear()

    async def test_soft_deleted_user(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["admin"])
        user.soft_delete()
        await db_session.flush()

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/test")
        async def test_endpoint(current_user=Depends(get_current_user)):
            return {"id": str(current_user.id)}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/test", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 401

        app.dependency_overrides.clear()

    async def test_token_wrong_type(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        from app.core.security import create_2fa_token
        token = create_2fa_token(user_id=user.id, tenant_id=tenant.id)

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/test")
        async def test_endpoint(current_user=Depends(get_current_user)):
            return {"id": str(current_user.id)}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/test", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 401

        app.dependency_overrides.clear()


from fastapi import Depends


class TestGetTenant:
    async def test_returns_tenant(self, db_session, test_engine):
        user, tenant = await _create_user_with_tenant(db_session)
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["admin"])

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/test")
        async def test_endpoint(
            current_user=Depends(get_current_user),
            current_tenant=Depends(get_tenant),
        ):
            return {"tenant_id": str(current_tenant.id), "tenant_code": current_tenant.code}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/test", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["tenant_id"] == str(tenant.id)
            assert data["tenant_code"] == "TST"

        app.dependency_overrides.clear()


class TestGetRateLimiter:
    def test_returns_singleton(self):
        rl1 = get_rate_limiter()
        rl2 = get_rate_limiter()
        assert rl1 is rl2
        assert isinstance(rl1, RateLimiter)
        assert rl1.max_attempts == 50
        assert rl1.window_seconds == 60
