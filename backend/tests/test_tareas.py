"""Tests for Tareas module (C-16).

Strict TDD: RED → GREEN → REFACTOR.
Tests the full stack: Router → Service → Repository → DB.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.models import (
    Materia,
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
    UserTenant,
)
from app.models.tarea import Tarea

pytestmark = pytest.mark.asyncio


# ===== Helpers =====


async def _setup_tenant_and_user(
    db_session,
    role_name: str = "COORDINADOR",
    extra_permissions: list[str] | None = None,
    skip_permissions: list[str] | None = None,
):
    """Setup tenant with user having specific roles and tareas permissions.

    By default gives tareas:gestionar + tareas:admin for COORDINADOR/ADMIN,
    and only tareas:gestionar for other roles.
    """
    code = f"TAR{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Tarea Test {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"tar-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Tarea",
        apellido="Test",
        password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
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

    # Create permissions and assign them
    perms_to_set = extra_permissions or []
    if skip_permissions:
        perms_to_set = [p for p in perms_to_set if p not in skip_permissions]
    else:
        if role_name in ("COORDINADOR", "ADMIN"):
            perms_to_set = ["tareas:gestionar", "tareas:admin"]
        else:
            perms_to_set = ["tareas:gestionar"]

    for perm_name in perms_to_set:
        stmt = select(Permission).where(Permission.name == perm_name)
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm is None:
            module, action = perm_name.split(":", 1)
            perm = Permission(name=perm_name, module=module, action=action)
            db_session.add(perm)
            await db_session.flush()

        rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

    return user, tenant, role


async def _setup_second_tenant(db_session):
    """Setup a second tenant with user for isolation tests."""
    code = f"TAR2{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Tarea Test B {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"tar-b-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="TareaB",
        apellido="Test",
        password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
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

    for perm_name in ["tareas:gestionar", "tareas:admin"]:
        stmt = select(Permission).where(Permission.name == perm_name)
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm is None:
            module, action = perm_name.split(":", 1)
            perm = Permission(name=perm_name, module=module, action=action)
            db_session.add(perm)
            await db_session.flush()
        rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

    return user, tenant


async def _create_materia(db_session, tenant_id):
    m = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:6].upper()}",
        nombre="Materia Tareas Test",
    )
    db_session.add(m)
    await db_session.flush()
    return m


def _make_token(user, tenant, roles=None):
    return create_access_token(user.id, tenant.id, roles or ["COORDINADOR"])


# ===== Tests =====


class TestCrearTarea:
    """8.1-8.2: Crear tareas"""

    async def test_coordinador_crea_tarea_201(self, client, db_session):
        """8.1: COORDINADOR crea tarea → 201, campos correctos"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        # Create a target user (profesor) to assign to
        target_user = User(
            tenant_id=tenant.id,
            email=f"prof-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof",
            apellido="Destino",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(target_user)
        await db_session.flush()

        token = _make_token(user, tenant, ["COORDINADOR"])

        resp = await client.post(
            "/api/v1/tareas/",
            json={
                "asignado_a": str(target_user.id),
                "descripcion": "Preparar informe de avance",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["asignado_a"] == str(target_user.id)
        assert data["asignado_por"] == str(user.id)
        assert data["estado"] == "Pendiente"
        assert data["descripcion"] == "Preparar informe de avance"
        assert data["tenant_id"] == str(tenant.id)
        assert "id" in data

    async def test_profesor_sin_admin_intenta_crear_403(self, client, db_session):
        """8.2: PROFESOR sin tareas:admin intenta crear → 403"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "PROFESOR")

        token = _make_token(user, tenant, ["PROFESOR"])

        resp = await client.post(
            "/api/v1/tareas/",
            json={
                "asignado_a": str(user.id),
                "descripcion": "Tarea que no deberia poder crear",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 403

    async def test_crear_tarea_con_materia_y_contexto(self, client, db_session):
        """COORDINADOR crea tarea con materia_id y contexto_id opcionales"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        target_user = User(
            tenant_id=tenant.id,
            email=f"prof2-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof2",
            apellido="Destino",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(target_user)
        await db_session.flush()

        materia = await _create_materia(db_session, tenant.id)
        contexto_id = uuid.uuid4()
        token = _make_token(user, tenant, ["COORDINADOR"])

        resp = await client.post(
            "/api/v1/tareas/",
            json={
                "asignado_a": str(target_user.id),
                "descripcion": "Tarea con contexto",
                "materia_id": str(materia.id),
                "contexto_id": str(contexto_id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["materia_id"] == str(materia.id)
        assert data["contexto_id"] == str(contexto_id)


class TestTransicionesEstado:
    """8.3-8.6: Transiciones de estado"""

    async def test_transicion_valida_pendiente_enprogreso_resuelta(self, client, db_session):
        """8.3: Transición Pendiente → EnProgreso → Resuelta válida"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        # Create profesor (asignado)
        prof = User(
            tenant_id=tenant.id,
            email=f"prof3-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof3",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof)
        await db_session.flush()

        # Coord creates tarea
        coord_token = _make_token(coord, tenant, ["COORDINADOR"])
        resp = await client.post(
            "/api/v1/tareas/",
            json={
                "asignado_a": str(prof.id),
                "descripcion": "Tarea con transiciones",
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 201
        tarea_id = resp.json()["id"]

        # Setup profesor with tareas:gestionar
        prof_role = Role(name="PROFESOR", tenant_id=tenant.id)
        db_session.add(prof_role)
        await db_session.flush()
        ur = UserRole(user_id=prof.id, tenant_id=tenant.id, role_id=prof_role.id)
        db_session.add(ur)
        await db_session.flush()

        stmt = select(Permission).where(Permission.name == "tareas:gestionar")
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm is None:
            perm = Permission(name="tareas:gestionar", module="tareas", action="gestionar")
            db_session.add(perm)
            await db_session.flush()
        rp = RolePermission(role_id=prof_role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

        prof_token = _make_token(prof, tenant, ["PROFESOR"])

        resp = await client.put(
            f"/api/v1/tareas/{tarea_id}",
            json={"estado": "EnProgreso"},
            headers={"Authorization": f"Bearer {prof_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["estado"] == "EnProgreso"

        # Prof transitions to Resuelta
        resp = await client.put(
            f"/api/v1/tareas/{tarea_id}",
            json={"estado": "Resuelta"},
            headers={"Authorization": f"Bearer {prof_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["estado"] == "Resuelta"

    async def test_transicion_invalida_retroceso_422(self, client, db_session):
        """8.4: Transición inválida (retroceso) → 422"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof = User(
            tenant_id=tenant.id,
            email=f"prof4-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof4",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof)
        await db_session.flush()

        coord_token = _make_token(coord, tenant, ["COORDINADOR"])
        resp = await client.post(
            "/api/v1/tareas/",
            json={
                "asignado_a": str(prof.id),
                "descripcion": "Tarea retroceso",
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 201
        tarea_id = resp.json()["id"]

        # Setup profesor with tareas:gestionar
        prof_role = Role(name="PROFESOR", tenant_id=tenant.id)
        db_session.add(prof_role)
        await db_session.flush()
        ur = UserRole(user_id=prof.id, tenant_id=tenant.id, role_id=prof_role.id)
        db_session.add(ur)
        await db_session.flush()

        stmt = select(Permission).where(Permission.name == "tareas:gestionar")
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm is None:
            perm = Permission(name="tareas:gestionar", module="tareas", action="gestionar")
            db_session.add(perm)
            await db_session.flush()
        rp = RolePermission(role_id=prof_role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

        prof_token = _make_token(prof, tenant, ["PROFESOR"])

        resp = await client.put(
            f"/api/v1/tareas/{tarea_id}",
            json={"estado": "Cancelada"},
            headers={"Authorization": f"Bearer {prof_token}"},
        )
        assert resp.status_code == 422

    async def test_profesor_no_cambia_estado_tarea_ajena_403(self, client, db_session):
        """8.5: PROFESOR no cambia estado de tarea ajena → 403"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof_a = User(
            tenant_id=tenant.id,
            email=f"prof5a-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="ProfA",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof_a)
        await db_session.flush()

        prof_b = User(
            tenant_id=tenant.id,
            email=f"prof5b-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="ProfB",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof_b)
        await db_session.flush()

        # Coord creates tarea assigned to prof_a
        coord_token = _make_token(coord, tenant, ["COORDINADOR"])
        resp = await client.post(
            "/api/v1/tareas/",
            json={
                "asignado_a": str(prof_a.id),
                "descripcion": "Tarea de ProfA",
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        tarea_id = resp.json()["id"]

        # Setup profesor B with tareas:gestionar
        prof_b_role = Role(name="PROFESOR", tenant_id=tenant.id)
        db_session.add(prof_b_role)
        await db_session.flush()
        ur = UserRole(user_id=prof_b.id, tenant_id=tenant.id, role_id=prof_b_role.id)
        db_session.add(ur)
        await db_session.flush()

        stmt = select(Permission).where(Permission.name == "tareas:gestionar")
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm is None:
            perm = Permission(name="tareas:gestionar", module="tareas", action="gestionar")
            db_session.add(perm)
            await db_session.flush()
        rp = RolePermission(role_id=prof_b_role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

        prof_b_token = _make_token(prof_b, tenant, ["PROFESOR"])

        resp = await client.put(
            f"/api/v1/tareas/{tarea_id}",
            json={"estado": "EnProgreso"},
            headers={"Authorization": f"Bearer {prof_b_token}"},
        )
        assert resp.status_code == 403

    async def test_coordinador_cancela_desde_cualquier_estado_200(self, client, db_session):
        """8.6: COORDINADOR cancela tarea desde cualquier estado → 200"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof = User(
            tenant_id=tenant.id,
            email=f"prof6-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof6",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof)
        await db_session.flush()

        coord_token = _make_token(coord, tenant, ["COORDINADOR"])

        # Test cancel from Pendiente
        resp = await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(prof.id), "descripcion": "Tarea a cancelar 1"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        tarea_id = resp.json()["id"]

        resp = await client.put(
            f"/api/v1/tareas/{tarea_id}",
            json={"estado": "Cancelada"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["estado"] == "Cancelada"

        # Test cancel from EnProgreso
        resp = await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(prof.id), "descripcion": "Tarea a cancelar 2"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        tarea_id2 = resp.json()["id"]

        # First set to EnProgreso
        await client.put(
            f"/api/v1/tareas/{tarea_id2}",
            json={"estado": "EnProgreso"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )

        # Now cancel
        resp = await client.put(
            f"/api/v1/tareas/{tarea_id2}",
            json={"estado": "Cancelada"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["estado"] == "Cancelada"


class TestVisibilidadRol:
    """8.7-8.10: Visibilidad por rol y filtros"""

    async def test_profesor_lista_solo_sus_tareas(self, client, db_session):
        """8.7: PROFESOR lista solo sus tareas (no ve ajenas)"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof_a = User(
            tenant_id=tenant.id,
            email=f"prof7a-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof7A",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof_a)
        await db_session.flush()

        prof_b = User(
            tenant_id=tenant.id,
            email=f"prof7b-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof7B",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof_b)
        await db_session.flush()

        # Setup single PROFESOR role for both prof_a and prof_b
        prof_role = Role(name="PROFESOR", tenant_id=tenant.id)
        db_session.add(prof_role)
        await db_session.flush()

        # Ensure tareas:gestionar permission exists and is assigned
        stmt = select(Permission).where(Permission.name == "tareas:gestionar")
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm is None:
            perm = Permission(name="tareas:gestionar", module="tareas", action="gestionar")
            db_session.add(perm)
            await db_session.flush()
        rp = RolePermission(role_id=prof_role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

        for prof in [prof_a, prof_b]:
            ur = UserRole(user_id=prof.id, tenant_id=tenant.id, role_id=prof_role.id)
            db_session.add(ur)
            await db_session.flush()

        coord_token = _make_token(coord, tenant, ["COORDINADOR"])

        # Create 2 tareas: one for prof_a, one for prof_b
        await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(prof_a.id), "descripcion": "Tarea de A"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(prof_b.id), "descripcion": "Tarea de B"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )

        # Prof A lists his tareas
        prof_a_token = _make_token(prof_a, tenant, ["PROFESOR"])
        resp = await client.get(
            "/api/v1/tareas/",
            headers={"Authorization": f"Bearer {prof_a_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["descripcion"] == "Tarea de A"

    async def test_coordinador_ve_todas_las_tareas(self, client, db_session):
        """8.8: COORDINADOR ve todas las tareas del tenant"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof = User(
            tenant_id=tenant.id,
            email=f"prof8-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof8",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof)
        await db_session.flush()

        coord_token = _make_token(coord, tenant, ["COORDINADOR"])

        # Create 3 tareas
        for i in range(3):
            await client.post(
                "/api/v1/tareas/",
                json={"asignado_a": str(prof.id), "descripcion": f"Tarea {i}"},
                headers={"Authorization": f"Bearer {coord_token}"},
            )

        resp = await client.get(
            "/api/v1/tareas/",
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3

    async def test_filtros_estado_materia_busqueda(self, client, db_session):
        """8.9: Filtros por estado, materia, búsqueda libre"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof = User(
            tenant_id=tenant.id,
            email=f"prof9-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof9",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof)
        await db_session.flush()

        materia = await _create_materia(db_session, tenant.id)
        coord_token = _make_token(coord, tenant, ["COORDINADOR"])

        # Create tareas with different states
        resp1 = await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(prof.id), "descripcion": "Informe de programacion"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        t1_id = resp1.json()["id"]

        resp2 = await client.post(
            "/api/v1/tareas/",
            json={
                "asignado_a": str(prof.id),
                "descripcion": "Corregir examenes de matematicas",
                "materia_id": str(materia.id),
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        t2_id = resp2.json()["id"]

        # Move t2 to Resuelta (Pendiente → EnProgreso → Resuelta)
        put_resp = await client.put(
            f"/api/v1/tareas/{t2_id}",
            json={"estado": "EnProgreso"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert put_resp.status_code == 200

        put_resp = await client.put(
            f"/api/v1/tareas/{t2_id}",
            json={"estado": "Resuelta"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["estado"] == "Resuelta"

        # Filter by estado
        resp = await client.get(
            f"/api/v1/tareas/?estado=Resuelta",
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1, f"Expected at least 1 tarea with estado=Resuelta, got {data['total']}"
        resuelta_ids = [item["id"] for item in data["items"] if item["estado"] == "Resuelta"]
        assert t2_id in resuelta_ids

        # Filter by materia
        resp = await client.get(
            f"/api/v1/tareas/?materia_id={materia.id}",
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == t2_id

        # Search by descripcion
        resp = await client.get(
            f"/api/v1/tareas/?q=programacion",
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert "programacion" in data["items"][0]["descripcion"].lower()

    async def test_paginacion_limit_offset(self, client, db_session):
        """8.10: Paginación (limit, offset)"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof = User(
            tenant_id=tenant.id,
            email=f"prof10-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof10",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof)
        await db_session.flush()

        coord_token = _make_token(coord, tenant, ["COORDINADOR"])

        # Create 5 tareas
        for i in range(5):
            await client.post(
                "/api/v1/tareas/",
                json={"asignado_a": str(prof.id), "descripcion": f"Tarea pag {i}"},
                headers={"Authorization": f"Bearer {coord_token}"},
            )

        # Get first 2
        resp = await client.get(
            "/api/v1/tareas/?limit=2&offset=0",
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 0


class TestSoftDelete:
    """8.11-8.12: Soft delete"""

    async def test_admin_soft_delete_204(self, client, db_session):
        """8.11: Soft delete por ADMIN → 204, tarea no aparece en listado"""
        admin, tenant, _ = await _setup_tenant_and_user(db_session, "ADMIN")

        target = User(
            tenant_id=tenant.id,
            email=f"target-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Target",
            apellido="Delete",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(target)
        await db_session.flush()

        admin_token = _make_token(admin, tenant, ["ADMIN"])

        resp = await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(target.id), "descripcion": "Tarea a borrar"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        tarea_id = resp.json()["id"]

        # Soft delete
        resp = await client.delete(
            f"/api/v1/tareas/{tarea_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 204

        # Should not appear in list
        resp = await client.get(
            "/api/v1/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert tarea_id not in ids

    async def test_profesor_no_puede_borrar_403(self, client, db_session):
        """8.12: PROFESOR no puede borrar → 403"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof = User(
            tenant_id=tenant.id,
            email=f"prof12-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof12",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof)
        await db_session.flush()

        prof_role = Role(name="PROFESOR", tenant_id=tenant.id)
        db_session.add(prof_role)
        await db_session.flush()
        ur = UserRole(user_id=prof.id, tenant_id=tenant.id, role_id=prof_role.id)
        db_session.add(ur)
        await db_session.flush()

        stmt = select(Permission).where(Permission.name == "tareas:gestionar")
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm is None:
            perm = Permission(name="tareas:gestionar", module="tareas", action="gestionar")
            db_session.add(perm)
            await db_session.flush()
        rp = RolePermission(role_id=prof_role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

        coord_token = _make_token(coord, tenant, ["COORDINADOR"])

        resp = await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(prof.id), "descripcion": "Tarea que nadie borra"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        tarea_id = resp.json()["id"]

        prof_token = _make_token(prof, tenant, ["PROFESOR"])
        resp = await client.delete(
            f"/api/v1/tareas/{tarea_id}",
            headers={"Authorization": f"Bearer {prof_token}"},
        )
        assert resp.status_code == 403


class TestComentarios:
    """8.13-8.15: Comentarios"""

    async def test_agregar_comentario_201(self, client, db_session):
        """8.13: Agregar comentario → 201, autor correcto"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof = User(
            tenant_id=tenant.id,
            email=f"prof13-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof13",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof)
        await db_session.flush()

        coord_token = _make_token(coord, tenant, ["COORDINADOR"])

        resp = await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(prof.id), "descripcion": "Tarea con comentario"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        tarea_id = resp.json()["id"]

        # Add comment
        resp = await client.post(
            f"/api/v1/tareas/{tarea_id}/comentarios",
            json={"texto": "Este es un comentario de prueba"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["autor_id"] == str(coord.id)
        assert data["texto"] == "Este es un comentario de prueba"
        assert data["tarea_id"] == tarea_id

    async def test_listar_comentarios_ordenados(self, client, db_session):
        """8.14: Listar comentarios de tarea → ordenados por fecha"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof = User(
            tenant_id=tenant.id,
            email=f"prof14-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof14",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof)
        await db_session.flush()

        coord_token = _make_token(coord, tenant, ["COORDINADOR"])

        resp = await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(prof.id), "descripcion": "Tarea varios comentarios"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        tarea_id = resp.json()["id"]

        # Add 2 comments
        await client.post(
            f"/api/v1/tareas/{tarea_id}/comentarios",
            json={"texto": "Primer comentario"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        await client.post(
            f"/api/v1/tareas/{tarea_id}/comentarios",
            json={"texto": "Segundo comentario"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )

        # List comments
        resp = await client.get(
            f"/api/v1/tareas/{tarea_id}/comentarios",
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["texto"] == "Primer comentario"
        assert data[1]["texto"] == "Segundo comentario"

    async def test_comentario_sin_texto_422(self, client, db_session):
        """8.15: Comentario sin texto → 422"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof = User(
            tenant_id=tenant.id,
            email=f"prof15-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Prof15",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof)
        await db_session.flush()

        coord_token = _make_token(coord, tenant, ["COORDINADOR"])

        resp = await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(prof.id), "descripcion": "Tarea comentario vacio"},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        tarea_id = resp.json()["id"]

        # Empty texto
        resp = await client.post(
            f"/api/v1/tareas/{tarea_id}/comentarios",
            json={"texto": ""},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 422


class TestMultiTenant:
    """8.16: Aislamiento multi-tenant"""

    async def test_aislamiento_multi_tenant(self, client, db_session):
        """8.16: Tenant A no ve tareas de tenant B"""
        # Tenant A
        user_a, tenant_a = await _setup_second_tenant(db_session)

        # Tenant B
        user_b, tenant_b = await _setup_second_tenant(db_session)

        # Actually use _setup_tenant_and_user for better control
        # Let's create tareas in each tenant
        token_a = _make_token(user_a, tenant_a, ["COORDINADOR"])
        token_b = _make_token(user_b, tenant_b, ["COORDINADOR"])

        # Create tarea in tenant A
        # Need a target user in tenant A
        target_a = User(
            tenant_id=tenant_a.id,
            email=f"targeta-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="TargetA",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(target_a)
        await db_session.flush()

        resp = await client.post(
            "/api/v1/tareas/",
            json={"asignado_a": str(target_a.id), "descripcion": "Tarea solo tenant A"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert resp.status_code == 201

        # User B should see 0 tareas
        resp = await client.get(
            "/api/v1/tareas/",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0


class TestReasignacion:
    """8.17: Reasignación"""

    async def test_reasignacion_mantiene_asignado_por(self, client, db_session):
        """8.17: Reasignación por COORDINADOR mantiene asignado_por original"""
        coord, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")

        prof_original = User(
            tenant_id=tenant.id,
            email=f"prof_orig-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="ProfOrig",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof_original)
        await db_session.flush()

        prof_nuevo = User(
            tenant_id=tenant.id,
            email=f"prof_nuevo-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="ProfNuevo",
            apellido="Test",
            password_hash="$2b$12$dummyhashfordummyhashfordummyhashfo",
        )
        db_session.add(prof_nuevo)
        await db_session.flush()

        coord_token = _make_token(coord, tenant, ["COORDINADOR"])

        resp = await client.post(
            "/api/v1/tareas/",
            json={
                "asignado_a": str(prof_original.id),
                "descripcion": "Tarea a reasignar",
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        tarea_id = resp.json()["id"]
        assert resp.json()["asignado_por"] == str(coord.id)

        # Reassign to prof_nuevo
        resp = await client.put(
            f"/api/v1/tareas/{tarea_id}",
            json={"asignado_a": str(prof_nuevo.id)},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["asignado_a"] == str(prof_nuevo.id)
        assert data["asignado_por"] == str(coord.id)  # Original creator preserved
