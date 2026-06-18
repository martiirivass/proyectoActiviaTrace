"""Tests for audit code logging on liquidaciones actions.

Every state-changing action must generate the correct audit code.
Strict TDD: RED → GREEN → REFACTOR.
"""

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.audit_codes import (
    SALARIO_BASE_CREAR,
    SALARIO_BASE_MODIFICAR,
    SALARIO_BASE_ELIMINAR,
    SALARIO_PLUS_CREAR,
    SALARIO_PLUS_MODIFICAR,
    SALARIO_PLUS_ELIMINAR,
    LIQUIDACION_CALCULAR,
    LIQUIDACION_CERRAR,
    FACTURA_CARGAR,
    FACTURA_ABONAR,
    FACTURA_ELIMINAR,
)
from app.models import (
    Asignacion,
    Carrera,
    Cohorte,
    Materia,
)
from app.models.audit_log import AuditLog

pytestmark = pytest.mark.asyncio


# =============================================================================
# Helpers
# =============================================================================


async def _get_audit_logs(db_session, tenant_id, accion=None):
    """Get audit logs for a tenant, optionally filtered by action."""
    stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
    if accion:
        stmt = stmt.where(AuditLog.accion == accion)
    stmt = stmt.order_by(AuditLog.created_at.desc())
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def _seed_minimal(db_session, tenant_id, usuario_id):
    """Seed minimal data for calculation and return cohorte."""
    carrera = Carrera(
        tenant_id=tenant_id,
        codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
        nombre="Carrera Audit",
    )
    db_session.add(carrera)
    await db_session.flush()

    cohorte = Cohorte(
        tenant_id=tenant_id, carrera_id=carrera.id,
        nombre=f"COH-{uuid.uuid4().hex[:6].upper()}", anio=2026,
    )
    db_session.add(cohorte)
    await db_session.flush()

    materia = Materia(
        tenant_id=tenant_id, codigo=f"MAT-{uuid.uuid4().hex[:6].upper()}",
        nombre="Materia Audit", grupo_plus="PROG",
    )
    db_session.add(materia)
    await db_session.flush()

    a = Asignacion(
        tenant_id=tenant_id, usuario_id=usuario_id, materia_id=materia.id,
        cohorte_id=cohorte.id, rol="PROFESOR",
        desde=datetime.now(timezone.utc).date() - timedelta(days=30),
        hasta=datetime.now(timezone.utc).date() + timedelta(days=365),
    )
    db_session.add(a)
    await db_session.flush()

    return cohorte


async def _seed_salario_base(db_session, tenant_id, rol="PROFESOR", monto="150000.00", desde="2026-01-01"):
    from app.models.salario_base import SalarioBase
    from datetime import date
    sb = SalarioBase(tenant_id=tenant_id, rol=rol, monto=monto, desde=date.fromisoformat(desde))
    db_session.add(sb)
    await db_session.flush()
    return sb


async def _seed_salario_plus(db_session, tenant_id, grupo="PROG", rol="PROFESOR", monto="25000.00", desde="2026-01-01"):
    from app.models.salario_plus import SalarioPlus
    from datetime import date
    sp = SalarioPlus(tenant_id=tenant_id, grupo=grupo, rol=rol, descripcion="Plus", monto=monto, desde=date.fromisoformat(desde))
    db_session.add(sp)
    await db_session.flush()
    return sp


# =============================================================================
# Tests
# =============================================================================


