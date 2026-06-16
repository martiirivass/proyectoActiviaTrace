import uuid

import pytest
from sqlalchemy import select

from app.core.security import PasswordService, create_access_token
from app.models import Tenant, User, UserTenant

pytestmark = pytest.mark.asyncio


async def _setup_user(db_session):
    tenant = Tenant(name="PerfilTest", code=f"PF-{uuid.uuid4().hex[:6].upper()}")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"perfil-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Perfil",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
        sexo="M",
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    return user, tenant


class TestPerfilRead:

    async def test_get_perfil_returns_profile_with_sexo(self, client, db_session):
        user, tenant = await _setup_user(db_session)
        token = create_access_token(user.id, tenant.id, [])

        resp = await client.get(
            "/api/v1/perfil/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(user.id)
        assert data["email"] == user.email
        assert data["sexo"] == "M"
        assert "password_hash" not in data
        assert "totp_secret" not in data

    async def test_get_perfil_without_auth_returns_401(self, client, db_session):
        resp = await client.get("/api/v1/perfil/")
        assert resp.status_code == 401


class TestPerfilUpdate:

    async def test_update_editable_fields(self, client, db_session):
        user, tenant = await _setup_user(db_session)
        token = create_access_token(user.id, tenant.id, [])

        resp = await client.put(
            "/api/v1/perfil/",
            json={"nombre": "NuevoNombre", "apellido": "NuevoApellido", "sexo": "F"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "NuevoNombre"
        assert data["apellido"] == "NuevoApellido"
        assert data["sexo"] == "F"

    async def test_update_with_cuil_returns_422(self, client, db_session):
        user, tenant = await _setup_user(db_session)
        token = create_access_token(user.id, tenant.id, [])

        resp = await client.put(
            "/api/v1/perfil/",
            json={"cuil": "20-12345678-9"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "CUIL" in data["detail"] or "cuil" in str(data["detail"]).lower()

    async def test_update_with_legajo_returns_422(self, client, db_session):
        user, tenant = await _setup_user(db_session)
        token = create_access_token(user.id, tenant.id, [])

        resp = await client.put(
            "/api/v1/perfil/",
            json={"legajo": "LEG-NEW"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "LEGAJO" in data["detail"] or "legajo" in str(data["detail"]).lower()

    async def test_update_with_duplicate_email_returns_409(self, client, db_session):
        user, tenant = await _setup_user(db_session)
        token = create_access_token(user.id, tenant.id, [])

        other = User(
            tenant_id=tenant.id,
            email=f"other-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Other",
            apellido="User",
            password_hash=PasswordService.hash("pass"),
        )
        db_session.add(other)
        await db_session.flush()

        existing_email = other.email
        resp = await client.put(
            "/api/v1/perfil/",
            json={"email": existing_email},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    async def test_partial_update_only_modifies_sent_fields(self, client, db_session):
        user, tenant = await _setup_user(db_session)
        token = create_access_token(user.id, tenant.id, [])

        resp = await client.put(
            "/api/v1/perfil/",
            json={"nombre": "SoloNombre"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "SoloNombre"
        assert data["apellido"] == user.apellido

    async def test_update_without_auth_returns_401(self, client, db_session):
        resp = await client.put(
            "/api/v1/perfil/",
            json={"nombre": "Hacker"},
        )
        assert resp.status_code == 401

    async def test_update_with_unknown_field_returns_422(self, client, db_session):
        user, tenant = await _setup_user(db_session)
        token = create_access_token(user.id, tenant.id, [])

        resp = await client.put(
            "/api/v1/perfil/",
            json={"campo_inexistente": "valor"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
