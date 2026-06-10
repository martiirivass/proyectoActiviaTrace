import uuid

import pytest

from app.core.security import PasswordService, create_access_token
from app.models import Permission, Role, RolePermission, Tenant, User, UserRole, UserTenant

pytestmark = pytest.mark.asyncio


async def _setup_admin_user(db_session, tenant=None):
    if tenant is None:
        code = f"EST{uuid.uuid4().hex[:6].upper()}"
        tenant = Tenant(name=f"Estructura Test {code}", code=code)
        db_session.add(tenant)
        await db_session.flush()

    user = User(
        email=f"est-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Estructura",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name="ESTRUCTURA_ADMIN", tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    from sqlalchemy import select
    stmt = select(Permission).where(Permission.name == "estructura:gestionar")
    result = await db_session.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        perm = Permission(name="estructura:gestionar", module="estructura", action="gestionar")
        db_session.add(perm)
        await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
    db_session.add(rp)
    await db_session.flush()

    return user, tenant, role


async def _setup_user_without_permission(db_session, tenant=None):
    if tenant is None:
        code = f"NP{uuid.uuid4().hex[:6].upper()}"
        tenant = Tenant(name=f"NoPerm Test {code}", code=code)
        db_session.add(tenant)
        await db_session.flush()

    user = User(
        email=f"np-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="NoPerm",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    return user, tenant


async def _create_carrera(db_session, tenant_id, codigo="PROG", nombre="Programación"):
    from app.models.carrera import Carrera
    c = Carrera(tenant_id=tenant_id, codigo=codigo, nombre=nombre)
    db_session.add(c)
    await db_session.flush()
    return c


async def _create_cohorte(db_session, tenant_id, carrera_id, nombre="MAR-2026", anio=2026):
    from app.models.cohorte import Cohorte
    c = Cohorte(tenant_id=tenant_id, carrera_id=carrera_id, nombre=nombre, anio=anio)
    db_session.add(c)
    await db_session.flush()
    return c


async def _create_materia(db_session, tenant_id, codigo="PROG_I", nombre="Programación I"):
    from app.models.materia import Materia
    m = Materia(tenant_id=tenant_id, codigo=codigo, nombre=nombre)
    db_session.add(m)
    await db_session.flush()
    return m


async def _create_dictado(db_session, tenant_id, materia_id, carrera_id, cohorte_id, nombre="Programación I - Python"):
    from app.models.dictado import Dictado
    d = Dictado(tenant_id=tenant_id, materia_id=materia_id, carrera_id=carrera_id, cohorte_id=cohorte_id, nombre=nombre)
    db_session.add(d)
    await db_session.flush()
    return d


class TestCarreraCRUD:
    async def test_create_carrera(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/carreras/",
            json={"codigo": "TUPAD", "nombre": "Tecnicatura en Programación"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["codigo"] == "TUPAD"
        assert data["nombre"] == "Tecnicatura en Programación"
        assert data["estado"] == "Activa"
        assert data["tenant_id"] == str(tenant.id)

    async def test_list_carreras(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        await _create_carrera(db_session, tenant.id, "TUPAD", "Tecnicatura")
        await _create_carrera(db_session, tenant.id, "TSP", "Tecnicatura Superior")
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            "/api/v1/admin/carreras/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2

    async def test_get_carrera(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            f"/api/v1/admin/carreras/{carrera.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["codigo"] == "PROG"

    async def test_get_carrera_not_found(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            f"/api/v1/admin/carreras/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_update_carrera(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.put(
            f"/api/v1/admin/carreras/{carrera.id}",
            json={"nombre": "Programación Actualizada"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Programación Actualizada"

    async def test_delete_carrera_soft(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.delete(
            f"/api/v1/admin/carreras/{carrera.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        resp_get = await client.get(
            f"/api/v1/admin/carreras/{carrera.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_get.status_code == 404

    async def test_codigo_duplicado_mismo_tenant(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        await _create_carrera(db_session, tenant.id, "PROG")
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/carreras/",
            json={"codigo": "PROG", "nombre": "Otra Programación"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    async def test_mismo_codigo_distinto_tenant(self, client, db_session):
        user_a, tenant_a, _ = await _setup_admin_user(db_session)
        user_b, tenant_b, _ = await _setup_admin_user(db_session)
        await _create_carrera(db_session, tenant_a.id, "PROG")
        token_b = create_access_token(user_b.id, tenant_b.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/carreras/",
            json={"codigo": "PROG", "nombre": "Programación en otro tenant"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 201

    async def test_soft_delete_not_listed(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        c1 = await _create_carrera(db_session, tenant.id, "C1")
        c2 = await _create_carrera(db_session, tenant.id, "C2")
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        await client.delete(
            f"/api/v1/admin/carreras/{c1.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = await client.get(
            "/api/v1/admin/carreras/",
            headers={"Authorization": f"Bearer {token}"},
        )
        codigos = [c["codigo"] for c in resp.json()]
        assert "C1" not in codigos
        assert "C2" in codigos


class TestCohorteCRUD:
    async def test_create_cohorte(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/cohortes/",
            json={"carrera_id": str(carrera.id), "nombre": "MAR-2026", "anio": 2026},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["nombre"] == "MAR-2026"
        assert resp.json()["anio"] == 2026

    async def test_list_cohortes_by_carrera(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        await _create_cohorte(db_session, tenant.id, carrera.id, "C1")
        await _create_cohorte(db_session, tenant.id, carrera.id, "C2")
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            f"/api/v1/admin/cohortes/?carrera_id={carrera.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_get_cohorte(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            f"/api/v1/admin/cohortes/{cohorte.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "MAR-2026"

    async def test_update_cohorte(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.put(
            f"/api/v1/admin/cohortes/{cohorte.id}",
            json={"nombre": "ABR-2026"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "ABR-2026"

    async def test_delete_cohorte_soft(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.delete(
            f"/api/v1/admin/cohortes/{cohorte.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        resp_get = await client.get(
            f"/api/v1/admin/cohortes/{cohorte.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_get.status_code == 404

    async def test_cohorte_carrera_inactiva_error(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        carrera.estado = "Inactiva"
        await db_session.flush()
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/cohortes/",
            json={"carrera_id": str(carrera.id), "nombre": "MAR-2026", "anio": 2026},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_nombre_duplicado_misma_carrera(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        await _create_cohorte(db_session, tenant.id, carrera.id, "MAR-2026")
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/cohortes/",
            json={"carrera_id": str(carrera.id), "nombre": "MAR-2026", "anio": 2026},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409


class TestMateriaCRUD:
    async def test_create_materia(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/materias/",
            json={"codigo": "PROG_I", "nombre": "Programación I"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["codigo"] == "PROG_I"
        assert resp.json()["estado"] == "Activa"

    async def test_list_materias(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        await _create_materia(db_session, tenant.id, "M1")
        await _create_materia(db_session, tenant.id, "M2")
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            "/api/v1/admin/materias/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    async def test_get_materia(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            f"/api/v1/admin/materias/{materia.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["codigo"] == "PROG_I"

    async def test_update_materia(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.put(
            f"/api/v1/admin/materias/{materia.id}",
            json={"nombre": "Programación I Actualizada"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Programación I Actualizada"

    async def test_delete_materia_soft(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.delete(
            f"/api/v1/admin/materias/{materia.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        resp_get = await client.get(
            f"/api/v1/admin/materias/{materia.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_get.status_code == 404

    async def test_codigo_duplicado_materia(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        await _create_materia(db_session, tenant.id, "PROG_I")
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/materias/",
            json={"codigo": "PROG_I", "nombre": "Otra Programación"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409


class TestDictadoCRUD:
    async def test_create_dictado(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        materia = await _create_materia(db_session, tenant.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/dictados/",
            json={
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "nombre": "Programación I - Python",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["nombre"] == "Programación I - Python"

    async def test_dictado_nombre_descriptivo(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        materia = await _create_materia(db_session, tenant.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/dictados/",
            json={
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "nombre": "Nombre Distinto a la Materia",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["nombre"] == "Nombre Distinto a la Materia"

    async def test_list_dictados(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        materia = await _create_materia(db_session, tenant.id)
        await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            "/api/v1/admin/dictados/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_list_dictados_by_materia(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        c1 = await _create_cohorte(db_session, tenant.id, carrera.id, "C1")
        c2 = await _create_cohorte(db_session, tenant.id, carrera.id, "C2")
        m1 = await _create_materia(db_session, tenant.id, "M1")
        m2 = await _create_materia(db_session, tenant.id, "M2")
        await _create_dictado(db_session, tenant.id, m1.id, carrera.id, c1.id, "D1")
        await _create_dictado(db_session, tenant.id, m1.id, carrera.id, c2.id, "D2")
        await _create_dictado(db_session, tenant.id, m2.id, carrera.id, c1.id, "D3")
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            f"/api/v1/admin/dictados/?materia_id={m1.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_get_dictado(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        materia = await _create_materia(db_session, tenant.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            f"/api/v1/admin/dictados/{dictado.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_update_dictado(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        materia = await _create_materia(db_session, tenant.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.put(
            f"/api/v1/admin/dictados/{dictado.id}",
            json={"nombre": "Nombre Actualizado"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Nombre Actualizado"

    async def test_delete_dictado_soft(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        materia = await _create_materia(db_session, tenant.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.delete(
            f"/api/v1/admin/dictados/{dictado.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        resp_get = await client.get(
            f"/api/v1/admin/dictados/{dictado.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_get.status_code == 404

    async def test_combinacion_materia_cohorte_duplicada(self, client, db_session):
        user, tenant, _ = await _setup_admin_user(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        materia = await _create_materia(db_session, tenant.id)
        await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        token = create_access_token(user.id, tenant.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.post(
            "/api/v1/admin/dictados/",
            json={
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "nombre": "Intento Duplicado",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409


class TestMultitenant:
    async def test_aislamiento_carreras(self, client, db_session):
        user_a, tenant_a, _ = await _setup_admin_user(db_session)
        user_b, tenant_b, _ = await _setup_admin_user(db_session)

        await _create_carrera(db_session, tenant_a.id, "TUPAD")
        await _create_carrera(db_session, tenant_b.id, "TSP")

        token_a = create_access_token(user_a.id, tenant_a.id, ["ESTRUCTURA_ADMIN"])

        resp = await client.get(
            "/api/v1/admin/carreras/",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        codigos = [c["codigo"] for c in resp.json()]
        assert "TUPAD" in codigos
        assert "TSP" not in codigos


class TestPermissions:
    async def test_403_sin_permiso(self, client, db_session):
        user, tenant = await _setup_user_without_permission(db_session)
        token = create_access_token(user.id, tenant.id, ["NO_PERM"])

        endpoints = [
            ("POST", "/api/v1/admin/carreras/", {"codigo": "X", "nombre": "X"}),
            ("GET", "/api/v1/admin/carreras/", None),
            ("POST", "/api/v1/admin/materias/", {"codigo": "X", "nombre": "X"}),
            ("GET", "/api/v1/admin/materias/", None),
            ("POST", "/api/v1/admin/cohortes/", {"carrera_id": str(uuid.uuid4()), "nombre": "X", "anio": 2026}),
            ("GET", "/api/v1/admin/cohortes/", None),
            ("POST", "/api/v1/admin/dictados/", {
                "materia_id": str(uuid.uuid4()),
                "carrera_id": str(uuid.uuid4()),
                "cohorte_id": str(uuid.uuid4()),
                "nombre": "X",
            }),
            ("GET", "/api/v1/admin/dictados/", None),
        ]

        for method, path, body in endpoints:
            if method == "POST":
                resp = await client.post(path, json=body, headers={"Authorization": f"Bearer {token}"})
            else:
                resp = await client.get(path, headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 403, f"{method} {path} returned {resp.status_code}"

    async def test_401_sin_token(self, client, db_session):
        endpoints = [
            ("GET", "/api/v1/admin/carreras/"),
            ("POST", "/api/v1/admin/carreras/"),
            ("GET", "/api/v1/admin/cohortes/"),
            ("GET", "/api/v1/admin/materias/"),
            ("GET", "/api/v1/admin/dictados/"),
        ]

        for method, path in endpoints:
            if method == "GET":
                resp = await client.get(path)
            else:
                resp = await client.post(path, json={})
            assert resp.status_code in (401, 403), f"{method} {path} returned {resp.status_code}"
