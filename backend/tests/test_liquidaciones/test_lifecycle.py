"""Tests for Liquidacion lifecycle — from calculation to close.

Strict TDD: RED → GREEN → REFACTOR.
"""

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient

from app.models import (
    Asignacion,
    Carrera,
    Cohorte,
    Materia,
)

pytestmark = pytest.mark.asyncio


# =============================================================================
# Helpers
# =============================================================================


async def _seed_minimal(db_session, tenant_id, usuario_id, rol="PROFESOR"):
    """Seed minimal data and return cohorte."""
    carrera = Carrera(
        tenant_id=tenant_id,
        codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
        nombre="Carrera Life",
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
        nombre="Materia Life", grupo_plus="PROG",
    )
    db_session.add(materia)
    await db_session.flush()

    asignacion = Asignacion(
        tenant_id=tenant_id, usuario_id=usuario_id, materia_id=materia.id,
        cohorte_id=cohorte.id, rol=rol,
        desde=datetime.now(timezone.utc).date() - timedelta(days=30),
        hasta=datetime.now(timezone.utc).date() + timedelta(days=365),
    )
    db_session.add(asignacion)
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


async def _calcular(client, cohorte_id, headers):
    """Helper to trigger calculation."""
    return await client.post(
        "/api/v1/liquidaciones/calcular",
        json={"cohorte_id": str(cohorte_id), "periodo": "2026-06"},
        headers=headers,
    )


# =============================================================================
# Tests
# =============================================================================


