import uuid

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.security import PasswordService, create_access_token
from app.models import Permission, Role, RolePermission, Tenant, User, UserRole, UserTenant
from app.services.permission_service import PermissionService

pytestmark = pytest.mark.asyncio


async def _setup_user_with_permission(db_session, permission_codename: str):
    tenant = Tenant(name="Perm Test", code="PERM")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        email=f"perm-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Perm", apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name="PERM_ROLE", tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    module, action = permission_codename.split(":", 1)
    perm = Permission(name=permission_codename, module=module, action=action)
    db_session.add(perm)
    await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id,
                        tenant_id=tenant.id, scope="global")
    db_session.add(rp)
    await db_session.flush()

    return user, tenant


class TestRequirePermission:
    async def test_user_with_permission_passes_guard(self, db_session, test_engine):
        user, tenant = await _setup_user_with_permission(db_session, "test:acceder")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["PERM_ROLE"])

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/secure")
        async def secure_endpoint(_=Depends(require_permission("test:acceder"))):
            return {"ok": True}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/secure", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            assert resp.json() == {"ok": True}

        app.dependency_overrides.clear()

    async def test_user_without_permission_receives_403(self, db_session, test_engine):
        user, tenant = await _setup_user_with_permission(db_session, "test:otro")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["PERM_ROLE"])

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/secure")
        async def secure_endpoint(_=Depends(require_permission("test:acceder"))):
            return {"ok": True}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/secure", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 403

        app.dependency_overrides.clear()

    async def test_unauthenticated_user_receives_401(self, db_session, test_engine):
        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/secure")
        async def secure_endpoint(_=Depends(require_permission("test:acceder"))):
            return {"ok": True}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/secure")
            assert resp.status_code == 401

        app.dependency_overrides.clear()

    async def test_union_of_roles_grants_permission(self, db_session, test_engine):
        tenant = Tenant(name="Union Test", code="UNION")
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            email="union@test.com", legajo="LEG-UNION",
            nombre="Union", apellido="Test",
            password_hash=PasswordService.hash("pass"),
        )
        db_session.add(user)
        await db_session.flush()

        ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
        db_session.add(ut)
        await db_session.flush()

        role_a = Role(name="ROLE_A_ONLY", tenant_id=tenant.id)
        db_session.add(role_a)
        await db_session.flush()

        role_b = Role(name="ROLE_B_WITH_PERM", tenant_id=tenant.id)
        db_session.add(role_b)
        await db_session.flush()

        ur_a = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role_a.id)
        db_session.add(ur_a)
        ur_b = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role_b.id)
        db_session.add(ur_b)
        await db_session.flush()

        perm = Permission(name="test:union_perm", module="test", action="union_perm")
        db_session.add(perm)
        await db_session.flush()

        rp = RolePermission(role_id=role_b.id, permission_id=perm.id,
                            tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

        token = create_access_token(user_id=user.id, tenant_id=tenant.id,
                                    roles=["ROLE_A_ONLY", "ROLE_B_WITH_PERM"])

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session

        @app.get("/secure")
        async def secure_endpoint(_=Depends(require_permission("test:union_perm"))):
            return {"ok": True}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/secure", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200

        app.dependency_overrides.clear()
