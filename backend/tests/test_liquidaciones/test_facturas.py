"""Tests for Factura CRUD and state transitions.

Covers all scenarios from *facturas-spec.md* (14 scenarios).
Strict TDD: RED → GREEN → REFACTOR.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models import Materia

pytestmark = pytest.mark.asyncio


# =============================================================================
# Helpers
# =============================================================================


async def _create_minimal_factura(client, headers, usuario_id, periodo="2026-06", **extra):
    """Create a basic factura and return the response."""
    payload = {
        "usuario_id": str(usuario_id),
        "periodo": periodo,
        "detalle": "Honorarios test",
        "referencia_archivo": "fact_test.pdf",
        "tamano_kb": "500.00",
        **extra,
    }
    return await client.post("/api/v1/facturas/", json=payload, headers=headers)


async def _create_materia_in_tenant(db_session, tenant_id):
    """Create a Materia in the given tenant and return it."""
    m = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:6].upper()}",
        nombre="Factura Materia Test",
    )
    db_session.add(m)
    await db_session.flush()
    await db_session.refresh(m)
    return m


# =============================================================================
# Tests
# =============================================================================


class TestFacturaCrear:
    """Factura creation scenarios."""

    async def test_crear_factura_periodo_sin_comision(
        self, client: AsyncClient, db_session, user_finanzas, factura_data, auth_headers_finanzas
    ):
        """Crear factura por período (sin materia_id) → 201, Pendiente."""
        user, tenant, _ = user_finanzas

        resp = await _create_minimal_factura(
            client, auth_headers_finanzas,
            usuario_id=user.id,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["estado"] == "Pendiente"
        assert data["materia_id"] is None
        assert data["periodo"] == "2026-06"
        assert data["detalle"] == "Honorarios test"
        assert data["usuario_id"] == str(user.id)

    async def test_crear_factura_con_materia_id(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """⚠️ PA-24: Crear factura asociada a materia específica → 201."""
        user, tenant, _ = user_finanzas
        materia = await _create_materia_in_tenant(db_session, tenant.id)

        resp = await _create_minimal_factura(
            client, auth_headers_finanzas,
            usuario_id=user.id,
            materia_id=str(materia.id),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["materia_id"] == str(materia.id)

    async def test_crear_factura_usuario_inexistente_retorna_404(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Crear factura con usuario_id inexistente → 404."""
        fake_id = uuid.uuid4()
        resp = await _create_minimal_factura(
            client, auth_headers_finanzas,
            usuario_id=fake_id,
        )
        assert resp.status_code == 404

    async def test_crear_factura_periodo_invalido_retorna_422(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Crear factura con periodo inválido → 422."""
        user, tenant, _ = user_finanzas

        # Invalid month
        resp = await _create_minimal_factura(
            client, auth_headers_finanzas,
            usuario_id=user.id, periodo="2026-13",
        )
        assert resp.status_code == 422

        # Wrong format
        resp2 = await _create_minimal_factura(
            client, auth_headers_finanzas,
            usuario_id=user.id, periodo="06-2026",
        )
        assert resp2.status_code == 422

    async def test_crear_factura_sin_permiso_retorna_403(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_no_perms
    ):
        """Crear factura sin permiso facturas:gestionar → 403."""
        user, _, _ = user_finanzas
        resp = await _create_minimal_factura(
            client, auth_headers_no_perms,
            usuario_id=user.id,
        )
        assert resp.status_code == 403

    async def test_crear_factura_con_materia_de_otro_tenant_retorna_404(
        self, client: AsyncClient, db_session, user_finanzas, tenant_b, auth_headers_finanzas
    ):
        """Crear factura con materia_id de otro tenant → 404."""
        user_a, tenant_a, _ = user_finanzas
        _, tenant_b_data, _ = tenant_b

        # Materia belongs to tenant_b
        materia_b = await _create_materia_in_tenant(db_session, tenant_b_data.id)

        resp = await _create_minimal_factura(
            client, auth_headers_finanzas,
            usuario_id=user_a.id,
            materia_id=str(materia_b.id),
        )
        assert resp.status_code == 404


class TestFacturaObtener:
    """Factura retrieval scenarios."""

    async def test_obtener_factura_por_id(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Obtener factura por ID → 200 con todos los campos."""
        user, tenant, _ = user_finanzas

        resp = await _create_minimal_factura(
            client, auth_headers_finanzas, usuario_id=user.id,
        )
        factura_id = resp.json()["id"]

        resp2 = await client.get(
            f"/api/v1/facturas/{factura_id}",
            headers=auth_headers_finanzas,
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["id"] == factura_id
        assert data["usuario_id"] == str(user.id)
        assert data["periodo"] == "2026-06"
        assert data["detalle"] == "Honorarios test"
        assert data["referencia_archivo"] == "fact_test.pdf"
        assert data["tamano_kb"] == "500.00"
        assert data["estado"] == "Pendiente"
        assert data["cargada_at"] is not None

    async def test_obtener_factura_inexistente_retorna_404(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Obtener factura con ID inexistente → 404."""
        fake_id = uuid.uuid4()
        resp = await client.get(
            f"/api/v1/facturas/{fake_id}",
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 404

    async def test_obtener_factura_de_otro_tenant_retorna_404(
        self, client: AsyncClient, db_session, user_finanzas, tenant_b, auth_headers_finanzas
    ):
        """Obtener factura de otro tenant → 404."""
        user_a, tenant_a, _ = user_finanzas
        _, _, token_b = tenant_b
        headers_b = {"Authorization": f"Bearer {token_b}"}

        resp = await _create_minimal_factura(
            client, auth_headers_finanzas, usuario_id=user_a.id,
        )
        factura_id = resp.json()["id"]

        resp2 = await client.get(
            f"/api/v1/facturas/{factura_id}",
            headers=headers_b,
        )
        assert resp2.status_code == 404


class TestFacturaAbonar:
    """Factura payment (state transition) scenarios."""

    async def test_abonar_factura_retorna_200(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Abonar factura → estado=Abonada, abonada_at seteado."""
        user, tenant, _ = user_finanzas

        resp = await _create_minimal_factura(
            client, auth_headers_finanzas, usuario_id=user.id,
        )
        factura_id = resp.json()["id"]

        resp2 = await client.post(
            f"/api/v1/facturas/{factura_id}/abonar",
            headers=auth_headers_finanzas,
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["estado"] == "Abonada"
        assert data["abonada_at"] is not None

    async def test_abonar_factura_ya_abonada_retorna_409(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Abonar factura ya abonada → 409 Conflict."""
        user, tenant, _ = user_finanzas

        resp = await _create_minimal_factura(
            client, auth_headers_finanzas, usuario_id=user.id,
        )
        factura_id = resp.json()["id"]

        # First abonar → 200
        resp2 = await client.post(
            f"/api/v1/facturas/{factura_id}/abonar",
            headers=auth_headers_finanzas,
        )
        assert resp2.status_code == 200

        # Second abonar → 409
        resp3 = await client.post(
            f"/api/v1/facturas/{factura_id}/abonar",
            headers=auth_headers_finanzas,
        )
        assert resp3.status_code == 409

    async def test_abonar_factura_sin_permiso_retorna_403(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas, auth_headers_no_perms
    ):
        """Abonar factura sin permiso → 403."""
        user, tenant, _ = user_finanzas

        resp = await _create_minimal_factura(
            client, auth_headers_finanzas, usuario_id=user.id,
        )
        factura_id = resp.json()["id"]

        resp2 = await client.post(
            f"/api/v1/facturas/{factura_id}/abonar",
            headers=auth_headers_no_perms,
        )
        assert resp2.status_code == 403


class TestFacturaEliminar:
    """Factura soft delete scenarios."""

    async def test_eliminar_factura_retorna_204(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Soft delete factura → 204, luego GET devuelve 404."""
        user, tenant, _ = user_finanzas

        resp = await _create_minimal_factura(
            client, auth_headers_finanzas, usuario_id=user.id,
        )
        factura_id = resp.json()["id"]

        # Delete
        resp2 = await client.delete(
            f"/api/v1/facturas/{factura_id}",
            headers=auth_headers_finanzas,
        )
        assert resp2.status_code == 204

        # Get after delete → 404
        resp3 = await client.get(
            f"/api/v1/facturas/{factura_id}",
            headers=auth_headers_finanzas,
        )
        assert resp3.status_code == 404

    async def test_eliminar_factura_inexistente_retorna_404(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Eliminar factura inexistente → 404."""
        fake_id = uuid.uuid4()
        resp = await client.delete(
            f"/api/v1/facturas/{fake_id}",
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 404


class TestFacturaListar:
    """Factura listing/filtering scenarios."""

    async def test_listar_facturas_por_periodo_y_estado(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Listar facturas filtrado por periodo y estado."""
        user, tenant, _ = user_finanzas

        # Create one Pendiente for 2026-06
        await _create_minimal_factura(
            client, auth_headers_finanzas, usuario_id=user.id, periodo="2026-06",
        )

        # Create one Abonada for 2026-05
        resp2 = await _create_minimal_factura(
            client, auth_headers_finanzas, usuario_id=user.id, periodo="2026-05",
        )
        factura2_id = resp2.json()["id"]
        await client.post(
            f"/api/v1/facturas/{factura2_id}/abonar",
            headers=auth_headers_finanzas,
        )

        # Filter by estado=Pendiente & periodo=2026-06
        resp3 = await client.get(
            "/api/v1/facturas/?estado=Pendiente&periodo=2026-06",
            headers=auth_headers_finanzas,
        )
        assert resp3.status_code == 200
        data = resp3.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["estado"] == "Pendiente"
            assert item["periodo"] == "2026-06"

    async def test_listar_facturas_filtro_usuario(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Listar facturas filtrado por usuario_id."""
        user, tenant, _ = user_finanzas

        # Create two users
        from app.models import Tenant, User, UserTenant
        user2 = User(tenant_id=tenant.id, email=f"other-{uuid.uuid4().hex[:8]}@test.com",
                      legajo=f"LEG-{uuid.uuid4().hex[:8]}", nombre="Other", apellido="User",
                      password_hash="hash")
        db_session.add(user2)
        await db_session.flush()
        ut2 = UserTenant(user_id=user2.id, tenant_id=tenant.id, is_active=True)
        db_session.add(ut2)
        await db_session.flush()

        await _create_minimal_factura(client, auth_headers_finanzas, usuario_id=user.id)
        await _create_minimal_factura(client, auth_headers_finanzas, usuario_id=user2.id)

        resp = await client.get(
            f"/api/v1/facturas/?usuario_id={user.id}",
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["usuario_id"] == str(user.id)

    async def test_multi_tenant_aislamiento_facturas(
        self, client: AsyncClient, db_session, user_finanzas, tenant_b, auth_headers_finanzas
    ):
        """Tenant B no ve facturas de Tenant A."""
        user_a, _, _ = user_finanzas
        _, _, token_b = tenant_b
        headers_b = {"Authorization": f"Bearer {token_b}"}

        await _create_minimal_factura(client, auth_headers_finanzas, usuario_id=user_a.id)

        resp = await client.get("/api/v1/facturas/", headers=headers_b)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
