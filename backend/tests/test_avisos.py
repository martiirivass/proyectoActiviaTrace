"""Tests for Avisos module.

Strict TDD: RED -> GREEN -> REFACTOR.
Full stack: Router -> Service -> Repository -> DB.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.core.security import PasswordService, create_access_token
from app.models import (
    Asignacion,
    Carrera,
    Cohorte,
    Materia,
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
    UserTenant,
)
from app.models.aviso import Aviso

pytestmark = pytest.mark.asyncio


# ===== Helpers =====


async def _setup_tenant_with_user(db_session, role_name="COORDINADOR", extra_perms=None):
    """Setup tenant with user having avisos:publicar permission."""
    code = f"AV{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Avisos Test {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"avisos-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Avisos",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name=role_name, tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    from sqlalchemy import select

    perm_names = extra_perms or ["avisos:publicar"]
    for pname in perm_names:
        stmt = select(Permission).where(Permission.name == pname)
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm is None:
            mod, act = pname.split(":")
            perm = Permission(name=pname, module=mod, action=act)
            db_session.add(perm)
            await db_session.flush()

        rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

    return user, tenant, role


async def _setup_second_tenant(db_session):
    """Setup a second tenant with user for isolation tests."""
    from sqlalchemy import select

    code = f"AV2{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Avisos Test B {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"avisos-b-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="AvisosB",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name="COORDINADOR", tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    stmt = select(Permission).where(Permission.name == "avisos:publicar")
    result = await db_session.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        perm = Permission(name="avisos:publicar", module="avisos", action="publicar")
        db_session.add(perm)
        await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
    db_session.add(rp)
    await db_session.flush()

    return user, tenant, role


async def _setup_role_user(db_session, tenant, role_name, extra_perms=None):
    """Setup a user with a specific role in the given tenant."""
    role = Role(name=role_name, tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"{role_name.lower()}-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre=role_name,
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    from sqlalchemy import select

    perm_names = extra_perms or []
    for pname in perm_names:
        stmt = select(Permission).where(Permission.name == pname)
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm is None:
            mod, act = pname.split(":")
            perm = Permission(name=pname, module=mod, action=act)
            db_session.add(perm)
            await db_session.flush()

        rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

    return user, role


async def _create_materia(db_session, tenant_id):
    m = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:6].upper()}",
        nombre="Materia Avisos Test",
    )
    db_session.add(m)
    await db_session.flush()
    return m


async def _create_carrera(db_session, tenant_id):
    c = Carrera(
        tenant_id=tenant_id,
        codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
        nombre="Carrera Test",
    )
    db_session.add(c)
    await db_session.flush()
    return c


async def _create_cohorte(db_session, tenant_id, carrera_id):
    coh = Cohorte(
        tenant_id=tenant_id,
        carrera_id=carrera_id,
        nombre=f"COH-{uuid.uuid4().hex[:6].upper()}",
        anio=2026,
    )
    db_session.add(coh)
    await db_session.flush()
    return coh


async def _create_asignacion(db_session, tenant_id, usuario_id, materia_id=None, cohorte_id=None, rol="ALUMNO"):
    a = Asignacion(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        rol=rol,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        desde=datetime.now(timezone.utc).date(),
    )
    db_session.add(a)
    await db_session.flush()
    return a


def _make_token(user, tenant, roles=None):
    return create_access_token(user.id, tenant.id, roles or ["COORDINADOR"])


async def _create_aviso(db_session, tenant_id, **overrides):
    now = datetime.now(timezone.utc)
    defaults = {
        "tenant_id": tenant_id,
        "alcance": "Global",
        "severidad": "Info",
        "titulo": "Aviso de prueba",
        "cuerpo": "Cuerpo del aviso de prueba",
        "inicio_en": now - timedelta(hours=1),
        "fin_en": now + timedelta(days=7),
        "orden": 0,
        "activo": True,
        "requiere_ack": False,
    }
    defaults.update(overrides)
    aviso = Aviso(**defaults)
    db_session.add(aviso)
    await db_session.flush()
    await db_session.refresh(aviso)
    return aviso


# ===== Fixtures =====


class TestSetup:
    """8.1: Fixtures work correctly"""

    async def test_setup_creates_tenant_and_user(self, client, db_session):
        user, tenant, role = await _setup_tenant_with_user(db_session)
        assert user.id is not None
        assert tenant.id is not None
        assert role is not None


class TestCrearAviso:
    """8.2-8.3: Crear aviso"""

    async def test_crear_aviso_global_con_ack(self, client, db_session):
        """8.2: Crear aviso global con ack obligatorio -> 201"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        now = datetime.now(timezone.utc)

        resp = await client.post(
            "/api/v1/avisos/",
            json={
                "alcance": "Global",
                "severidad": "Info",
                "titulo": "Aviso importante",
                "cuerpo": "Este es un aviso importante",
                "inicio_en": now.isoformat(),
                "fin_en": (now + timedelta(days=7)).isoformat(),
                "orden": 1,
                "activo": True,
                "requiere_ack": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["titulo"] == "Aviso importante"
        assert data["requiere_ack"] == True
        assert data["alcance"] == "Global"

    async def test_crear_aviso_sin_cuerpo_422(self, client, db_session):
        """8.3: Crear aviso sin cuerpo -> 422"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        now = datetime.now(timezone.utc)

        resp = await client.post(
            "/api/v1/avisos/",
            json={
                "alcance": "Global",
                "severidad": "Info",
                "titulo": "Aviso sin cuerpo",
                "cuerpo": "",
                "inicio_en": now.isoformat(),
                "fin_en": (now + timedelta(days=7)).isoformat(),
                "orden": 1,
                "activo": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestEditarAviso:
    """8.4: Editar aviso"""

    async def test_editar_aviso_existente(self, client, db_session):
        """8.4: Editar aviso existente -> 200"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        now = datetime.now(timezone.utc)

        aviso = await _create_aviso(db_session, tenant.id)

        resp = await client.patch(
            f"/api/v1/avisos/{aviso.id}",
            json={
                "titulo": "Título editado",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["titulo"] == "Título editado"


class TestEliminarAviso:
    """8.5: Soft delete de aviso"""

    async def test_soft_delete_aviso(self, client, db_session):
        """8.5: Eliminar aviso -> 204 y desaparece de listados"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        now = datetime.now(timezone.utc)

        aviso = await _create_aviso(db_session, tenant.id)

        resp_delete = await client.delete(
            f"/api/v1/avisos/{aviso.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_delete.status_code == 204

        # Verify it no longer appears
        resp_list = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_list.status_code == 200
        data = resp_list.json()
        ids = [item["id"] for item in data["items"]]
        assert str(aviso.id) not in ids


class TestVisibilidadCoordinador:
    """8.6: COORDINADOR ve todos los avisos del tenant"""

    async def test_coordinador_ve_todos_los_avisos(self, client, db_session):
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)

        await _create_aviso(db_session, tenant.id, titulo="Aviso Global")
        await _create_aviso(db_session, tenant.id, titulo="Aviso Inactivo", activo=False)

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2


class TestVisibilidadAlumno:
    """8.7: ALUMNO ve solo avisos globales, de su cohorte y de su rol"""

    async def test_alumno_ve_solo_avisos_aplicables(self, client, db_session):
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        alumno, _ = await _setup_role_user(db_session, tenant, "ALUMNO", extra_perms=["avisos:confirmar"])
        token = _make_token(alumno, tenant, ["ALUMNO"])

        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        otro_cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        await _create_asignacion(db_session, tenant.id, alumno.id, cohorte_id=cohorte.id, rol="ALUMNO")

        await _create_aviso(db_session, tenant.id, titulo="Global", alcance="Global")
        await _create_aviso(db_session, tenant.id, titulo="De mi cohorte", alcance="PorCohorte", cohorte_id=cohorte.id)
        await _create_aviso(db_session, tenant.id, titulo="De otro cohorte", alcance="PorCohorte", cohorte_id=otro_cohorte.id)
        await _create_aviso(db_session, tenant.id, titulo="Para mi rol", alcance="PorRol", rol_destino="ALUMNO")

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        titulos = [item["titulo"] for item in data["items"]]
        assert "Global" in titulos
        assert "De mi cohorte" in titulos
        assert "De otro cohorte" not in titulos
        assert "Para mi rol" in titulos


class TestVisibilidadProfesor:
    """8.8: PROFESOR ve avisos de su materia"""

    async def test_profesor_ve_avisos_su_materia(self, client, db_session):
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        profesor, _ = await _setup_role_user(db_session, tenant, "PROFESOR", extra_perms=["avisos:publicar"])
        token = _make_token(profesor, tenant, ["PROFESOR"])

        materia_a = await _create_materia(db_session, tenant.id)
        materia_b = await _create_materia(db_session, tenant.id)
        await _create_asignacion(db_session, tenant.id, profesor.id, materia_id=materia_a.id, rol="PROFESOR")

        await _create_aviso(db_session, tenant.id, titulo="Global", alcance="Global")
        await _create_aviso(db_session, tenant.id, titulo="Mi materia", alcance="PorMateria", materia_id=materia_a.id)
        await _create_aviso(db_session, tenant.id, titulo="Otra materia", alcance="PorMateria", materia_id=materia_b.id)
        await _create_aviso(db_session, tenant.id, titulo="Para mi rol", alcance="PorRol", rol_destino="PROFESOR")

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        titulos = [item["titulo"] for item in data["items"]]
        assert "Global" in titulos
        assert "Mi materia" in titulos
        assert "Otra materia" not in titulos
        assert "Para mi rol" in titulos


class TestVigenciaAviso:
    """8.9: Aviso fuera de vigencia no se muestra"""

    async def test_aviso_fuera_de_vigencia_no_visible(self, client, db_session):
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        alumno, _ = await _setup_role_user(db_session, tenant, "ALUMNO")
        token = _make_token(alumno, tenant, ["ALUMNO"])
        now = datetime.now(timezone.utc)

        await _create_aviso(db_session, tenant.id, titulo="Futuro", inicio_en=now + timedelta(days=10), fin_en=now + timedelta(days=20))
        await _create_aviso(db_session, tenant.id, titulo="Vencido", inicio_en=now - timedelta(days=20), fin_en=now - timedelta(days=10))
        await _create_aviso(db_session, tenant.id, titulo="Vigente", inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7))

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        titulos = [item["titulo"] for item in data["items"]]
        assert "Vigente" in titulos
        assert "Futuro" not in titulos
        assert "Vencido" not in titulos


class TestAvisoInactivo:
    """8.10: Aviso inactivo no se muestra"""

    async def test_aviso_inactivo_no_visible(self, client, db_session):
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        alumno, _ = await _setup_role_user(db_session, tenant, "ALUMNO")
        token = _make_token(alumno, tenant, ["ALUMNO"])

        await _create_aviso(db_session, tenant.id, titulo="Activo")
        await _create_aviso(db_session, tenant.id, titulo="Inactivo", activo=False)

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        titulos = [item["titulo"] for item in data["items"]]
        assert "Activo" in titulos
        assert "Inactivo" not in titulos


class TestAcknowledgment:
    """8.11-8.13: Ack de avisos"""

    async def test_ack_requiere_ack_true_201(self, client, db_session):
        """8.11: Ack de aviso con requiere_ack=true -> 201"""
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        alumno, _ = await _setup_role_user(db_session, tenant, "ALUMNO", extra_perms=["avisos:confirmar"])
        token = _make_token(alumno, tenant, ["ALUMNO"])

        aviso = await _create_aviso(db_session, tenant.id, requiere_ack=True)

        resp = await client.post(
            f"/api/v1/avisos/{aviso.id}/acknowledge",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["aviso_id"] == str(aviso.id)
        assert data["usuario_id"] == str(alumno.id)

    async def test_ack_duplicado_409(self, client, db_session):
        """8.12: Ack duplicado -> 409"""
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        alumno, _ = await _setup_role_user(db_session, tenant, "ALUMNO", extra_perms=["avisos:confirmar"])
        token = _make_token(alumno, tenant, ["ALUMNO"])

        aviso = await _create_aviso(db_session, tenant.id, requiere_ack=True)

        resp1 = await client.post(
            f"/api/v1/avisos/{aviso.id}/acknowledge",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 201

        resp2 = await client.post(
            f"/api/v1/avisos/{aviso.id}/acknowledge",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 409

    async def test_ack_sin_requiere_ack_400(self, client, db_session):
        """8.13: Ack de aviso sin requiere_ack -> 400"""
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        alumno, _ = await _setup_role_user(db_session, tenant, "ALUMNO", extra_perms=["avisos:confirmar"])
        token = _make_token(alumno, tenant, ["ALUMNO"])

        aviso = await _create_aviso(db_session, tenant.id, requiere_ack=False)

        resp = await client.post(
            f"/api/v1/avisos/{aviso.id}/acknowledge",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400


class TestAckExcluyeDeListado:
    """8.14: Aviso confirmado no aparece en listado pendiente"""

    async def test_aviso_confirmado_no_aparece_en_listado(self, client, db_session):
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        alumno, _ = await _setup_role_user(db_session, tenant, "ALUMNO", extra_perms=["avisos:confirmar"])
        token = _make_token(alumno, tenant, ["ALUMNO"])

        aviso = await _create_aviso(db_session, tenant.id, requiere_ack=True, titulo="A confirmar")

        # Before ack: should appear
        resp_before = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_before.status_code == 200
        titulos_before = [item["titulo"] for item in resp_before.json()["items"]]
        assert "A confirmar" in titulos_before

        # Ack
        await client.post(
            f"/api/v1/avisos/{aviso.id}/acknowledge",
            headers={"Authorization": f"Bearer {token}"},
        )

        # After ack: should NOT appear
        resp_after = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_after.status_code == 200
        titulos_after = [item["titulo"] for item in resp_after.json()["items"]]
        assert "A confirmar" not in titulos_after


class TestOrdenPrioridad:
    """8.15: Orden de presentación por prioridad"""

    async def test_orden_por_prioridad(self, client, db_session):
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        token = _make_token(coord, tenant, ["COORDINADOR"])

        await _create_aviso(db_session, tenant.id, titulo="Prioridad 3", orden=3)
        await _create_aviso(db_session, tenant.id, titulo="Prioridad 1", orden=1)
        await _create_aviso(db_session, tenant.id, titulo="Prioridad 2", orden=2)

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        titulos = [item["titulo"] for item in data["items"]]
        # Should be ordered by orden ASC
        idx1 = titulos.index("Prioridad 1")
        idx2 = titulos.index("Prioridad 2")
        idx3 = titulos.index("Prioridad 3")
        assert idx1 < idx2 < idx3


class TestMetricas:
    """8.16-8.17: Métricas de aviso"""

    async def test_metricas_despues_de_ack(self, client, db_session):
        """8.16: Métricas con contadores correctos después de ack"""
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        token = _make_token(coord, tenant)

        aviso = await _create_aviso(db_session, tenant.id, requiere_ack=True)

        # Create alumno and ack
        alumno, _ = await _setup_role_user(db_session, tenant, "ALUMNO", extra_perms=["avisos:confirmar"])
        alumno_token = _make_token(alumno, tenant, ["ALUMNO"])
        await client.post(
            f"/api/v1/avisos/{aviso.id}/acknowledge",
            headers={"Authorization": f"Bearer {alumno_token}"},
        )

        resp = await client.get(
            f"/api/v1/avisos/{aviso.id}/metricas",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["aviso_id"] == str(aviso.id)
        assert data["total_vistos"] >= 1
        assert data["total_confirmados"] >= 1

    async def test_alumno_no_accede_metricas_403(self, client, db_session):
        """8.17: ALUMNO no accede a métricas -> 403"""
        coord, tenant, _ = await _setup_tenant_with_user(db_session)
        alumno, _ = await _setup_role_user(db_session, tenant, "ALUMNO")
        token = _make_token(alumno, tenant, ["ALUMNO"])

        aviso = await _create_aviso(db_session, tenant.id)

        resp = await client.get(
            f"/api/v1/avisos/{aviso.id}/metricas",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestAislamientoTenant:
    """8.18: Aislamiento tenant"""

    async def test_datos_tenant_a_no_visibles_en_tenant_b(self, client, db_session):
        user_a, tenant_a, _ = await _setup_tenant_with_user(db_session)
        user_b, tenant_b, _ = await _setup_second_tenant(db_session)
        token_b = _make_token(user_b, tenant_b)

        aviso_a = await _create_aviso(db_session, tenant_a.id)

        # Try to access aviso from tenant B
        resp = await client.get(
            f"/api/v1/avisos/{aviso_a.id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

        # List should not include tenant A's data
        resp_list = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        data = resp_list.json()
        ids = [item["id"] for item in data["items"]]
        assert str(aviso_a.id) not in ids
