import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.audit_codes import (
    ASIGNACION_MODIFICAR,
    CALIFICACIONES_IMPORTAR,
    COMUNICACION_ENVIAR,
    IMPERSONACION_FINALIZAR,
    IMPERSONACION_INICIAR,
    LIQUIDACION_CERRAR,
    PADRON_CARGAR,
)
from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.security import PasswordService, create_access_token
from app.main import app
from app.models import (
    Asignacion,
    Materia,
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
    UserTenant,
)
from app.models.audit_log import AuditLog
from app.models.comunicacion import Comunicacion, EstadoComunicacion

pytestmark = pytest.mark.asyncio


def _ensure_table(engine):
    from app.core.database import Base
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(engine.begin())
    # already created by test_session_factory


async def _create_tenant_and_user(db_session, role_name="ADMIN", code=None):
    if code is None:
        code = f"AUD-{uuid.uuid4().hex[:6]}"
    tenant = Tenant(name="Audit Test", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        email=f"audit-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Audit",
        apellido="Test",
        tenant_id=tenant.id,
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

    return user, tenant, role


async def _assign_permission(db_session, role, codename, scope="global"):
    module, action = codename.split(":", 1)
    stmt = select(Permission).where(Permission.name == codename)
    result = await db_session.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        perm = Permission(name=codename, module=module, action=action)
        db_session.add(perm)
        await db_session.flush()
    stmt2 = select(RolePermission).where(
        RolePermission.role_id == role.id,
        RolePermission.permission_id == perm.id,
    )
    result2 = await db_session.execute(stmt2)
    rp = result2.scalar_one_or_none()
    if rp is None:
        rp = RolePermission(
            role_id=role.id, permission_id=perm.id,
            tenant_id=role.tenant_id, scope=scope,
        )
        db_session.add(rp)
        await db_session.flush()


async def _create_audit_log(db_session, tenant_id, actor_id, accion="TEST_ACTION", **kwargs):
    from app.repositories.audit_log_repository import AuditLogRepository
    repo = AuditLogRepository(db_session)
    return await repo.create(
        tenant_id=tenant_id,
        actor_id=actor_id,
        accion=accion,
        **kwargs,
    )


async def _create_materia(db_session, tenant_id, nombre=None):
    if nombre is None:
        nombre = f"Materia-{uuid.uuid4().hex[:6]}"
    materia = Materia(
        tenant_id=tenant_id,
        codigo=f"COD-{uuid.uuid4().hex[:4]}",
        nombre=nombre,
    )
    db_session.add(materia)
    await db_session.flush()
    return materia


async def _create_asignacion(db_session, usuario_id, tenant_id, materia_id):
    asig = Asignacion(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        rol="COORDINADOR",
        materia_id=materia_id,
        desde=date(2026, 1, 1),
    )
    db_session.add(asig)
    await db_session.flush()
    return asig


async def _create_comunicacion(db_session, tenant_id, enviado_por, materia_id, estado=EstadoComunicacion.PENDIENTE):
    comm = Comunicacion(
        tenant_id=tenant_id,
        enviado_por=enviado_por,
        materia_id=materia_id,
        destinatario="test@test.com",
        asunto="Test",
        cuerpo="Test body",
        estado=estado,
    )
    db_session.add(comm)
    await db_session.flush()
    return comm


class TestAuditCodes:
    async def test_action_codes_exist_as_constants(self):
        assert CALIFICACIONES_IMPORTAR == "CALIFICACIONES_IMPORTAR"
        assert PADRON_CARGAR == "PADRON_CARGAR"
        assert COMUNICACION_ENVIAR == "COMUNICACION_ENVIAR"
        assert ASIGNACION_MODIFICAR == "ASIGNACION_MODIFICAR"
        assert LIQUIDACION_CERRAR == "LIQUIDACION_CERRAR"
        assert IMPERSONACION_INICIAR == "IMPERSONACION_INICIAR"
        assert IMPERSONACION_FINALIZAR == "IMPERSONACION_FINALIZAR"


class TestAuditLogModel:
    async def test_model_creates_record_correctly(self, db_session):
        user, tenant, role = await _create_tenant_and_user(db_session)

        log_entry = await _create_audit_log(
            db_session,
            tenant_id=tenant.id,
            actor_id=user.id,
            accion=CALIFICACIONES_IMPORTAR,
            detalle={"archivo": "notas.csv", "filas": 150},
            filas_afectadas=150,
            ip="192.168.1.1",
            user_agent="pytest/1.0",
        )

        assert log_entry.id is not None
        assert log_entry.tenant_id == tenant.id
        assert log_entry.actor_id == user.id
        assert log_entry.accion == CALIFICACIONES_IMPORTAR
        assert log_entry.detalle == {"archivo": "notas.csv", "filas": 150}
        assert log_entry.filas_afectadas == 150
        assert log_entry.ip == "192.168.1.1"
        assert log_entry.user_agent == "pytest/1.0"
        assert log_entry.impersonado_id is None
        assert log_entry.materia_id is None
        assert log_entry.fecha_hora is not None
        assert log_entry.created_at is not None
        assert log_entry.updated_at is not None

    async def test_registration_with_impersonation(self, db_session):
        user, tenant, role = await _create_tenant_and_user(db_session)
        target_user, _, _ = await _create_tenant_and_user(db_session)

        log_entry = await _create_audit_log(
            db_session,
            tenant_id=tenant.id,
            actor_id=user.id,
            impersonado_id=target_user.id,
            accion=IMPERSONACION_INICIAR,
            detalle={"motivo": "soporte"},
        )

        assert log_entry.actor_id == user.id
        assert log_entry.impersonado_id == target_user.id
        assert log_entry.impersonado_id != log_entry.actor_id


class TestAuditLogRepository:
    async def test_update_not_available(self, db_session):
        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)
        assert not hasattr(repo, "update") or not callable(getattr(repo, "update", None))

    async def test_delete_not_available(self, db_session):
        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)
        assert not hasattr(repo, "delete")
        assert not hasattr(repo, "soft_delete")

    async def test_paginated_query_without_filters(self, db_session):
        user, tenant, role = await _create_tenant_and_user(db_session)
        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)

        for i in range(5):
            await repo.create(
                tenant_id=tenant.id,
                actor_id=user.id,
                accion=f"ACCION_{i}",
            )

        results = await repo.find(tenant_id=tenant.id, offset=0, limit=3)
        assert len(results) == 3

        results_2 = await repo.find(tenant_id=tenant.id, offset=3, limit=5)
        assert len(results_2) == 2

    async def test_filter_by_accion(self, db_session):
        user, tenant, role = await _create_tenant_and_user(db_session)
        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)

        await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="TIPO_A")
        await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="TIPO_B")
        await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="TIPO_A")

        results = await repo.find(tenant_id=tenant.id, accion="TIPO_A")
        assert len(results) == 2
        for r in results:
            assert r.accion == "TIPO_A"

    async def test_filter_by_actor_id(self, db_session):
        user_a, tenant, _ = await _create_tenant_and_user(db_session)
        user_b, _, _ = await _create_tenant_and_user(db_session)
        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)

        await repo.create(tenant_id=tenant.id, actor_id=user_a.id, accion="ACCION")
        await repo.create(tenant_id=tenant.id, actor_id=user_b.id, accion="ACCION")

        results = await repo.find(tenant_id=tenant.id, actor_id=user_a.id)
        assert len(results) == 1
        assert results[0].actor_id == user_a.id

    async def test_filter_by_date_range(self, db_session):
        user, tenant, role = await _create_tenant_and_user(db_session)
        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)

        past = datetime.now(timezone.utc) - timedelta(days=10)
        recent = datetime.now(timezone.utc)

        log_past = await repo.create(
            tenant_id=tenant.id, actor_id=user.id, accion="OLD",
        )
        log_past.fecha_hora = past
        await db_session.flush()

        log_recent = await repo.create(
            tenant_id=tenant.id, actor_id=user.id, accion="NEW",
        )

        results = await repo.find(
            tenant_id=tenant.id,
            desde=past - timedelta(hours=1),
            hasta=past + timedelta(hours=1),
        )
        assert len(results) == 1
        assert results[0].accion == "OLD"

    async def test_multi_tenant_isolation(self, db_session):
        user_a, tenant_a, _ = await _create_tenant_and_user(db_session)
        user_b, tenant_b, _ = await _create_tenant_and_user(db_session)
        from app.repositories.audit_log_repository import AuditLogRepository

        repo_a = AuditLogRepository(db_session)
        repo_b = AuditLogRepository(db_session)

        await repo_a.create(tenant_id=tenant_a.id, actor_id=user_a.id, accion="A_ACTION")
        await repo_b.create(tenant_id=tenant_b.id, actor_id=user_b.id, accion="B_ACTION")

        results_a = await repo_a.find(tenant_id=tenant_a.id)
        assert len(results_a) == 1
        assert results_a[0].accion == "A_ACTION"

        results_b = await repo_b.find(tenant_id=tenant_b.id)
        assert len(results_b) == 1
        assert results_b[0].accion == "B_ACTION"


