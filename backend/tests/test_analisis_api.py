"""Integration tests for analisis API endpoints.

These test the full stack: Router → Service → Repository → DB.
They use a real database via fixtures from conftest.py.
"""

import uuid
from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient

from app.core.dependencies import get_current_user
from app.core.security import PasswordService, create_access_token
from app.models import Permission, Role, RolePermission, Tenant, User, UserRole, UserTenant
from app.models.calificacion import Calificacion, OrigenCalificacion
from app.schemas.auth import CurrentUser

pytestmark = pytest.mark.asyncio


# ===== Fixtures =====


async def _ensure_table(engine):
    from app.core.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _setup_tenant_permission(db_session, permission_codename: str):
    """Setup tenant with user having a specific permission."""
    code = f"API{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"API Test {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"api-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="API",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name="API_ROLE", tenant_id=tenant.id)
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


async def _create_materia(db_session, tenant_id):
    from app.models.materia import Materia

    m = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:6].upper()}",
        nombre="Materia Test",
    )
    db_session.add(m)
    await db_session.flush()
    return m


async def _create_cohorte(db_session, tenant_id):
    from app.models.cohorte import Cohorte
    from app.models.carrera import Carrera

    c = Carrera(
        tenant_id=tenant_id,
        codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
        nombre="Carrera Test",
    )
    db_session.add(c)
    await db_session.flush()

    coh = Cohorte(
        tenant_id=tenant_id,
        carrera_id=c.id,
        nombre=f"COH-{uuid.uuid4().hex[:6].upper()}",
        anio=2026,
    )
    db_session.add(coh)
    await db_session.flush()
    return coh


async def _create_version_padron(db_session, tenant_id, materia_id, cohorte_id, user_id):
    from app.models.version_padron import VersionPadron

    v = VersionPadron(
        tenant_id=tenant_id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        cargado_por=user_id,
        activa=True,
    )
    db_session.add(v)
    await db_session.flush()
    return v


async def _create_entrada(db_session, tenant_id, version_id, nombre, apellidos, email=None, comision="A", regional="CABA"):
    from app.models.entrada_padron import EntradaPadron

    if email is None:
        email = f"{nombre.lower()}.{apellidos.lower()}@test.com"
    e = EntradaPadron(
        version_id=version_id,
        tenant_id=tenant_id,
        nombre=nombre,
        apellidos=apellidos,
        email=email,
        comision=comision,
        regional=regional,
    )
    db_session.add(e)
    await db_session.flush()
    return e


async def _setup_analisis_data(db_session, test_engine, tenant_id, materia_id, cohorte_id, user_id):
    """Helper to set up common test data for analysis endpoints."""
    version = await _create_version_padron(db_session, tenant_id, materia_id, cohorte_id, user_id)

    entry_a = await _create_entrada(db_session, tenant_id, version.id, "Juan", "Perez", "juan@test.com", "A", "CABA")
    entry_b = await _create_entrada(db_session, tenant_id, version.id, "Maria", "Garcia", "maria@test.com", "B", "GBA")
    entry_c = await _create_entrada(db_session, tenant_id, version.id, "Carlos", "Lopez", "carlos@test.com", "A", "CABA")

    now = datetime.now(timezone.utc)
    # Juan: TP1 aprobada (80), TP2 reprobada (40)
    for nota, aprobado, actividad in [(80, True, "TP1"), (40, False, "TP2")]:
        cal = Calificacion(
            tenant_id=tenant_id,
            entrada_padron_id=entry_a.id,
            materia_id=materia_id,
            actividad=actividad,
            nota_numerica=float(nota),
            aprobado=aprobado,
            origen=OrigenCalificacion.IMPORTADO,
            importado_at=now,
        )
        db_session.add(cal)

    # Maria: TP1 aprobada (70), TP2 aprobada (85)
    for nota, aprobado, actividad in [(70, True, "TP1"), (85, True, "TP2")]:
        cal = Calificacion(
            tenant_id=tenant_id,
            entrada_padron_id=entry_b.id,
            materia_id=materia_id,
            actividad=actividad,
            nota_numerica=float(nota),
            aprobado=aprobado,
            origen=OrigenCalificacion.IMPORTADO,
            importado_at=now,
        )
        db_session.add(cal)

    # Carlos: TP1 reprobada (30), TP2 reprobada (20)
    for nota, aprobado, actividad in [(30, False, "TP1"), (20, False, "TP2")]:
        cal = Calificacion(
            tenant_id=tenant_id,
            entrada_padron_id=entry_c.id,
            materia_id=materia_id,
            actividad=actividad,
            nota_numerica=float(nota),
            aprobado=aprobado,
            origen=OrigenCalificacion.IMPORTADO,
            importado_at=now,
        )
        db_session.add(cal)

    await db_session.flush()
    return entry_a, entry_b, entry_c