class TestAuditSalarioBase:
    """Audit codes for SalarioBase actions."""

    async def test_crear_salario_base_genera_audit(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """POST /grilla-salarial/base → audit SALARIO_BASE_CREAR."""
        _, tenant, _ = user_finanzas

        await client.post(
            "/api/v1/grilla-salarial/base",
            json={"rol": "PROFESOR", "monto": "150000.00", "desde": "2026-01-01"},
            headers=auth_headers_finanzas,
        )

        logs = await _get_audit_logs(db_session, tenant.id, accion=SALARIO_BASE_CREAR)
        assert len(logs) >= 1

    async def test_editar_salario_base_genera_audit(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """PUT /grilla-salarial/base/{id} → audit SALARIO_BASE_MODIFICAR."""
        _, tenant, _ = user_finanzas

        resp = await client.post(
            "/api/v1/grilla-salarial/base",
            json={"rol": "PROFESOR", "monto": "100000.00", "desde": "2026-01-01"},
            headers=auth_headers_finanzas,
        )
        base_id = resp.json()["id"]

        await client.put(
            f"/api/v1/grilla-salarial/base/{base_id}",
            json={"monto": "120000.00"},
            headers=auth_headers_finanzas,
        )

        logs = await _get_audit_logs(db_session, tenant.id, accion=SALARIO_BASE_MODIFICAR)
        assert len(logs) >= 1

    async def test_eliminar_salario_base_genera_audit(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """DELETE /grilla-salarial/base/{id} → audit SALARIO_BASE_ELIMINAR."""
        _, tenant, _ = user_finanzas

        resp = await client.post(
            "/api/v1/grilla-salarial/base",
            json={"rol": "PROFESOR", "monto": "100000.00", "desde": "2026-01-01"},
            headers=auth_headers_finanzas,
        )
        base_id = resp.json()["id"]

        await client.delete(
            f"/api/v1/grilla-salarial/base/{base_id}",
            headers=auth_headers_finanzas,
        )

        logs = await _get_audit_logs(db_session, tenant.id, accion=SALARIO_BASE_ELIMINAR)
        assert len(logs) >= 1


class TestAuditSalarioPlus:
    """Audit codes for SalarioPlus actions."""

    async def test_crear_salario_plus_genera_audit(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """POST /grilla-salarial/plus → audit SALARIO_PLUS_CREAR."""
        _, tenant, _ = user_finanzas

        await client.post(
            "/api/v1/grilla-salarial/plus",
            json={"grupo": "PROG", "rol": "PROFESOR", "descripcion": "Test", "monto": "25000.00", "desde": "2026-01-01"},
            headers=auth_headers_finanzas,
        )

        logs = await _get_audit_logs(db_session, tenant.id, accion=SALARIO_PLUS_CREAR)
        assert len(logs) >= 1


class TestAuditLiquidaciones:
    """Audit codes for Liquidacion actions."""

    async def test_calcular_liquidacion_genera_audit(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """POST /liquidaciones/calcular → audit LIQUIDACION_CALCULAR."""
        user, tenant, _ = user_finanzas
        cohorte = await _seed_minimal(db_session, tenant.id, user.id)
        await _seed_salario_base(db_session, tenant.id)
        await _seed_salario_plus(db_session, tenant.id)

        await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )

        logs = await _get_audit_logs(db_session, tenant.id, accion=LIQUIDACION_CALCULAR)
        assert len(logs) >= 1
        log = logs[0]
        assert log.detalle is not None
        assert "cohorte_id" in log.detalle
        assert log.detalle["periodo"] == "2026-06"

    async def test_cerrar_liquidacion_genera_audit(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """POST /liquidaciones/{id}/cerrar → audit LIQUIDACION_CERRAR."""
        user, tenant, _ = user_finanzas
        cohorte = await _seed_minimal(db_session, tenant.id, user.id)
        await _seed_salario_base(db_session, tenant.id)
        await _seed_salario_plus(db_session, tenant.id)

        resp_calc = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        liq_id = resp_calc.json()["items"][0]["id"]

        await client.post(
            f"/api/v1/liquidaciones/{liq_id}/cerrar",
            headers=auth_headers_finanzas,
        )

        logs = await _get_audit_logs(db_session, tenant.id, accion=LIQUIDACION_CERRAR)
        assert len(logs) >= 1
        log = logs[0]
        assert log.detalle is not None
        assert log.detalle["liquidacion_id"] == liq_id


class TestAuditFacturas:
    """Audit codes for Factura actions."""

    async def test_crear_factura_genera_audit(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """POST /facturas/ → audit FACTURA_CARGAR."""
        user, tenant, _ = user_finanzas

        await client.post(
            "/api/v1/facturas/",
            json={
                "usuario_id": str(user.id),
                "periodo": "2026-06",
                "detalle": "Honorarios junio",
                "referencia_archivo": "fact.pdf",
                "tamano_kb": "500.00",
            },
            headers=auth_headers_finanzas,
        )

        logs = await _get_audit_logs(db_session, tenant.id, accion=FACTURA_CARGAR)
        assert len(logs) >= 1

    async def test_abonar_factura_genera_audit(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """POST /facturas/{id}/abonar → audit FACTURA_ABONAR."""
        user, tenant, _ = user_finanzas

        resp = await client.post(
            "/api/v1/facturas/",
            json={
                "usuario_id": str(user.id),
                "periodo": "2026-06",
                "detalle": "Honorarios junio",
                "referencia_archivo": "fact.pdf",
                "tamano_kb": "500.00",
            },
            headers=auth_headers_finanzas,
        )
        factura_id = resp.json()["id"]

        await client.post(
            f"/api/v1/facturas/{factura_id}/abonar",
            headers=auth_headers_finanzas,
        )

        logs = await _get_audit_logs(db_session, tenant.id, accion=FACTURA_ABONAR)
        assert len(logs) >= 1

    async def test_eliminar_factura_genera_audit(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """DELETE /facturas/{id} → audit FACTURA_ELIMINAR."""
        user, tenant, _ = user_finanzas

        resp = await client.post(
            "/api/v1/facturas/",
            json={
                "usuario_id": str(user.id),
                "periodo": "2026-06",
                "detalle": "Honorarios junio",
                "referencia_archivo": "fact.pdf",
                "tamano_kb": "500.00",
            },
            headers=auth_headers_finanzas,
        )
        factura_id = resp.json()["id"]

        await client.delete(
            f"/api/v1/facturas/{factura_id}",
            headers=auth_headers_finanzas,
        )

        logs = await _get_audit_logs(db_session, tenant.id, accion=FACTURA_ELIMINAR)
        assert len(logs) >= 1


class TestAuditCodesExisten:
    """Verify audit code constants exist and have correct values."""

    def test_salario_base_codes_exist(self):
        assert SALARIO_BASE_CREAR == "SALARIO_BASE_CREAR"
        assert SALARIO_BASE_MODIFICAR == "SALARIO_BASE_MODIFICAR"
        assert SALARIO_BASE_ELIMINAR == "SALARIO_BASE_ELIMINAR"

    def test_salario_plus_codes_exist(self):
        assert SALARIO_PLUS_CREAR == "SALARIO_PLUS_CREAR"
        assert SALARIO_PLUS_MODIFICAR == "SALARIO_PLUS_MODIFICAR"
        assert SALARIO_PLUS_ELIMINAR == "SALARIO_PLUS_ELIMINAR"

    def test_liquidacion_codes_exist(self):
        assert LIQUIDACION_CALCULAR == "LIQUIDACION_CALCULAR"
        assert LIQUIDACION_CERRAR == "LIQUIDACION_CERRAR"

    def test_factura_codes_exist(self):
        assert FACTURA_CARGAR == "FACTURA_CARGAR"
        assert FACTURA_ABONAR == "FACTURA_ABONAR"
        assert FACTURA_ELIMINAR == "FACTURA_ELIMINAR"