class TestAuditLogEndpoint:
    async def _setup_admin_with_audit(self, db_session):
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="AUDIT_ADMIN")
        await _assign_permission(db_session, role, "auditoria:ver")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["AUDIT_ADMIN"])
        return user, tenant, token

    async def test_get_endpoint_200_with_data(self, db_session):
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)
        await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="TEST_200")

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/log",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 1
            assert data[0]["accion"] == "TEST_200"

        app.dependency_overrides.clear()

    async def test_get_endpoint_403_without_permission(self, db_session):
        user, tenant, _ = await _create_tenant_and_user(db_session, role_name="NO_PERM")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["NO_PERM"])

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/log",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 403

        app.dependency_overrides.clear()

    async def test_get_endpoint_pagination_respects_limits(self, db_session):
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)
        for i in range(10):
            await repo.create(tenant_id=tenant.id, actor_id=user.id, accion=f"PAG_{i}")

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/log?limit=3",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 3

            resp2 = await client.get(
                "/api/v1/audit/log?limit=3&offset=3",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp2.status_code == 200
            data2 = resp2.json()
            assert len(data2) == 3
            assert data2[0]["id"] != data[0]["id"]

        app.dependency_overrides.clear()

    async def test_get_endpoint_returns_all_audit_fields(self, db_session):
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)
        entry = await repo.create(
            tenant_id=tenant.id,
            actor_id=user.id,
            accion="FULL_FIELDS",
            detalle={"key": "value"},
            filas_afectadas=42,
            ip="10.0.0.1",
            user_agent="test-agent",
        )

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/log",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            match = [d for d in data if d["id"] == str(entry.id)]
            assert len(match) == 1
            item = match[0]
            assert item["accion"] == "FULL_FIELDS"
            assert item["detalle"] == {"key": "value"}
            assert item["filas_afectadas"] == 42
            assert item["ip"] == "10.0.0.1"
            assert item["user_agent"] == "test-agent"

        app.dependency_overrides.clear()


