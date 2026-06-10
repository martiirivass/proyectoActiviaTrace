import uuid
from datetime import datetime, timedelta, timezone

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
from app.models import Permission, Role, RolePermission, Tenant, User, UserRole, UserTenant
from app.models.audit_log import AuditLog

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


async def _assign_permission(db_session, role, codename):
    module, action = codename.split(":", 1)
    perm = Permission(name=codename, module=module, action=action)
    db_session.add(perm)
    await db_session.flush()
    rp = RolePermission(
        role_id=role.id, permission_id=perm.id,
        tenant_id=role.tenant_id, scope="global",
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