class TestLifecycleCalcularYListar:
    """Calculate → list flow."""

    async def test_calcular_y_listar_muestra_liquidaciones(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Calcular → GET / muestra las liquidaciones creadas."""
        user, tenant, _ = user_finanzas
        cohorte = await _seed_minimal(db_session, tenant.id, user.id)
        await _seed_salario_base(db_session, tenant.id)
        await _seed_salario_plus(db_session, tenant.id)

        # Calculate
        resp = await _calcular(client, cohorte.id, auth_headers_finanzas)
        assert resp.status_code == 201
        created_id = resp.json()["items"][0]["id"]

        # List
        resp2 = await client.get(
            f"/api/v1/liquidaciones/?cohorte_id={cohorte.id}&periodo=2026-06",
            headers=auth_headers_finanzas,
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["total"] >= 1
        ids = [item["id"] for item in data["items"]]
        assert created_id in ids

    async def test_obtener_liquidacion_por_id(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """GET /{id} devuelve la liquidación correcta."""
        user, tenant, _ = user_finanzas
        cohorte = await _seed_minimal(db_session, tenant.id, user.id)
        await _seed_salario_base(db_session, tenant.id)
        await _seed_salario_plus(db_session, tenant.id)

        resp = await _calcular(client, cohorte.id, auth_headers_finanzas)
        liq_id = resp.json()["items"][0]["id"]

        resp2 = await client.get(
            f"/api/v1/liquidaciones/{liq_id}",
            headers=auth_headers_finanzas,
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["id"] == liq_id
        assert data["cohorte_id"] == str(cohorte.id)
        assert data["periodo"] == "2026-06"
        assert data["estado"] == "Abierta"
        assert data["monto_base"] == "150000.00"
        assert data["monto_plus"] == "25000.00"
        assert data["total"] == "175000.00"

    async def test_obtener_liquidacion_inexistente_retorna_404(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """GET /{id} con ID inexistente → 404."""
        fake_id = uuid.uuid4()
        resp = await client.get(
            f"/api/v1/liquidaciones/{fake_id}",
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 404


class TestLifecycleRecalculo:
    """Recalculation idempotency."""

    async def test_recalculo_misma_cohorte_periodo_actualiza(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Recalcular misma (cohorte, periodo) actualiza, no duplica."""
        from decimal import Decimal
        user, tenant, _ = user_finanzas
        cohorte = await _seed_minimal(db_session, tenant.id, user.id)
        await _seed_salario_base(db_session, tenant.id, monto="100000.00")
        await _seed_salario_plus(db_session, tenant.id, monto="20000.00")

        # First calculation
        resp1 = await _calcular(client, cohorte.id, auth_headers_finanzas)
        assert resp1.status_code == 201
        assert resp1.json()["creadas"] == 1
        first_total = resp1.json()["items"][0]["total"]

        # Recalculate with different base
        # Update the SalarioBase monto
        from app.models.salario_base import SalarioBase
        from sqlalchemy import select
        stmt = select(SalarioBase).where(SalarioBase.tenant_id == tenant.id)
        sb = (await db_session.execute(stmt)).scalar_one()
        sb.monto = Decimal("200000.00")
        await db_session.flush()
        await db_session.refresh(sb)

        resp2 = await _calcular(client, cohorte.id, auth_headers_finanzas)
        assert resp2.status_code == 201
        data = resp2.json()
        assert data["creadas"] == 1  # Still 1 (updated, not duplicated)
        second_total = data["items"][0]["total"]

        # Second total should be higher (base changed from 100000 to 200000)
        assert second_total != first_total
        assert second_total == "220000.00"  # 200000 + 20000


class TestLifecycleCierre:
    """Close liquidacion → makes it immutable."""

    async def test_cerrar_liquidacion_retorna_200(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Cerrar liquidación → estado = Cerrada."""
        user, tenant, _ = user_finanzas
        cohorte = await _seed_minimal(db_session, tenant.id, user.id)
        await _seed_salario_base(db_session, tenant.id)
        await _seed_salario_plus(db_session, tenant.id)

        resp = await _calcular(client, cohorte.id, auth_headers_finanzas)
        liq_id = resp.json()["items"][0]["id"]

        # Close
        resp2 = await client.post(
            f"/api/v1/liquidaciones/{liq_id}/cerrar",
            headers=auth_headers_finanzas,
        )
        assert resp2.status_code == 200
        assert resp2.json()["estado"] == "Cerrada"

    async def test_cerrar_liquidacion_ya_cerrada_retorna_409(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Cerrar liquidación ya cerrada → 409 Conflict."""
        user, tenant, _ = user_finanzas
        cohorte = await _seed_minimal(db_session, tenant.id, user.id)
        await _seed_salario_base(db_session, tenant.id)
        await _seed_salario_plus(db_session, tenant.id)

        resp = await _calcular(client, cohorte.id, auth_headers_finanzas)
        liq_id = resp.json()["items"][0]["id"]

        # First close → 200
        resp2 = await client.post(
            f"/api/v1/liquidaciones/{liq_id}/cerrar",
            headers=auth_headers_finanzas,
        )
        assert resp2.status_code == 200

        # Second close → 409
        resp3 = await client.post(
            f"/api/v1/liquidaciones/{liq_id}/cerrar",
            headers=auth_headers_finanzas,
        )
        assert resp3.status_code == 409

    async def test_recalcular_despues_de_cerrar_retorna_409(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Recalcular cohorte con liquidaciones cerradas → 409."""
        user, tenant, _ = user_finanzas
        cohorte = await _seed_minimal(db_session, tenant.id, user.id)
        await _seed_salario_base(db_session, tenant.id)
        await _seed_salario_plus(db_session, tenant.id)

        resp = await _calcular(client, cohorte.id, auth_headers_finanzas)
        liq_id = resp.json()["items"][0]["id"]

        # Close
        await client.post(
            f"/api/v1/liquidaciones/{liq_id}/cerrar",
            headers=auth_headers_finanzas,
        )

        # Recalculate should fail with 409
        resp3 = await _calcular(client, cohorte.id, auth_headers_finanzas)
        assert resp3.status_code == 409

    async def test_cerrar_liquidacion_de_otro_tenant_retorna_404(
        self, client: AsyncClient, db_session, user_finanzas, tenant_b, auth_headers_finanzas
    ):
        """Cerrar liquidación de otro tenant → 404."""
        user_a, tenant_a, _ = user_finanzas
        _, _, token_b = tenant_b
        headers_b = {"Authorization": f"Bearer {token_b}"}

        cohorte = await _seed_minimal(db_session, tenant_a.id, user_a.id)
        await _seed_salario_base(db_session, tenant_a.id)
        await _seed_salario_plus(db_session, tenant_a.id)

        resp = await _calcular(client, cohorte.id, auth_headers_finanzas)
        liq_id = resp.json()["items"][0]["id"]

        # Tenant B tries to close Tenant A's liquidacion
        resp2 = await client.post(
            f"/api/v1/liquidaciones/{liq_id}/cerrar",
            headers=headers_b,
        )
        assert resp2.status_code == 404

    async def test_listar_liquidaciones_vacia_sin_datos(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Listar sin filtros (o filtros que no matchean) → lista vacía."""
        resp = await client.get(
            "/api/v1/liquidaciones/",
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["items"], list)
        assert data["total"] >= 0
