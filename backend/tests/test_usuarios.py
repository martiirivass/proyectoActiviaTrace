import uuid
import base64

import pytest
from sqlalchemy import text

from app.core.security import PasswordService, create_access_token
from app.models import Permission, Role, RolePermission, Tenant, User, UserRole, UserTenant

pytestmark = pytest.mark.asyncio


async def _setup_admin(db_session, perm_name="usuarios:gestionar"):
    tenant = Tenant(name="UsrTest", code=f"USR-{uuid.uuid4().hex[:6].upper()}")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Admin",
        apellido="Usuarios",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name=f"USR_ADMIN_{uuid.uuid4().hex[:6]}", tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    from sqlalchemy import select
    module, action = perm_name.split(":", 1)
    stmt = select(Permission).where(Permission.name == perm_name)
    result = await db_session.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        perm = Permission(name=perm_name, module=module, action=action)
        db_session.add(perm)
        await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
    db_session.add(rp)
    await db_session.flush()

    return user, tenant


async def _setup_no_perm_user(db_session):
    tenant = Tenant(name="NoPerm", code=f"NP-{uuid.uuid4().hex[:6].upper()}")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"np-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="NoPerm",
        apellido="User",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    return user, tenant


class TestUsuariosCRUD:
    async def test_create_user_with_all_pii_fields(self, client, db_session):
        user, tenant = await _setup_admin(db_session)
        token = create_access_token(user.id, tenant.id, ["USR_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/usuarios/",
            json={
                "email": "juan@test.com",
                "password": "SecurePass123!",
                "nombre": "Juan",
                "apellido": "Pérez",
                "legajo": "LEG-JUAN",
                "dni": "12345678",
                "cuil": "20-12345678-9",
                "cbu": "0000003100012345678901",
                "alias_cbu": "JUAN.PEREZ.ALIAS",
                "banco": "Banco Nación",
                "regional": "CABA",
                "legajo_profesional": "LP-1234",
                "facturador": True,
                "estado": "Activo",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "juan@test.com"
        assert data["nombre"] == "Juan"
        assert data["apellido"] == "Pérez"
        assert data["legajo"] == "LEG-JUAN"
        assert data["dni"] == "12345678"
        assert data["cuil"] == "20-12345678-9"
        assert data["cbu"] == "0000003100012345678901"
        assert data["alias_cbu"] == "JUAN.PEREZ.ALIAS"
        assert data["banco"] == "Banco Nación"
        assert data["regional"] == "CABA"
        assert data["legajo_profesional"] == "LP-1234"
        assert data["facturador"] is True
        assert data["estado"] == "Activo"

    async def test_pii_encrypted_in_db(self, client, db_session):
        user, tenant = await _setup_admin(db_session)
        token = create_access_token(user.id, tenant.id, ["USR_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/usuarios/",
            json={
                "email": "pii-test@test.com",
                "password": "Pass123!",
                "nombre": "PII",
                "apellido": "Test",
                "dni": "87654321",
                "cuil": "27-87654321-0",
                "cbu": "0000003100012345678902",
                "alias_cbu": "PII.TEST.ALIAS",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        result = await db_session.execute(text("SELECT dni, cuil, cbu, alias_cbu FROM users WHERE id = :uid"), {"uid": uuid.UUID(user_id)})
        row = result.one()
        raw_dni, raw_cuil, raw_cbu, raw_alias = row

        assert raw_dni != "87654321"
        assert raw_cuil != "27-87654321-0"
        assert raw_cbu != "0000003100012345678902"
        assert raw_alias != "PII.TEST.ALIAS"

        for val in [raw_dni, raw_cuil, raw_cbu, raw_alias]:
            try:
                base64.b64decode(val)
                is_valid = True
            except Exception:
                is_valid = False
            assert is_valid

    async def test_pii_decrypted_in_response(self, client, db_session):
        user, tenant = await _setup_admin(db_session)
        token = create_access_token(user.id, tenant.id, ["USR_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/usuarios/",
            json={
                "email": "pii-decrypt@test.com",
                "password": "Pass123!",
                "nombre": "PII",
                "apellido": "Decrypt",
                "dni": "11223344",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        created_id = resp.json()["id"]

        resp_get = await client.get(
            f"/api/v1/admin/usuarios/{created_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_get.status_code == 200
        assert resp_get.json()["dni"] == "11223344"

    async def test_email_duplicate_same_tenant_returns_409(self, client, db_session):
        user, tenant = await _setup_admin(db_session)
        token = create_access_token(user.id, tenant.id, ["USR_ADMIN"])

        await client.post(
            "/api/v1/admin/usuarios/",
            json={"email": "dup@test.com", "password": "Pass123!", "nombre": "A", "apellido": "B"},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = await client.post(
            "/api/v1/admin/usuarios/",
            json={"email": "dup@test.com", "password": "Pass123!", "nombre": "C", "apellido": "D"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    async def test_same_email_different_tenants_ok(self, client, db_session):
        user_a, tenant_a = await _setup_admin(db_session)
        user_b, tenant_b = await _setup_admin(db_session)
        token_a = create_access_token(user_a.id, tenant_a.id, ["USR_ADMIN"])
        token_b = create_access_token(user_b.id, tenant_b.id, ["USR_ADMIN"])

        resp_a = await client.post(
            "/api/v1/admin/usuarios/",
            json={"email": "cross@test.com", "password": "Pass123!", "nombre": "A", "apellido": "B"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert resp_a.status_code == 201

        resp_b = await client.post(
            "/api/v1/admin/usuarios/",
            json={"email": "cross@test.com", "password": "Pass123!", "nombre": "C", "apellido": "D"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp_b.status_code == 201

    async def test_soft_delete_not_listed(self, client, db_session):
        user, tenant = await _setup_admin(db_session)
        token = create_access_token(user.id, tenant.id, ["USR_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/usuarios/",
            json={"email": "del@test.com", "password": "Pass123!", "nombre": "Del", "apellido": "User"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        del_id = resp.json()["id"]

        await client.delete(
            f"/api/v1/admin/usuarios/{del_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        resp_get = await client.get(
            f"/api/v1/admin/usuarios/{del_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_get.status_code == 404

    async def test_response_does_not_expose_password_hash(self, client, db_session):
        user, tenant = await _setup_admin(db_session)
        token = create_access_token(user.id, tenant.id, ["USR_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/usuarios/",
            json={"email": "safe@test.com", "password": "Secret123!", "nombre": "Safe", "apellido": "User"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "password_hash" not in data
        assert "totp_secret" not in data

    async def test_403_without_permission(self, client, db_session):
        user, tenant = await _setup_no_perm_user(db_session)
        token = create_access_token(user.id, tenant.id, ["NO_PERM"])

        endpoints = [
            ("POST", "/api/v1/admin/usuarios/", {"email": "x@x.com", "password": "Pass123!", "nombre": "X", "apellido": "X"}),
            ("GET", "/api/v1/admin/usuarios/", None),
            ("GET", f"/api/v1/admin/usuarios/{uuid.uuid4()}", None),
        ]

        for method, path, body in endpoints:
            if method == "POST":
                resp = await client.post(path, json=body, headers={"Authorization": f"Bearer {token}"})
            else:
                resp = await client.get(path, headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 403