# ===== 6.6 Integration: GET /api/v1/analisis/atrasados =====


class TestAtrasadosEndpoint:
    async def test_atrasados_devuelve_alumnos_con_nota_bajo_umbral(self, client, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_permission(db_session, "atrasados:ver")
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        await _setup_analisis_data(db_session, test_engine, tenant.id, materia.id, cohorte.id, user.id)

        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["API_ROLE"])

        response = await client.get(
            f"/api/v1/analisis/atrasados?materia_id={materia.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0

    async def test_atrasados_sin_permiso_retorna_403(self, client, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_permission(db_session, "otro:permiso")
        materia_id = uuid.uuid4()

        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["API_ROLE"])

        response = await client.get(
            f"/api/v1/analisis/atrasados?materia_id={materia_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    async def test_atrasados_sin_token_retorna_401(self, client):
        response = await client.get(
            f"/api/v1/analisis/atrasados?materia_id={uuid.uuid4()}",
        )
        assert response.status_code == 401

    async def test_atrasados_filtro_busqueda(self, client, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_permission(db_session, "atrasados:ver")
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        await _setup_analisis_data(db_session, test_engine, tenant.id, materia.id, cohorte.id, user.id)

        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["API_ROLE"])

        response = await client.get(
            f"/api/v1/analisis/atrasados?materia_id={materia.id}&busqueda=Juan",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert "Juan" in item["alumno_nombre"]


# ===== 6.7 Integration: GET /api/v1/analisis/ranking =====


class TestRankingEndpoint:
    async def test_ranking_retorna_orden_descendente(self, client, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_permission(db_session, "atrasados:ver")
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        await _setup_analisis_data(db_session, test_engine, tenant.id, materia.id, cohorte.id, user.id)

        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["API_ROLE"])

        response = await client.get(
            f"/api/v1/analisis/ranking?materia_id={materia.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        # Maria should be first (2 aprobadas)
        if data["items"]:
            assert data["items"][0]["aprobadas"] >= data["items"][-1]["aprobadas"]


# ===== 6.8 Integration: GET /api/v1/analisis/exportar-tps-sin-corregir =====


class TestExportarTpsEndpoint:
    async def test_export_devuelve_csv(self, client, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_permission(db_session, "atrasados:ver")
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        await _setup_analisis_data(db_session, test_engine, tenant.id, materia.id, cohorte.id, user.id)

        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["API_ROLE"])

        response = await client.get(
            f"/api/v1/analisis/exportar-tps-sin-corregir?materia_id={materia.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        assert "attachment" in response.headers.get("content-disposition", "")


# ===== 6.9 Integration: monitores =====


class TestMonitorGeneralEndpoint:
    async def test_monitor_general_retorna_paginado(self, client, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_permission(db_session, "atrasados:ver")
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        await _setup_analisis_data(db_session, test_engine, tenant.id, materia.id, cohorte.id, user.id)

        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["API_ROLE"])

        response = await client.get(
            f"/api/v1/analisis/monitor-general?materia_id={materia.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data


class TestMonitorSeguimientoEndpoint:
    async def test_monitor_seguimiento_retorna_data(self, client, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_permission(db_session, "atrasados:ver")
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        await _setup_analisis_data(db_session, test_engine, tenant.id, materia.id, cohorte.id, user.id)

        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["API_ROLE"])

        response = await client.get(
            "/api/v1/analisis/monitor-seguimiento",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestMonitorSeguimientoExtendidoEndpoint:
    async def test_extendido_retorna_data(self, client, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_permission(db_session, "atrasados:ver")
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        await _setup_analisis_data(db_session, test_engine, tenant.id, materia.id, cohorte.id, user.id)

        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["API_ROLE"])

        response = await client.get(
            "/api/v1/analisis/monitor-seguimiento-extendido",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data


# ===== 6.10 Integration: 403 sin permiso =====


class TestAnalisisPermisos:
    async def test_todos_los_endpoints_requieren_permiso(self, client, db_session, test_engine):
        """Verify all endpoints return 401 without token."""
        endpoints = [
            f"/api/v1/analisis/atrasados?materia_id={uuid.uuid4()}",
            f"/api/v1/analisis/ranking?materia_id={uuid.uuid4()}",
            f"/api/v1/analisis/reportes-rapidos?materia_id={uuid.uuid4()}",
            f"/api/v1/analisis/notas-finales?materia_id={uuid.uuid4()}",
            f"/api/v1/analisis/exportar-tps-sin-corregir?materia_id={uuid.uuid4()}",
            "/api/v1/analisis/monitor-general",
            "/api/v1/analisis/monitor-seguimiento",
            "/api/v1/analisis/monitor-seguimiento-extendido",
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 401, f"Expected 401 for {endpoint}"
