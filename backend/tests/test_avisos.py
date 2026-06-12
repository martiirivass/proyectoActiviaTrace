"""Tests for Avisos y Acknowledgment module (C-15).

Strict TDD: RED → GREEN → REFACTOR.
These test the full stack: Router → Service → Repository → DB.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

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
from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso
from app.models.acknowledgment_aviso import AcknowledgmentAviso

pytestmark = pytest.mark.asyncio


# ===== Helpers =====


async def _setup_tenant_and_user(
    db_session,
    role_name: str = "COORDINADOR",
    extra_permissions: list[str] | None = None,
    skip_permissions: list[str] | None = None,
):
    """Setup tenant with user having specific roles and avisos permissions.

    By default gives avisos:publicar + avisos:ver for COORDINADOR/ADMIN,
    and only avisos:ver for other roles.
    """
    code = f"AV{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Aviso Test {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"av-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Aviso",
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

    # Create permissions and assign them
    perms_to_set = extra_permissions or []
    if skip_permissions:
        perms_to_set = [p for p in perms_to_set if p not in skip_permissions]
    else:
        # Default: assign based on role
        if role_name in ("COORDINADOR", "ADMIN"):
            perms_to_set = ["avisos:publicar", "avisos:ver"]
        else:
            perms_to_set = ["avisos:ver"]

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
    code = f"AV2{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Aviso Test B {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"av-b-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="AvisoB",
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

    for perm_name in ["avisos:publicar", "avisos:ver"]:
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


async def _create_asignacion(db_session, tenant_id, usuario_id, materia_id=None, rol="PROFESOR"):
    a = Asignacion(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        rol=rol,
        materia_id=materia_id,
        desde=datetime.now(timezone.utc).date() - timedelta(days=30),
        hasta=datetime.now(timezone.utc).date() + timedelta(days=365),
    )
    db_session.add(a)
    await db_session.flush()
    return a


def _now():
    return datetime.now(timezone.utc)


def _make_token(user, tenant, roles=None):
    return create_access_token(user.id, tenant.id, roles or ["COORDINADOR"])


# ===== 8.1 Setup fixtures (implicit in helpers) =====


class TestCrearAviso:
    """8.2-8.5: Crear avisos"""

    async def test_crear_aviso_global_como_coordinador(self, client, db_session):
        """8.2: Crear aviso global como COORDINADOR → 201"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        now = _now()

        resp = await client.post(
            "/api/v1/avisos/",
            json={
                "titulo": "Aviso Importante",
                "cuerpo": "Este es un aviso de prueba",
                "alcance": "Global",
                "severidad": "Info",
                "inicio_en": now.isoformat(),
                "fin_en": (now + timedelta(days=7)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["titulo"] == "Aviso Importante"
        assert data["cuerpo"] == "Este es un aviso de prueba"
        assert data["alcance"] == "Global"
        assert data["severidad"] == "Info"
        assert "id" in data
        assert data["activo"] is True
        assert data["requiere_ack"] is False

        # Verify persistence
        stmt = select(Aviso).where(Aviso.id == uuid.UUID(data["id"]))
        result = await db_session.execute(stmt)
        aviso = result.scalar_one_or_none()
        assert aviso is not None
        assert aviso.titulo == "Aviso Importante"

    async def test_crear_aviso_como_alumno_retorna_403(self, client, db_session):
        """8.3: Crear aviso como ALUMNO → 403"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token = _make_token(user, tenant, ["ALUMNO"])
        now = _now()

        resp = await client.post(
            "/api/v1/avisos/",
            json={
                "titulo": "Aviso no permitido",
                "cuerpo": "No deberia poder crearlo",
                "alcance": "Global",
                "severidad": "Info",
                "inicio_en": now.isoformat(),
                "fin_en": (now + timedelta(days=7)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_crear_aviso_por_materia_sin_materia_id_retorna_422(self, client, db_session):
        """8.4: Crear aviso PorMateria sin materia_id → 422"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        now = _now()

        resp = await client.post(
            "/api/v1/avisos/",
            json={
                "titulo": "Aviso sin materia",
                "cuerpo": "Falta materia_id",
                "alcance": "PorMateria",
                "severidad": "Info",
                "inicio_en": now.isoformat(),
                "fin_en": (now + timedelta(days=7)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_crear_aviso_con_fin_anterior_a_inicio_retorna_422(self, client, db_session):
        """8.5: Crear aviso con fin_en anterior a inicio_en → 422"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        now = _now()

        resp = await client.post(
            "/api/v1/avisos/",
            json={
                "titulo": "Aviso con fechas invalidas",
                "cuerpo": "Prueba",
                "alcance": "Global",
                "severidad": "Info",
                "inicio_en": (now + timedelta(days=7)).isoformat(),
                "fin_en": now.isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestListarAvisos:
    """8.6-8.11: Listado de avisos"""

    async def test_alumno_ve_solo_global_y_por_rol(self, client, db_session):
        """8.6: ALUMNO solo ve Global y PorRol(ALUMNO)"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token = _make_token(user, tenant, ["ALUMNO"])
        now = _now()

        # Create avisos: Global, PorMateria, PorRol(ALUMNO), PorRol(PROFESOR)
        materia = await _create_materia(db_session, tenant.id)

        aviso_global = Aviso(
            tenant_id=tenant.id,
            titulo="Global",
            cuerpo="Global",
            alcance=AlcanceAviso.Global,
            severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1),
            fin_en=now + timedelta(days=7),
            orden=0,
            activo=True,
            requiere_ack=False,
        )
        db_session.add(aviso_global)
        await db_session.flush()

        aviso_materia = Aviso(
            tenant_id=tenant.id,
            titulo="PorMateria",
            cuerpo="Solo materia",
            alcance=AlcanceAviso.PorMateria,
            severidad=SeveridadAviso.Info,
            materia_id=materia.id,
            inicio_en=now - timedelta(hours=1),
            fin_en=now + timedelta(days=7),
            orden=1,
            activo=True,
            requiere_ack=False,
        )
        db_session.add(aviso_materia)
        await db_session.flush()

        aviso_rol_alumno = Aviso(
            tenant_id=tenant.id,
            titulo="PorRolAlumno",
            cuerpo="Solo alumnos",
            alcance=AlcanceAviso.PorRol,
            severidad=SeveridadAviso.Advertencia,
            rol_destino="ALUMNO",
            inicio_en=now - timedelta(hours=1),
            fin_en=now + timedelta(days=7),
            orden=2,
            activo=True,
            requiere_ack=False,
        )
        db_session.add(aviso_rol_alumno)
        await db_session.flush()

        aviso_rol_profesor = Aviso(
            tenant_id=tenant.id,
            titulo="PorRolProfesor",
            cuerpo="Solo profesores",
            alcance=AlcanceAviso.PorRol,
            severidad=SeveridadAviso.Critico,
            rol_destino="PROFESOR",
            inicio_en=now - timedelta(hours=1),
            fin_en=now + timedelta(days=7),
            orden=3,
            activo=True,
            requiere_ack=True,
        )
        db_session.add(aviso_rol_profesor)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        titulos = {item["titulo"] for item in data["items"]}
        assert "Global" in titulos
        assert "PorRolAlumno" in titulos
        assert "PorMateria" not in titulos
        assert "PorRolProfesor" not in titulos

    async def test_profesor_con_materia_ve_global_por_materia_y_por_rol(self, client, db_session):
        """8.7: PROFESOR con asignación ve Global + PorMateria + PorRol(PROFESOR)"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "PROFESOR")
        token = _make_token(user, tenant, ["PROFESOR"])
        now = _now()

        materia = await _create_materia(db_session, tenant.id)
        otra_materia = await _create_materia(db_session, tenant.id)
        await _create_asignacion(db_session, tenant.id, user.id, materia.id, rol="PROFESOR")

        aviso_global = Aviso(
            tenant_id=tenant.id, titulo="Global", cuerpo="Global",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso_global)

        aviso_materia = Aviso(
            tenant_id=tenant.id, titulo="MiMateria", cuerpo="Mi materia",
            alcance=AlcanceAviso.PorMateria, severidad=SeveridadAviso.Info,
            materia_id=materia.id,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso_materia)

        aviso_rol = Aviso(
            tenant_id=tenant.id, titulo="SoloProfes", cuerpo="Solo profe",
            alcance=AlcanceAviso.PorRol, severidad=SeveridadAviso.Advertencia,
            rol_destino="PROFESOR",
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso_rol)

        aviso_otra_materia = Aviso(
            tenant_id=tenant.id, titulo="OtraMateria", cuerpo="Otra materia",
            alcance=AlcanceAviso.PorMateria, severidad=SeveridadAviso.Info,
            materia_id=otra_materia.id,  # materia que existe pero el profe no tiene asignada
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso_otra_materia)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        titulos = {item["titulo"] for item in data["items"]}
        assert "Global" in titulos
        assert "MiMateria" in titulos
        assert "SoloProfes" in titulos
        assert "OtraMateria" not in titulos

    async def test_aviso_fuera_de_vigencia_no_aparece(self, client, db_session):
        """8.8: Aviso fuera de vigencia no aparece"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token = _make_token(user, tenant, ["ALUMNO"])
        now = _now()

        aviso_valido = Aviso(
            tenant_id=tenant.id, titulo="Valido", cuerpo="Vigente",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(days=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso_valido)

        aviso_vencido = Aviso(
            tenant_id=tenant.id, titulo="Vencido", cuerpo="Ya vencio",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(days=10), fin_en=now - timedelta(days=1),
            activo=True,
        )
        db_session.add(aviso_vencido)

        aviso_futuro = Aviso(
            tenant_id=tenant.id, titulo="Futuro", cuerpo="Aun no",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now + timedelta(days=10), fin_en=now + timedelta(days=20),
            activo=True,
        )
        db_session.add(aviso_futuro)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        titulos = {item["titulo"] for item in resp.json()["items"]}
        assert "Valido" in titulos
        assert "Vencido" not in titulos
        assert "Futuro" not in titulos

    async def test_aviso_desactivado_no_aparece(self, client, db_session):
        """8.9: Aviso desactivado (activo=false) no aparece"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token = _make_token(user, tenant, ["ALUMNO"])
        now = _now()

        aviso_activo = Aviso(
            tenant_id=tenant.id, titulo="Activo", cuerpo="Activo",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(days=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso_activo)

        aviso_inactivo = Aviso(
            tenant_id=tenant.id, titulo="Inactivo", cuerpo="Inactivo",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(days=1), fin_en=now + timedelta(days=7),
            activo=False,
        )
        db_session.add(aviso_inactivo)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        titulos = {item["titulo"] for item in resp.json()["items"]}
        assert "Activo" in titulos
        assert "Inactivo" not in titulos

    async def test_orden_por_prioridad(self, client, db_session):
        """8.10: Orden por prioridad (orden ASC, inicio_en DESC)"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token = _make_token(user, tenant, ["ALUMNO"])
        now = _now()

        # orden 0 (mas prioritario) mas antiguo
        aviso_a = Aviso(
            tenant_id=tenant.id, titulo="A-prioritario-viejo", cuerpo="A",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(days=5), fin_en=now + timedelta(days=7),
            orden=0, activo=True,
        )
        db_session.add(aviso_a)

        # orden 0 mas reciente
        aviso_b = Aviso(
            tenant_id=tenant.id, titulo="B-prioritario-reciente", cuerpo="B",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(days=1), fin_en=now + timedelta(days=7),
            orden=0, activo=True,
        )
        db_session.add(aviso_b)

        # orden 1 (menos prioritario)
        aviso_c = Aviso(
            tenant_id=tenant.id, titulo="C-menosprioritario", cuerpo="C",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(days=3), fin_en=now + timedelta(days=7),
            orden=1, activo=True,
        )
        db_session.add(aviso_c)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        titulos = [item["titulo"] for item in items]
        # orden 0 (ASC) first, then by inicio_en DESC within same order
        # So: B (orden 0, mas reciente), A (orden 0, mas antiguo), C (orden 1)
        assert titulos[0] == "B-prioritario-reciente"
        assert titulos[1] == "A-prioritario-viejo"
        assert titulos[2] == "C-menosprioritario"

    async def test_paginacion_avisos(self, client, db_session):
        """8.11: Paginación de avisos"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        now = _now()

        for i in range(5):
            aviso = Aviso(
                tenant_id=tenant.id, titulo=f"Aviso {i}", cuerpo=str(i),
                alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
                inicio_en=now - timedelta(days=1), fin_en=now + timedelta(days=7),
                orden=i, activo=True,
            )
            db_session.add(aviso)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/avisos/?limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 0


class TestAcknowledgment:
    """8.12-8.15: Confirmación de lectura"""

    async def test_confirmar_lectura_retorna_200(self, client, db_session):
        """8.12: Confirmar lectura (ack) → 200"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token = _make_token(user, tenant, ["ALUMNO"])
        now = _now()

        aviso = Aviso(
            tenant_id=tenant.id, titulo="AckTest", cuerpo="Requiere ack",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Critico,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            requiere_ack=True, activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        resp = await client.post(
            f"/api/v1/avisos/{aviso.id}/ack",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        # Verify DB
        stmt = select(AcknowledgmentAviso).where(
            AcknowledgmentAviso.aviso_id == aviso.id,
            AcknowledgmentAviso.usuario_id == user.id,
        )
        result = await db_session.execute(stmt)
        ack = result.scalar_one_or_none()
        assert ack is not None
        assert ack.confirmado_at is not None

    async def test_ack_duplicado_es_idempotente(self, client, db_session):
        """8.13: Ack duplicado → 200 + un solo registro"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token = _make_token(user, tenant, ["ALUMNO"])
        now = _now()

        aviso = Aviso(
            tenant_id=tenant.id, titulo="Idempotente", cuerpo="Test",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            requiere_ack=True, activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        resp1 = await client.post(
            f"/api/v1/avisos/{aviso.id}/ack",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 200

        resp2 = await client.post(
            f"/api/v1/avisos/{aviso.id}/ack",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 200

        stmt = select(AcknowledgmentAviso).where(AcknowledgmentAviso.aviso_id == aviso.id)
        result = await db_session.execute(stmt)
        acks = list(result.scalars().all())
        assert len(acks) == 1

    async def test_ack_aviso_no_visible_retorna_404(self, client, db_session):
        """8.14: Ack de aviso no visible → 404"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token = _make_token(user, tenant, ["ALUMNO"])
        now = _now()

        materia = await _create_materia(db_session, tenant.id)
        aviso = Aviso(
            tenant_id=tenant.id, titulo="NoVisible", cuerpo="No visible",
            alcance=AlcanceAviso.PorMateria, severidad=SeveridadAviso.Info,
            materia_id=materia.id,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            requiere_ack=True, activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        resp = await client.post(
            f"/api/v1/avisos/{aviso.id}/ack",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_campo_acknowledged_true_despues_de_confirmar(self, client, db_session):
        """8.15: Campo acknowledged=true después de confirmar"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token = _make_token(user, tenant, ["ALUMNO"])
        now = _now()

        aviso = Aviso(
            tenant_id=tenant.id, titulo="AckFlag", cuerpo="Test flag",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            requiere_ack=False, activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        # Before ack
        resp = await client.get(
            f"/api/v1/avisos/{aviso.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["acknowledged"] is False

        # Ack
        await client.post(
            f"/api/v1/avisos/{aviso.id}/ack",
            headers={"Authorization": f"Bearer {token}"},
        )

        # After ack
        resp = await client.get(
            f"/api/v1/avisos/{aviso.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["acknowledged"] is True


class TestStats:
    """8.16-8.17: Estadísticas"""

    async def test_stats_de_aviso(self, client, db_session):
        """8.16: Stats de aviso — contar alcanzados + acknowledges"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        now = _now()

        # Create a global aviso
        aviso = Aviso(
            tenant_id=tenant.id, titulo="StatsTest", cuerpo="Test stats",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            requiere_ack=True, activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        # Create another user and ack
        otro_user = User(
            tenant_id=tenant.id,
            email=f"otro-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Otro",
            apellido="User",
            password_hash=PasswordService.hash("pass"),
        )
        db_session.add(otro_user)
        await db_session.flush()

        ack = AcknowledgmentAviso(aviso_id=aviso.id, usuario_id=otro_user.id)
        db_session.add(ack)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/avisos/{aviso.id}/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["aviso_id"] == str(aviso.id)
        assert data["total_acknowledgments"] >= 1
        assert data["total_usuarios_alcanzados"] >= 1
        assert data["porcentaje_confirmacion"] >= 0

    async def test_stats_sin_permiso_retorna_403(self, client, db_session):
        """8.17: Stats sin permiso avisos:publicar → 403"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token = _make_token(user, tenant, ["ALUMNO"])
        now = _now()

        aviso = Aviso(
            tenant_id=tenant.id, titulo="StatsNoPerm", cuerpo="Test",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/avisos/{aviso.id}/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestListarAcks:
    """8.18-8.19: Listar usuarios que confirmaron"""

    async def test_listar_usuarios_que_confirmaron(self, client, db_session):
        """8.18: Listar usuarios que confirmaron (GET /{id}/acks)"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        now = _now()

        aviso = Aviso(
            tenant_id=tenant.id, titulo="AckList", cuerpo="Test",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            requiere_ack=True, activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        ack = AcknowledgmentAviso(aviso_id=aviso.id, usuario_id=user.id)
        db_session.add(ack)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/avisos/{aviso.id}/acks",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) >= 1
        found = any(item["usuario_id"] == str(user.id) for item in data["items"])
        assert found

    async def test_listar_acks_vacio(self, client, db_session):
        """8.19: Listar acks vacío"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        now = _now()

        aviso = Aviso(
            tenant_id=tenant.id, titulo="AckVacio", cuerpo="Test",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/avisos/{aviso.id}/acks",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0


class TestEditarAviso:
    """8.20-8.21: Editar aviso"""

    async def test_editar_aviso_exitoso(self, client, db_session):
        """8.20: Editar aviso (PUT)"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        now = _now()

        aviso = Aviso(
            tenant_id=tenant.id, titulo="Original", cuerpo="Original",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        resp = await client.put(
            f"/api/v1/avisos/{aviso.id}",
            json={"titulo": "Modificado", "cuerpo": "Cuerpo modificado"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["titulo"] == "Modificado"
        assert data["cuerpo"] == "Cuerpo modificado"

    async def test_editar_aviso_inexistente_retorna_404(self, client, db_session):
        """8.21: Editar aviso inexistente → 404"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        fake_id = uuid.uuid4()

        resp = await client.put(
            f"/api/v1/avisos/{fake_id}",
            json={"titulo": "No existe"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestEliminarAviso:
    """8.22: Eliminar aviso (soft delete)"""

    async def test_eliminar_aviso_soft_delete(self, client, db_session):
        """8.22: Eliminar aviso → 204, ya no aparece"""
        user, tenant, _ = await _setup_tenant_and_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        now = _now()

        aviso = Aviso(
            tenant_id=tenant.id, titulo="ParaEliminar", cuerpo="Será eliminado",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        # Delete
        resp = await client.delete(
            f"/api/v1/avisos/{aviso.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        # Verify soft delete
        stmt = select(Aviso).where(Aviso.id == aviso.id)
        result = await db_session.execute(stmt)
        deleted = result.scalar_one()
        assert deleted.is_deleted is True

        # Should not appear in list
        user_alumno, _, _ = await _setup_tenant_and_user(db_session, "ALUMNO")
        token_alumno = _make_token(user_alumno, tenant, ["ALUMNO"])
        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token_alumno}"},
        )
        titulos = {item["titulo"] for item in resp.json()["items"]}
        assert "ParaEliminar" not in titulos


class TestAislamientoTenant:
    """8.23: Aislamiento multi-tenant"""

    async def test_aislamiento_tenant_datos_no_visibles(self, client, db_session):
        """8.23: Datos del tenant A no visibles en tenant B"""
        user_a, tenant_a = await _setup_second_tenant(db_session)
        user_b, tenant_b = await _setup_second_tenant(db_session)
        token_a = _make_token(user_a, tenant_a, ["COORDINADOR"])
        token_b = _make_token(user_b, tenant_b, ["COORDINADOR"])
        now = _now()

        # Create aviso in tenant A
        aviso_a = Aviso(
            tenant_id=tenant_a.id, titulo="SoloTenantA", cuerpo="Solo A",
            alcance=AlcanceAviso.Global, severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(hours=1), fin_en=now + timedelta(days=7),
            activo=True,
        )
        db_session.add(aviso_a)
        await db_session.flush()

        # Tenant B should not see it
        resp = await client.get(
            "/api/v1/avisos/",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 200
        titulos = {item["titulo"] for item in resp.json()["items"]}
        assert "SoloTenantA" not in titulos

        # Tenant B should get 404 on direct access
        resp = await client.get(
            f"/api/v1/avisos/{aviso_a.id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

        # Tenant B should get 404 on delete
        resp = await client.delete(
            f"/api/v1/avisos/{aviso_a.id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404