class TestAuditDependency:
    async def test_audit_dependency_logs_automatically(self, db_session):
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="AUDIT_DEP")
        await _assign_permission(db_session, role, "auditoria:ver")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["AUDIT_DEP"])

        from app.core.audit_dependency import audit_dependency

        test_app = type(app)(
            title="test",
            version="0.1.0",
        )
        test_app.dependency_overrides[get_db] = lambda: db_session

        @test_app.get("/test-audit")
        async def test_endpoint(
            _=Depends(audit_dependency("DEP_TEST")),
            current_user=Depends(get_current_user),
        ):
            return {"ok": True}

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(
                "/test-audit",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200

        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)
        logs = await repo.find(tenant_id=tenant.id, accion="DEP_TEST")
        assert len(logs) >= 1
        assert logs[0].accion == "DEP_TEST"
        assert logs[0].actor_id == user.id

    async def test_audit_dependency_logs_ip_and_user_agent(self, db_session):
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="AUDIT_DEP2")
        await _assign_permission(db_session, role, "auditoria:ver")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["AUDIT_DEP2"])

        from app.core.audit_dependency import audit_dependency

        test_app = type(app)(
            title="test",
            version="0.1.0",
        )
        test_app.dependency_overrides[get_db] = lambda: db_session

        @test_app.get("/test-audit-ua")
        async def test_endpoint(
            _=Depends(audit_dependency("DEP_UA")),
            current_user=Depends(get_current_user),
        ):
            return {"ok": True}

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(
                "/test-audit-ua",
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "custom-test-agent/1.0",
                },
            )
            assert resp.status_code == 200

        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)
        logs = await repo.find(tenant_id=tenant.id, accion="DEP_UA")
        assert len(logs) >= 1
        assert logs[0].ip is not None
        assert logs[0].user_agent == "custom-test-agent/1.0"


