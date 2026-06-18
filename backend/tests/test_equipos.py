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
    tenant = Tenant(name="EquiposTest", code=f"EQT-{uuid.uuid4().hex[:6].upper()}")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"admin-eq-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Admin",
        apellido="Equipos",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name=f"EQ_ADMIN_{uuid.uuid4().hex[:6]}", tenant_id=tenant.id)
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
    tenant = Tenant(name="NoPermEq", code=f"NPE-{uuid.uuid4().hex[:6].upper()}")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"np-eq-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="NoPerm",
        apellido="Equipos",
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
        email=f"prof-eq-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Profesor",
        apellido="Equipos",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(prof)
    await db_session.flush()
    return prof


async def _create_carrera(db_session, tenant_id):
    c = Carrera(tenant_id=tenant_id, codigo=f"CARR-EQ-{uuid.uuid4().hex[:6]}", nombre="Carrera Equipos Test")
    db_session.add(c)
    await db_session.flush()
    return c


async def _create_materia(db_session, tenant_id):
    m = Materia(tenant_id=tenant_id, codigo=f"MAT-EQ-{uuid.uuid4().hex[:6]}", nombre="Materia Equipos Test")
    db_session.add(m)
    await db_session.flush()
    return m


async def _create_cohorte(db_session, tenant_id, carrera_id):
    c = Cohorte(tenant_id=tenant_id, carrera_id=carrera_id, nombre=f"COH-EQ-{uuid.uuid4().hex[:6]}", anio=2026)
    db_session.add(c)
    await db_session.flush()
    return c


async def _create_dictado(db_session, tenant_id, materia_id, carrera_id, cohorte_id, nombre="Dictado Test"):
    d = Dictado(
        tenant_id=tenant_id,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        nombre=nombre,
    )
    db_session.add(d)
    await db_session.flush()
    return d


async def _create_asignacion(db_session, tenant_id, usuario_id, dictado_id, rol="PROFESOR"):
    # Load dictado for materia/carrera/cohorte IDs
    from sqlalchemy import select
    from app.models.dictado import Dictado
    stmt = select(Dictado).where(Dictado.id == dictado_id)
    result = await db_session.execute(stmt)
    dictado = result.scalar_one_or_none()

    a = Asignacion(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        rol=rol,
        dictado_id=dictado_id,
        materia_id=dictado.materia_id if dictado else None,
        carrera_id=dictado.carrera_id if dictado else None,
        cohorte_id=dictado.cohorte_id if dictado else None,
        desde=date.today(),
        hasta=date.today() + timedelta(days=365),
    )
    db_session.add(a)
    await db_session.flush()
    return a


async def _create_asignacion_simple(db_session, tenant_id, usuario_id, rol="PROFESOR"):
    a = Asignacion(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        rol=rol,
        desde=date.today(),
        hasta=date.today() + timedelta(days=365),
    )
    db_session.add(a)
    await db_session.flush()
    return a


