import uuid
from datetime import date, timedelta

import pytest

from app.core.security import PasswordService, create_access_token
from app.models import (
    Asignacion,
    Carrera,
    Cohorte,
    Dictado,
    Materia,
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
    UserTenant,
)

pytestmark = pytest.mark.asyncio


async def _setup_admin(db_session):
    tenant = Tenant(name="AsigTest", code=f"ASG-{uuid.uuid4().hex[:6].upper()}")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Admin",
        apellido="Asignaciones",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name=f"ASG_ADMIN_{uuid.uuid4().hex[:6]}", tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    from sqlalchemy import select
    stmt = select(Permission).where(Permission.name == "equipos:asignar")
    result = await db_session.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        perm = Permission(name="equipos:asignar", module="equipos", action="asignar")
        db_session.add(perm)
        await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
    db_session.add(rp)
    await db_session.flush()

    return user, tenant


async def _setup_no_perm_user(db_session):
    tenant = Tenant(name="NoPermAsig", code=f"NPA-{uuid.uuid4().hex[:6].upper()}")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"np-asig-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="NoPerm",
        apellido="Asig",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    return user, tenant


async def _create_profesor(db_session, tenant_id):
    prof = User(
        tenant_id=tenant_id,
        email=f"prof-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Profesor",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(prof)
    await db_session.flush()
    return prof


async def _create_carrera(db_session, tenant_id):
    c = Carrera(tenant_id=tenant_id, codigo=f"CARR-{uuid.uuid4().hex[:6]}", nombre="Carrera Test")
    db_session.add(c)
    await db_session.flush()
    return c


async def _create_materia(db_session, tenant_id):
    m = Materia(tenant_id=tenant_id, codigo=f"MAT-{uuid.uuid4().hex[:6]}", nombre="Materia Test")
    db_session.add(m)
    await db_session.flush()
    return m


async def _create_cohorte(db_session, tenant_id, carrera_id):
    c = Cohorte(tenant_id=tenant_id, carrera_id=carrera_id, nombre=f"COH-{uuid.uuid4().hex[:6]}", anio=2026)
    db_session.add(c)
    await db_session.flush()
    return c


class TestAsignacionesCRUD:
    async def test_create_asignacion_all_fields(self, client, db_session):
        admin_user, tenant = await _setup_admin(db_session)
        profesor = await _create_profesor(db_session, tenant.id)
        responsable = await _create_profesor(db_session, tenant.id)
        token = create_access_token(admin_user.id, tenant.id, ["ASG_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/asignaciones/",
            json={
                "usuario_id": str(profesor.id),
                "rol": "PROFESOR",
                "desde": str(date.today()),
                "hasta": str(date.today() + timedelta(days=365)),
                "responsable_id": str(responsable.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["rol"] == "PROFESOR"
        assert data["usuario_id"] == str(profesor.id)
        assert data["responsable_id"] == str(responsable.id)
        assert data["estado_vigencia"] == "Vigente"

    async def test_create_asignacion_sin_contexto(self, client, db_session):
        admin_user, tenant = await _setup_admin(db_session)
        profesor = await _create_profesor(db_session, tenant.id)
        token = create_access_token(admin_user.id, tenant.id, ["ASG_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/asignaciones/",
            json={
                "usuario_id": str(profesor.id),
                "rol": "TUTOR",
                "desde": str(date.today()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["rol"] == "TUTOR"
        assert data["materia_id"] is None
        assert data["carrera_id"] is None
        assert data["cohorte_id"] is None

    async def test_rol_invalido_returns_422(self, client, db_session):
        admin_user, tenant = await _setup_admin(db_session)
        profesor = await _create_profesor(db_session, tenant.id)
        token = create_access_token(admin_user.id, tenant.id, ["ASG_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/asignaciones/",
            json={
                "usuario_id": str(profesor.id),
                "rol": "INVALIDO",
                "desde": str(date.today()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_estado_vigencia_vencida(self, client, db_session):
        admin_user, tenant = await _setup_admin(db_session)
        profesor = await _create_profesor(db_session, tenant.id)
        token = create_access_token(admin_user.id, tenant.id, ["ASG_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/asignaciones/",
            json={
                "usuario_id": str(profesor.id),
                "rol": "PROFESOR",
                "desde": str(date.today() - timedelta(days=365)),
                "hasta": str(date.today() - timedelta(days=1)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["estado_vigencia"] == "Vencida"

    async def test_estado_vigencia_vigente(self, client, db_session):
        admin_user, tenant = await _setup_admin(db_session)
        profesor = await _create_profesor(db_session, tenant.id)
        token = create_access_token(admin_user.id, tenant.id, ["ASG_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/asignaciones/",
            json={
                "usuario_id": str(profesor.id),
                "rol": "PROFESOR",
                "desde": str(date.today() - timedelta(days=30)),
                "hasta": str(date.today() + timedelta(days=30)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["estado_vigencia"] == "Vigente"

    async def test_filtrar_por_usuario(self, client, db_session):
        admin_user, tenant = await _setup_admin(db_session)
        prof_a = await _create_profesor(db_session, tenant.id)
        prof_b = await _create_profesor(db_session, tenant.id)
        token = create_access_token(admin_user.id, tenant.id, ["ASG_ADMIN"])

        await client.post(
            "/api/v1/admin/asignaciones/",
            json={"usuario_id": str(prof_a.id), "rol": "PROFESOR", "desde": str(date.today())},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/admin/asignaciones/",
            json={"usuario_id": str(prof_b.id), "rol": "PROFESOR", "desde": str(date.today())},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = await client.get(
            f"/api/v1/admin/asignaciones/?usuario_id={prof_a.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["usuario_id"] == str(prof_a.id)

    async def test_filtrar_por_materia(self, client, db_session):
        admin_user, tenant = await _setup_admin(db_session)
        prof = await _create_profesor(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        materia_a = await _create_materia(db_session, tenant.id)
        materia_b = await _create_materia(db_session, tenant.id)
        token = create_access_token(admin_user.id, tenant.id, ["ASG_ADMIN"])

        await client.post(
            "/api/v1/admin/asignaciones/",
            json={"usuario_id": str(prof.id), "rol": "PROFESOR", "desde": str(date.today()), "materia_id": str(materia_a.id)},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/admin/asignaciones/",
            json={"usuario_id": str(prof.id), "rol": "PROFESOR", "desde": str(date.today()), "materia_id": str(materia_b.id)},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = await client.get(
            f"/api/v1/admin/asignaciones/?materia_id={materia_a.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    async def test_filtrar_por_rol(self, client, db_session):
        admin_user, tenant = await _setup_admin(db_session)
        prof = await _create_profesor(db_session, tenant.id)
        token = create_access_token(admin_user.id, tenant.id, ["ASG_ADMIN"])

        await client.post(
            "/api/v1/admin/asignaciones/",
            json={"usuario_id": str(prof.id), "rol": "PROFESOR", "desde": str(date.today())},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/admin/asignaciones/",
            json={"usuario_id": str(prof.id), "rol": "TUTOR", "desde": str(date.today())},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = await client.get(
            "/api/v1/admin/asignaciones/?rol=PROFESOR",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["rol"] == "PROFESOR"

    async def test_jerarquia_responsable(self, client, db_session):
        admin_user, tenant = await _setup_admin(db_session)
        profesor = await _create_profesor(db_session, tenant.id)
        responsable = await _create_profesor(db_session, tenant.id)
        token = create_access_token(admin_user.id, tenant.id, ["ASG_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/asignaciones/",
            json={
                "usuario_id": str(profesor.id),
                "rol": "PROFESOR",
                "desde": str(date.today()),
                "responsable_id": str(responsable.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["responsable_id"] == str(responsable.id)

    async def test_soft_delete_asignacion(self, client, db_session):
        admin_user, tenant = await _setup_admin(db_session)
        profesor = await _create_profesor(db_session, tenant.id)
        token = create_access_token(admin_user.id, tenant.id, ["ASG_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/asignaciones/",
            json={"usuario_id": str(profesor.id), "rol": "PROFESOR", "desde": str(date.today())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        asig_id = resp.json()["id"]

        await client.delete(
            f"/api/v1/admin/asignaciones/{asig_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        resp_get = await client.get(
            f"/api/v1/admin/asignaciones/{asig_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_get.status_code == 404

    async def test_403_without_permission(self, client, db_session):
        user, tenant = await _setup_no_perm_user(db_session)
        token = create_access_token(user.id, tenant.id, ["NO_PERM"])

        endpoints = [
            ("POST", "/api/v1/admin/asignaciones/", {"usuario_id": str(uuid.uuid4()), "rol": "PROFESOR", "desde": str(date.today())}),
            ("GET", "/api/v1/admin/asignaciones/", None),
        ]

        for method, path, body in endpoints:
            if method == "POST":
                resp = await client.post(path, json=body, headers={"Authorization": f"Bearer {token}"})
            else:
                resp = await client.get(path, headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 403