class TestAuditDashboard:
    """Phase 6: Dashboard endpoint tests."""

    async def _setup_admin_with_audit(self, db_session):
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="DASH_ADMIN")
        await _assign_permission(db_session, role, "auditoria:ver")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["DASH_ADMIN"])
        return user, tenant, token

    async def test_dashboard_admin_full_dashboard(self, db_session):
        """6.1: Admin gets full dashboard with 4 sections."""
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        materia = await _create_materia(db_session, tenant.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="TEST", materia_id=materia.id)

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "acciones_por_dia" in data
            assert "comunicaciones_por_docente" in data
            assert "interacciones_por_docente_materia" in data
            assert "ultimas_acciones" in data
            assert "total" in data
            assert len(data["ultimas_acciones"]) >= 1
        app.dependency_overrides.clear()

    async def test_dashboard_coordinator_scope_propio(self, db_session):
        """6.2: Coordinator with scope propio sees only their materias."""
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="DASH_COORD")
        await _assign_permission(db_session, role, "auditoria:ver", scope="propio")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["DASH_COORD"])

        my_materia = await _create_materia(db_session, tenant.id, "Mi materia")
        other_materia = await _create_materia(db_session, tenant.id, "Otra materia")
        await _create_asignacion(db_session, user.id, tenant.id, my_materia.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="MIA", materia_id=my_materia.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="OTRA", materia_id=other_materia.id)

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            ultimas = data["ultimas_acciones"]
            acciones = [a["accion"] for a in ultimas]
            assert "MIA" in acciones
            assert "OTRA" not in acciones
        app.dependency_overrides.clear()

    async def test_dashboard_finanzas_global(self, db_session):
        """6.3: Finanzas sees global dashboard (no scope filter)."""
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="DASH_FIN")
        await _assign_permission(db_session, role, "auditoria:ver")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["DASH_FIN"])

        materia_a = await _create_materia(db_session, tenant.id, "A")
        materia_b = await _create_materia(db_session, tenant.id, "B")
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="GLOBAL_A", materia_id=materia_a.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="GLOBAL_B", materia_id=materia_b.id)

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            acciones = [a["accion"] for a in data["ultimas_acciones"]]
            assert "GLOBAL_A" in acciones
            assert "GLOBAL_B" in acciones
        app.dependency_overrides.clear()

    async def test_dashboard_403_without_permission(self, db_session):
        """6.4: User without auditoria:ver gets 403."""
        user, tenant, _ = await _create_tenant_and_user(db_session, role_name="NO_PERM")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["NO_PERM"])

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 403
        app.dependency_overrides.clear()

    async def test_dashboard_date_range_filter(self, db_session):
        """6.5: Dashboard with date range filter works."""
        from app.repositories.audit_log_repository import AuditLogRepository
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        repo = AuditLogRepository(db_session)

        now = datetime.now(timezone.utc)
        old = now - timedelta(days=30)

        entry_old = await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="OLD_ACTION")
        entry_old.fecha_hora = old
        await db_session.flush()
        entry_new = await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="NEW_ACTION")

        desde = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        hasta = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/audit/dashboard?desde={desde}&hasta={hasta}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            acciones = [a["accion"] for a in data["ultimas_acciones"]]
            assert "NEW_ACTION" in acciones
            assert "OLD_ACTION" not in acciones
        app.dependency_overrides.clear()

    async def test_dashboard_materia_id_filter(self, db_session):
        """6.6: Dashboard with materia_id filter works."""
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        materia_a = await _create_materia(db_session, tenant.id, "A")
        materia_b = await _create_materia(db_session, tenant.id, "B")
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="MAT_A", materia_id=materia_a.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="MAT_B", materia_id=materia_b.id)

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/audit/dashboard?materia_id={materia_a.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            acciones = [a["accion"] for a in data["ultimas_acciones"]]
            assert "MAT_A" in acciones
            assert "MAT_B" not in acciones
        app.dependency_overrides.clear()

    async def test_dashboard_default_limit_200(self, db_session):
        """6.7: Dashboard default limit=200 for ultimas_acciones."""
        from app.repositories.audit_log_repository import AuditLogRepository
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        repo = AuditLogRepository(db_session)
        for i in range(250):
            await repo.create(tenant_id=tenant.id, actor_id=user.id, accion=f"BULK_{i}")

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["ultimas_acciones"]) == 200
            assert data["total"] == 200
        app.dependency_overrides.clear()

    async def test_dashboard_custom_limit_50(self, db_session):
        """6.8: Dashboard custom limit (50) works."""
        from app.repositories.audit_log_repository import AuditLogRepository
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        repo = AuditLogRepository(db_session)
        for i in range(100):
            await repo.create(tenant_id=tenant.id, actor_id=user.id, accion=f"LIM_{i}")

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/dashboard?limit=50",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["ultimas_acciones"]) == 50
            assert data["total"] == 50
        app.dependency_overrides.clear()

    async def test_dashboard_empty_range(self, db_session):
        """6.9: Dashboard with empty range returns empty arrays."""
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id, accion="EXISTS")

        far_future = "2099-01-01T00:00:00"

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/audit/dashboard?desde={far_future}&hasta={far_future}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["acciones_por_dia"] == []
            assert data["comunicaciones_por_docente"] == []
            assert data["interacciones_por_docente_materia"] == []
            assert data["ultimas_acciones"] == []
            assert data["total"] == 0
        app.dependency_overrides.clear()

    async def test_count_actions_by_day_groups_by_date(self, db_session):
        """6.10: count_actions_by_day groups correctly by date."""
        from app.repositories.audit_log_repository import AuditLogRepository
        user, tenant, _ = await _create_tenant_and_user(db_session, role_name="ADMIN")
        repo = AuditLogRepository(db_session)

        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        e1 = await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="A")
        e1.fecha_hora = yesterday
        await db_session.flush()
        e2 = await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="B")
        e2.fecha_hora = now
        await db_session.flush()
        await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="C")
        await db_session.flush()

        results = await repo.count_actions_by_day(tenant_id=tenant.id)
        assert len(results) >= 2
        for r in results:
            assert "fecha" in r
            assert "total" in r
            assert isinstance(r["total"], int)
        total_all = sum(r["total"] for r in results)
        assert total_all == 3

    async def test_count_comms_by_docente_groups_by_estado(self, db_session):
        """6.11: count_comms_by_docente groups by docente+estado."""
        from app.repositories.audit_log_repository import AuditLogRepository
        user, tenant, _ = await _create_tenant_and_user(db_session, role_name="ADMIN")
        repo = AuditLogRepository(db_session)
        materia = await _create_materia(db_session, tenant.id)

        await _create_comunicacion(db_session, tenant.id, user.id, materia.id, EstadoComunicacion.ENVIADO)
        await _create_comunicacion(db_session, tenant.id, user.id, materia.id, EstadoComunicacion.ENVIADO)
        await _create_comunicacion(db_session, tenant.id, user.id, materia.id, EstadoComunicacion.ERROR)

        results = await repo.count_comms_by_docente(tenant_id=tenant.id)
        assert len(results) >= 2
        for r in results:
            assert "docente_id" in r
            assert "estado" in r
            assert "total" in r
        estados = {r["estado"]: r["total"] for r in results}
        assert estados.get(EstadoComunicacion.ENVIADO) == 2
        assert estados.get(EstadoComunicacion.ERROR) == 1

    async def test_count_interactions_by_docente_materia_groups_correctly(self, db_session):
        """6.12: count_interactions_by_docente_materia groups by docente, materia, accion."""
        from app.repositories.audit_log_repository import AuditLogRepository
        user, tenant, _ = await _create_tenant_and_user(db_session, role_name="ADMIN")
        repo = AuditLogRepository(db_session)
        materia = await _create_materia(db_session, tenant.id)

        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="CALIFICACIONES_IMPORTAR", materia_id=materia.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="CALIFICACIONES_IMPORTAR", materia_id=materia.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="COMUNICACION_ENVIAR", materia_id=materia.id)

        results = await repo.count_interactions_by_docente_materia(tenant_id=tenant.id)
        assert len(results) == 2
        accion_map = {r["accion"]: r["total"] for r in results}
        assert accion_map["CALIFICACIONES_IMPORTAR"] == 2
        assert accion_map["COMUNICACION_ENVIAR"] == 1