class TestMisEquipos:
    """Tests para GET /api/v1/equipos/mis-equipos"""

    async def test_mis_equipos_returns_only_own(self, client, db_session):
        """6.1: mis equipos devuelve solo asignaciones del usuario autenticado"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        # Create another user
        otro_user = await _create_profesor(db_session, tenant.id)

        # Create dictado
        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)

        # Asignacion for admin_user
        await _create_asignacion(db_session, tenant.id, admin_user.id, dictado.id)
        # Asignacion for otro_user
        await _create_asignacion(db_session, tenant.id, otro_user.id, dictado.id)

        resp = await client.get(
            "/api/v1/equipos/mis-equipos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["usuario_id"] == str(admin_user.id)

    async def test_mis_equipos_sin_asignaciones(self, client, db_session):
        """6.2: mis equipos sin asignaciones devuelve lista vacía"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        resp = await client.get(
            "/api/v1/equipos/mis-equipos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data == []

    async def test_mis_equipos_filtro_por_rol(self, client, db_session):
        """6.3: mis equipos con filtro por rol"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        # Create dictado
        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)

        await _create_asignacion(db_session, tenant.id, admin_user.id, dictado.id, rol="PROFESOR")
        await _create_asignacion(db_session, tenant.id, admin_user.id, dictado.id, rol="TUTOR")

        resp = await client.get(
            "/api/v1/equipos/mis-equipos?rol=PROFESOR",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["rol"] == "PROFESOR"

    async def test_mis_equipos_sin_token(self, client, db_session):
        """Sin autenticación retorna 401"""
        resp = await client.get("/api/v1/equipos/mis-equipos")
        assert resp.status_code == 401

    async def test_mis_equipos_incluye_dictado_info(self, client, db_session):
        """Mis equipos incluye datos del dictado (materia_nombre, carrera_nombre, cohorte_nombre)"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)

        await _create_asignacion(db_session, tenant.id, admin_user.id, dictado.id)

        resp = await client.get(
            "/api/v1/equipos/mis-equipos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["dictado"] is not None
        assert data[0]["dictado"]["materia_nombre"] == "Materia Equipos Test"
        assert data[0]["dictado"]["carrera_nombre"] == "Carrera Equipos Test"
        assert data[0]["dictado"]["cohorte_nombre"] is not None


class TestListAsignacionesEquipos:
    """Tests para GET /api/v1/equipos/asignaciones"""

    async def test_list_asignaciones_filtro_dictado(self, client, db_session):
        """Filtrar asignaciones por dictado_id"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        d1 = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id, nombre="Dictado 1")
        d2 = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id, nombre="Dictado 2")
        prof = await _create_profesor(db_session, tenant.id)

        await _create_asignacion(db_session, tenant.id, prof.id, d1.id)
        await _create_asignacion(db_session, tenant.id, prof.id, d2.id)

        resp = await client.get(
            f"/api/v1/equipos/asignaciones?dictado_id={d1.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["dictado_id"] == str(d1.id)

    async def test_list_asignaciones_filtro_carrera(self, client, db_session):
        """Filtrar asignaciones por carrera_id"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        c1 = await _create_carrera(db_session, tenant.id)
        c2 = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        co1 = await _create_cohorte(db_session, tenant.id, c1.id)
        co2 = await _create_cohorte(db_session, tenant.id, c2.id)
        d1 = await _create_dictado(db_session, tenant.id, materia.id, c1.id, co1.id)
        d2 = await _create_dictado(db_session, tenant.id, materia.id, c2.id, co2.id)
        prof = await _create_profesor(db_session, tenant.id)

        await _create_asignacion(db_session, tenant.id, prof.id, d1.id)
        await _create_asignacion(db_session, tenant.id, prof.id, d2.id)

        resp = await client.get(
            f"/api/v1/equipos/asignaciones?carrera_id={c1.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["carrera_id"] == str(c1.id)

    async def test_list_asignaciones_filtro_rol(self, client, db_session):
        """Filtrar asignaciones por rol"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        prof = await _create_profesor(db_session, tenant.id)

        await _create_asignacion(db_session, tenant.id, prof.id, dictado.id, rol="PROFESOR")
        await _create_asignacion(db_session, tenant.id, prof.id, dictado.id, rol="TUTOR")

        resp = await client.get(
            f"/api/v1/equipos/asignaciones?rol=PROFESOR",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["rol"] == "PROFESOR"


class TestAsignacionMasiva:
    """Tests para POST /api/v1/equipos/masiva"""

    async def test_masiva_exitosa(self, client, db_session):
        """6.4: asignación masiva exitosa"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        prof1 = await _create_profesor(db_session, tenant.id)
        prof2 = await _create_profesor(db_session, tenant.id)

        resp = await client.post(
            "/api/v1/equipos/masiva",
            json={
                "dictado_id": str(dictado.id),
                "rol": "PROFESOR",
                "desde": str(date.today()),
                "hasta": str(date.today() + timedelta(days=365)),
                "usuario_ids": [str(prof1.id), str(prof2.id)],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 2
        assert data[0]["rol"] == "PROFESOR"

    async def test_masiva_usuario_duplicado(self, client, db_session):
        """6.5: asignación masiva con usuario duplicado → 422 + no se crea nada"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        prof = await _create_profesor(db_session, tenant.id)

        resp = await client.post(
            "/api/v1/equipos/masiva",
            json={
                "dictado_id": str(dictado.id),
                "rol": "PROFESOR",
                "desde": str(date.today()),
                "usuario_ids": [str(prof.id), str(prof.id)],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_masiva_usuario_invalido(self, client, db_session):
        """6.6: asignación masiva con usuario inválido → 422"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)

        fake_id = uuid.uuid4()
        resp = await client.post(
            "/api/v1/equipos/masiva",
            json={
                "dictado_id": str(dictado.id),
                "rol": "PROFESOR",
                "desde": str(date.today()),
                "usuario_ids": [str(fake_id)],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
        assert "no encontrado" in resp.json()["detail"].lower()

    async def test_masiva_sin_permiso(self, client, db_session):
        """6.7: asignación masiva sin permiso → 403"""
        user, tenant = await _setup_no_perm_user(db_session)
        token = create_access_token(user.id, tenant.id, ["NO_PERM"])

        resp = await client.post(
            "/api/v1/equipos/masiva",
            json={
                "dictado_id": str(uuid.uuid4()),
                "rol": "PROFESOR",
                "desde": str(date.today()),
                "usuario_ids": [str(uuid.uuid4())],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_masiva_rol_invalido(self, client, db_session):
        """Rol inválido → 422"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        prof = await _create_profesor(db_session, tenant.id)

        resp = await client.post(
            "/api/v1/equipos/masiva",
            json={
                "dictado_id": str(dictado.id),
                "rol": "INVALIDO",
                "desde": str(date.today()),
                "usuario_ids": [str(prof.id)],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestClonarEquipo:
    """Tests para POST /api/v1/equipos/clonar"""

    async def test_clonar_exitoso(self, client, db_session):
        """6.8: clonar equipo exitoso"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        d_origen = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id, nombre="Origen")
        d_destino = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id, nombre="Destino")
        prof1 = await _create_profesor(db_session, tenant.id)
        prof2 = await _create_profesor(db_session, tenant.id)

        await _create_asignacion(db_session, tenant.id, prof1.id, d_origen.id)
        await _create_asignacion(db_session, tenant.id, prof2.id, d_origen.id)

        resp = await client.post(
            "/api/v1/equipos/clonar",
            json={
                "dictado_origen_id": str(d_origen.id),
                "dictado_destino_id": str(d_destino.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 2
        assert data[0]["dictado_id"] == str(d_destino.id)

    async def test_clonar_destino_ocupado(self, client, db_session):
        """6.9: clonar con destino ocupado → 409"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        d_origen = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        d_destino = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        prof = await _create_profesor(db_session, tenant.id)

        await _create_asignacion(db_session, tenant.id, prof.id, d_origen.id)
        await _create_asignacion(db_session, tenant.id, prof.id, d_destino.id)

        resp = await client.post(
            "/api/v1/equipos/clonar",
            json={
                "dictado_origen_id": str(d_origen.id),
                "dictado_destino_id": str(d_destino.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    async def test_clonar_forzado(self, client, db_session):
        """6.10: clonar forzado con destino ocupado → 201"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        d_origen = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        d_destino = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        prof = await _create_profesor(db_session, tenant.id)

        await _create_asignacion(db_session, tenant.id, prof.id, d_origen.id)
        await _create_asignacion(db_session, tenant.id, prof.id, d_destino.id)

        resp = await client.post(
            "/api/v1/equipos/clonar",
            json={
                "dictado_origen_id": str(d_origen.id),
                "dictado_destino_id": str(d_destino.id),
                "force": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 1

    async def test_clonar_origen_sin_asignaciones(self, client, db_session):
        """6.11: clonar con origen sin asignaciones → lista vacía"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        d_origen = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        d_destino = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)

        resp = await client.post(
            "/api/v1/equipos/clonar",
            json={
                "dictado_origen_id": str(d_origen.id),
                "dictado_destino_id": str(d_destino.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data == []

    async def test_clonar_sin_permiso(self, client, db_session):
        """6.12: clonar sin permiso → 403"""
        user, tenant = await _setup_no_perm_user(db_session)
        token = create_access_token(user.id, tenant.id, ["NO_PERM"])

        resp = await client.post(
            "/api/v1/equipos/clonar",
            json={
                "dictado_origen_id": str(uuid.uuid4()),
                "dictado_destino_id": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestModificarVigencia:
    """Tests para PUT /api/v1/equipos/{dictado_id}/vigencia"""

    async def test_vigencia_exitosa(self, client, db_session):
        """6.13: modificar vigencia general exitoso"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        prof = await _create_profesor(db_session, tenant.id)

        await _create_asignacion(db_session, tenant.id, prof.id, dictado.id)
        await _create_asignacion(db_session, tenant.id, prof.id, dictado.id, rol="TUTOR")

        new_desde = date.today() + timedelta(days=10)
        new_hasta = date.today() + timedelta(days=200)
        resp = await client.put(
            f"/api/v1/equipos/{dictado.id}/vigencia",
            json={
                "desde": str(new_desde),
                "hasta": str(new_hasta),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["actualizadas"] == 2

    async def test_vigencia_sin_asignaciones(self, client, db_session):
        """Dictado sin asignaciones → 200 con actualizadas=0"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)

        resp = await client.put(
            f"/api/v1/equipos/{dictado.id}/vigencia",
            json={
                "desde": str(date.today()),
                "hasta": str(date.today() + timedelta(days=200)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["actualizadas"] == 0

    async def test_vigencia_fecha_invalida(self, client, db_session):
        """6.14: modificar vigencia con fecha inválida → 422"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)

        resp = await client.put(
            f"/api/v1/equipos/{dictado.id}/vigencia",
            json={
                "desde": str(date.today() + timedelta(days=30)),
                "hasta": str(date.today()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestExportarEquipo:
    """Tests para GET /api/v1/equipos/{dictado_id}/exportar"""

    async def test_exportar_csv(self, client, db_session):
        """6.15: exportar equipo genera CSV"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        prof = await _create_profesor(db_session, tenant.id)

        await _create_asignacion(db_session, tenant.id, prof.id, dictado.id)

        resp = await client.get(
            f"/api/v1/equipos/{dictado.id}/exportar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        content = resp.text
        assert "docente_id" in content
        assert "rol" in content
        assert "PROFESOR" in content

    async def test_exportar_csv_sin_datos(self, client, db_session):
        """6.16: exportar equipo sin datos genera CSV con solo headers"""
        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)

        resp = await client.get(
            f"/api/v1/equipos/{dictado.id}/exportar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        content = resp.text
        assert "docente_id" in content
        lines = content.strip().split("\n")
        assert len(lines) == 1  # Only header

    async def test_exportar_403(self, client, db_session):
        """Exportar sin permiso → 403"""
        user, tenant = await _setup_no_perm_user(db_session)
        token = create_access_token(user.id, tenant.id, ["NO_PERM"])

        resp = await client.get(
            f"/api/v1/equipos/{uuid.uuid4()}/exportar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestAuditLog:
    """Tests para audit logging"""

    async def test_audit_masiva(self, client, db_session):
        """6.17: audit log generado en asignación masiva"""
        from app.models.audit_log import AuditLog
        from sqlalchemy import select

        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        prof = await _create_profesor(db_session, tenant.id)

        await client.post(
            "/api/v1/equipos/masiva",
            json={
                "dictado_id": str(dictado.id),
                "rol": "PROFESOR",
                "desde": str(date.today()),
                "usuario_ids": [str(prof.id)],
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        stmt = select(AuditLog).where(
            AuditLog.actor_id == admin_user.id,
            AuditLog.accion == "ASIGNACION_MODIFICAR",
        )
        result = await db_session.execute(stmt)
        logs = result.scalars().all()
        assert len(logs) >= 1
        detalle = logs[-1].detalle
        assert detalle["operacion"] == "asignacion_masiva"
        assert detalle["cantidad"] == 1

    async def test_audit_clonar(self, client, db_session):
        """Audit log generado en clonar equipo"""
        from app.models.audit_log import AuditLog
        from sqlalchemy import select

        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        d_origen = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        d_destino = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)
        prof = await _create_profesor(db_session, tenant.id)
        await _create_asignacion(db_session, tenant.id, prof.id, d_origen.id)

        await client.post(
            "/api/v1/equipos/clonar",
            json={
                "dictado_origen_id": str(d_origen.id),
                "dictado_destino_id": str(d_destino.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        stmt = select(AuditLog).where(
            AuditLog.actor_id == admin_user.id,
            AuditLog.accion == "ASIGNACION_MODIFICAR",
        )
        result = await db_session.execute(stmt)
        logs = result.scalars().all()
        clonar_logs = [l for l in logs if l.detalle and l.detalle.get("operacion") == "clonar_equipo"]
        assert len(clonar_logs) >= 1

    async def test_audit_vigencia(self, client, db_session):
        """Audit log generado en modificar vigencia"""
        from app.models.audit_log import AuditLog
        from sqlalchemy import select

        admin_user, tenant = await _setup_admin(db_session)
        token = create_access_token(admin_user.id, tenant.id, ["EQ_ADMIN"])

        carrera = await _create_carrera(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        dictado = await _create_dictado(db_session, tenant.id, materia.id, carrera.id, cohorte.id)

        await client.put(
            f"/api/v1/equipos/{dictado.id}/vigencia",
            json={
                "desde": str(date.today()),
                "hasta": str(date.today() + timedelta(days=200)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        stmt = select(AuditLog).where(
            AuditLog.actor_id == admin_user.id,
            AuditLog.accion == "ASIGNACION_MODIFICAR",
        )
        result = await db_session.execute(stmt)
        logs = result.scalars().all()
        vig_logs = [l for l in logs if l.detalle and l.detalle.get("operacion") == "modificar_vigencia"]
        assert len(vig_logs) >= 1
