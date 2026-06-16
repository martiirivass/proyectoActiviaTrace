"""Tests for endpoint-level permission enforcement.

Every endpoint that requires a permission should:
- ✅ Return 200/201/204 when the user HAS the permission
- ❌ Return 403 when the user does NOT have the permission

Strict TDD: RED → GREEN → REFACTOR.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models import Materia

pytestmark = pytest.mark.asyncio


# =============================================================================
# Grilla Salarial permissions
# =============================================================================


class TestGrillaPermisos:
    """grilla-salarial:* permissions."""

    async def test_listar_base_con_permiso_retorna_200(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """GET /grilla-salarial/base con permiso → 200."""
        resp = await client.get(
            "/api/v1/grilla-salarial/base",
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 200

    async def test_listar_base_sin_permiso_retorna_403(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_no_perms
    ):
        """GET /grilla-salarial/base sin permiso → 403."""
        resp = await client.get(
            "/api/v1/grilla-salarial/base",
            headers=auth_headers_no_perms,
        )
        assert resp.status_code == 403

    async def test_crear_base_con_permiso_retorna_201(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """POST /grilla-salarial/base con permiso → 201."""
        resp = await client.post(
            "/api/v1/grilla-salarial/base",
            json={"rol": "PROFESOR", "monto": "50000.00", "desde": "2026-01-01"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 201

    async def test_crear_base_sin_permiso_retorna_403(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_no_perms
    ):
        """POST /grilla-salarial/base sin permiso → 403."""
        resp = await client.post(
            "/api/v1/grilla-salarial/base",
            json={"rol": "PROFESOR", "monto": "50000.00", "desde": "2026-01-01"},
            headers=auth_headers_no_perms,
        )
        assert resp.status_code == 403

    async def test_editar_base_con_permiso_retorna_200(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """PUT /grilla-salarial/base/{id} con permiso → 200."""
        resp = await client.post(
            "/api/v1/grilla-salarial/base",
            json={"rol": "PROFESOR", "monto": "50000.00", "desde": "2026-01-01"},
            headers=auth_headers_finanzas,
        )
        base_id = resp.json()["id"]

        resp2 = await client.put(
            f"/api/v1/grilla-salarial/base/{base_id}",
            json={"monto": "60000.00"},
            headers=auth_headers_finanzas,
        )
        assert resp2.status_code == 200

    async def test_eliminar_base_con_permiso_retorna_204(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """DELETE /grilla-salarial/base/{id} con permiso → 204."""
        resp = await client.post(
            "/api/v1/grilla-salarial/base",
            json={"rol": "PROFESOR", "monto": "50000.00", "desde": "2026-01-01"},
            headers=auth_headers_finanzas,
        )
        base_id = resp.json()["id"]

        resp2 = await client.delete(
            f"/api/v1/grilla-salarial/base/{base_id}",
            headers=auth_headers_finanzas,
        )
        assert resp2.status_code == 204

    async def test_editar_base_sin_permiso_retorna_403(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_no_perms
    ):
        """PUT /grilla-salarial/base/{id} sin permiso → 403."""
        fake_id = uuid.uuid4()
        resp = await client.put(
            f"/api/v1/grilla-salarial/base/{fake_id}",
            json={"monto": "60000.00"},
            headers=auth_headers_no_perms,
        )
        assert resp.status_code == 403

    async def test_eliminar_base_sin_permiso_retorna_403(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_no_perms
    ):
        """DELETE /grilla-salarial/base/{id} sin permiso → 403."""
        fake_id = uuid.uuid4()
        resp = await client.delete(
            f"/api/v1/grilla-salarial/base/{fake_id}",
            headers=auth_headers_no_perms,
        )
        assert resp.status_code == 403


class TestGrillaPlusPermisos:
    """SalarioPlus permission tests."""

    async def test_crear_plus_con_permiso_retorna_201(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """POST /grilla-salarial/plus con permiso → 201."""
        resp = await client.post(
            "/api/v1/grilla-salarial/plus",
            json={"grupo": "PROG", "rol": "PROFESOR", "descripcion": "Test", "monto": "10000.00", "desde": "2026-01-01"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 201

    async def test_crear_plus_sin_permiso_retorna_403(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_no_perms
    ):
        """POST /grilla-salarial/plus sin permiso → 403."""
        resp = await client.post(
            "/api/v1/grilla-salarial/plus",
            json={"grupo": "PROG", "rol": "PROFESOR", "descripcion": "Test", "monto": "10000.00", "desde": "2026-01-01"},
            headers=auth_headers_no_perms,
        )
        assert resp.status_code == 403


# =============================================================================
# Liquidaciones permissions
# =============================================================================


class TestLiquidacionesPermisos:
    """liquidaciones:* permissions."""

    async def test_listar_liquidaciones_con_permiso_retorna_200(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """GET /liquidaciones/ con permiso → 200."""
        resp = await client.get(
            "/api/v1/liquidaciones/",
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 200

    async def test_listar_liquidaciones_sin_permiso_retorna_403(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_no_perms
    ):
        """GET /liquidaciones/ sin permiso → 403."""
        resp = await client.get(
            "/api/v1/liquidaciones/",
            headers=auth_headers_no_perms,
        )
        assert resp.status_code == 403

    async def test_calcular_con_permiso_validacion_previa(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """POST /liquidaciones/calcular con permiso → el endpoint se ejecuta."""
        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(uuid.uuid4()), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        # The endpoint responds (even if it fails on data validation, it passed permission check)
        assert resp.status_code != 403

    async def test_calcular_sin_permiso_retorna_403(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_no_perms
    ):
        """POST /liquidaciones/calcular sin permiso → 403."""
        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(uuid.uuid4()), "periodo": "2026-06"},
            headers=auth_headers_no_perms,
        )
        assert resp.status_code == 403

    async def test_obtener_liquidacion_con_permiso_retorna_404_o_200(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """GET /liquidaciones/{id} con permiso → pasa el check de permiso."""
        fake_id = uuid.uuid4()
        resp = await client.get(
            f"/api/v1/liquidaciones/{fake_id}",
            headers=auth_headers_finanzas,
        )
        # Returns 404 (not found), NOT 403 — permission check passed
        assert resp.status_code == 404


# =============================================================================
# Facturas permissions
# =============================================================================


class TestFacturasPermisos:
    """facturas:gestionar permissions."""

    async def test_listar_facturas_con_permiso_retorna_200(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """GET /facturas/ con permiso → 200."""
        resp = await client.get(
            "/api/v1/facturas/",
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 200

    async def test_listar_facturas_sin_permiso_retorna_403(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_no_perms
    ):
        """GET /facturas/ sin permiso → 403."""
        resp = await client.get(
            "/api/v1/facturas/",
            headers=auth_headers_no_perms,
        )
        assert resp.status_code == 403

    async def test_abonar_factura_con_permiso_se_ejecuta(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """POST /facturas/{id}/abonar con permiso → pasa el check."""
        fake_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/facturas/{fake_id}/abonar",
            headers=auth_headers_finanzas,
        )
        # 404 (not found), NOT 403 — permission check passed
        assert resp.status_code == 404