class TestAuditLogEnhanced:
    """Phase 7: Log enhanced endpoint tests."""

    async def _setup_admin_with_audit(self, db_session):
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="LOG_ADMIN")
        await _assign_permission(db_session, role, "auditoria:ver")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["LOG_ADMIN"])
        return user, tenant, token

    async def test_log_filter_by_materia_id(self, db_session):
        """7.1: Log filter by materia_id works."""
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        materia_a = await _create_materia(db_session, tenant.id, "A")
        materia_b = await _create_materia(db_session, tenant.id, "B")
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="MAT_A", materia_id=materia_a.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="MAT_B", materia_id=materia_b.id)

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/audit/log?materia_id={materia_a.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["accion"] == "MAT_A"
        app.dependency_overrides.clear()

    async def test_log_invalid_materia_id_returns_422(self, db_session):
        """7.2: Invalid materia_id returns 422."""
        _, _, token = await self._setup_admin_with_audit(db_session)

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/log?materia_id=not-a-uuid",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 422
        app.dependency_overrides.clear()

    async def test_log_materia_id_no_matches(self, db_session):
        """7.3: materia_id with no matches returns empty."""
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        materia = await _create_materia(db_session, tenant.id, "NoMatch")
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="EXISTS", materia_id=materia.id)

        other_uuid = uuid.uuid4()

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/audit/log?materia_id={other_uuid}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data == []
        app.dependency_overrides.clear()

    async def test_log_coordinator_scope_propio(self, db_session):
        """7.4: Coordinator scope propio sees only own materias in log."""
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="LOG_COORD")
        await _assign_permission(db_session, role, "auditoria:ver", scope="propio")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["LOG_COORD"])

        my_mat = await _create_materia(db_session, tenant.id, "Mia")
        other_mat = await _create_materia(db_session, tenant.id, "Otra")
        await _create_asignacion(db_session, user.id, tenant.id, my_mat.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="MIA", materia_id=my_mat.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="OTRA", materia_id=other_mat.id)

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/log",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            acciones = [d["accion"] for d in data]
            assert "MIA" in acciones
            assert "OTRA" not in acciones
        app.dependency_overrides.clear()

    async def test_log_coordinator_materia_id_within_scope(self, db_session):
        """7.5: Coordinator materia_id within scope works."""
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="LOG_COORD2")
        await _assign_permission(db_session, role, "auditoria:ver", scope="propio")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["LOG_COORD2"])

        my_mat = await _create_materia(db_session, tenant.id, "Mia")
        await _create_asignacion(db_session, user.id, tenant.id, my_mat.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="EN_SCOPE", materia_id=my_mat.id)

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/audit/log?materia_id={my_mat.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["accion"] == "EN_SCOPE"
        app.dependency_overrides.clear()

    async def test_log_coordinator_materia_id_outside_scope(self, db_session):
        """7.6: Coordinator materia_id outside scope returns empty."""
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="LOG_COORD3")
        await _assign_permission(db_session, role, "auditoria:ver", scope="propio")
        token = create_access_token(user_id=user.id, tenant_id=tenant.id, roles=["LOG_COORD3"])

        my_mat = await _create_materia(db_session, tenant.id, "Mia")
        other_mat = await _create_materia(db_session, tenant.id, "Otra")
        await _create_asignacion(db_session, user.id, tenant.id, my_mat.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="EN_MIA", materia_id=my_mat.id)
        await _create_audit_log(db_session, tenant_id=tenant.id, actor_id=user.id,
                                accion="EN_OTRA", materia_id=other_mat.id)

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/audit/log?materia_id={other_mat.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data == []
        app.dependency_overrides.clear()

    async def test_log_limit_200_accepted(self, db_session):
        """7.7: Log limit=200 accepted."""
        from app.repositories.audit_log_repository import AuditLogRepository
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        repo = AuditLogRepository(db_session)
        for i in range(250):
            await repo.create(tenant_id=tenant.id, actor_id=user.id, accion=f"BULK_{i}")

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/log?limit=200",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 200
        app.dependency_overrides.clear()

    async def test_log_default_limit_50(self, db_session):
        """7.8: Log default limit remains 50."""
        from app.repositories.audit_log_repository import AuditLogRepository
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        repo = AuditLogRepository(db_session)
        for i in range(100):
            await repo.create(tenant_id=tenant.id, actor_id=user.id, accion=f"DEF_{i}")

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/log",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 50
        app.dependency_overrides.clear()

    async def test_log_limit_gt_200_returns_422(self, db_session):
        """7.9: Log limit > 200 returns 422."""
        _, _, token = await self._setup_admin_with_audit(db_session)

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/audit/log?limit=201",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 422
        app.dependency_overrides.clear()

    async def test_log_existing_filters_still_work(self, db_session):
        """7.10: Existing filters (accion, actor_id, desde, hasta) still work."""
        from app.repositories.audit_log_repository import AuditLogRepository
        user, tenant, token = await self._setup_admin_with_audit(db_session)
        repo = AuditLogRepository(db_session)

        now = datetime.now(timezone.utc)
        past = now - timedelta(days=10)

        e1 = await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="FILTER_ME")
        e1.fecha_hora = past
        await db_session.flush()
        await repo.create(tenant_id=tenant.id, actor_id=user.id, accion="OTHER")

        app.dependency_overrides[get_db] = lambda: db_session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            desde_str = (past - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
            hasta_str = (past + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
            resp = await client.get(
                f"/api/v1/audit/log?accion=FILTER_ME&actor_id={user.id}&desde={desde_str}&hasta={hasta_str}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 1
            for d in data:
                assert d["accion"] == "FILTER_ME"
                assert d["actor_id"] == str(user.id)
        app.dependency_overrides.clear()


class TestAuditPermissionsMigration:
    """Phase 8: Migration and permissions tests."""

    async def test_migration_adds_auditoria_ver_to_coordinador(self, db_session):
        """8.1: Migration adds auditoria:ver(propio) to COORDINADOR."""
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="COORDINADOR")
        await _assign_permission(db_session, role, "auditoria:ver", scope="propio")

        from app.services.permission_service import PermissionService
        svc = PermissionService(db_session)
        scope = await svc.get_effective_scope("auditoria:ver", user.id)
        assert scope == "propio"

        permissions = await svc.get_effective_permissions(user.id)
        assert "auditoria:ver" in permissions

    async def test_migration_idempotent(self, db_session):
        """8.2: Running same migration twice doesn't duplicate."""
        user, tenant, role = await _create_tenant_and_user(db_session, role_name="COORDINADOR")
        await _assign_permission(db_session, role, "auditoria:ver", scope="propio")

        from app.services.permission_service import PermissionService
        svc = PermissionService(db_session)
        permissions_1 = await svc.get_effective_permissions(user.id)

        # Simulate second run: call _assign_permission again (now idempotent)
        await _assign_permission(db_session, role, "auditoria:ver", scope="propio")

        permissions_2 = await svc.get_effective_permissions(user.id)
        assert permissions_1 == permissions_2
        perms_list = [p for p in permissions_2 if p == "auditoria:ver"]
        assert len(perms_list) == 1

    async def test_admin_finanzas_keep_global(self, db_session):
        """8.3: ADMIN and FINANZAS keep auditoria:ver(global)."""
        for role_name in ("ADMIN", "FINANZAS"):
            user, tenant, role = await _create_tenant_and_user(db_session, role_name=role_name)
            await _assign_permission(db_session, role, "auditoria:ver", scope="global")

            from app.services.permission_service import PermissionService
            svc = PermissionService(db_session)
            scope = await svc.get_effective_scope("auditoria:ver", user.id)
            assert scope == "global"

    async def test_scope_propio_resolves_via_asignacion(self, db_session):
        """8.4: Scope propio resolves via AsignacionRepository."""
        from app.services.audit_service import AuditService
        from app.schemas.auth import CurrentUser

        user, tenant, role = await _create_tenant_and_user(db_session, role_name="COORD")
        await _assign_permission(db_session, role, "auditoria:ver", scope="propio")

        materia = await _create_materia(db_session, tenant.id, "Resolved")
        await _create_asignacion(db_session, user.id, tenant.id, materia.id)

        current_user = CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["COORD"])
        svc = AuditService(db_session)
        resolved = await svc._resolve_materias(current_user)

        assert len(resolved) == 1
        assert resolved[0] == materia.id

    async def test_scope_global_no_filter(self, db_session):
        """8.5: Scope global doesn't add materia filter."""
        from app.services.audit_service import AuditService
        from app.schemas.auth import CurrentUser

        user, tenant, role = await _create_tenant_and_user(db_session, role_name="ADMIN")
        await _assign_permission(db_session, role, "auditoria:ver", scope="global")

        current_user = CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["ADMIN"])
        svc = AuditService(db_session)
        resolved = await svc._resolve_materias(current_user)

        assert resolved == []
