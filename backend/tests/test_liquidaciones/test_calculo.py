"""Tests for Liquidacion calculation logic.

Covers all scenarios from *liquidaciones-spec.md*.
Strict TDD: RED → GREEN → REFACTOR.

Requires seeded data: Cohorte, Materia (with grupo_plus),
Asignacion (linking user → materia → cohorte), SalarioBase, SalarioPlus.
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


async def _seed_calculo_base(
    db_session,
    tenant_id,
    usuario_id,
    rol="PROFESOR",
    grupo_plus="PROG",
    num_comisiones=1,
    facturador=False,
):
    """Seed the minimum data needed for a calculation.

    Creates: Cohorte, Materia(grupo_plus), Asignacion(s).
    Returns (cohorte, materia).
    """
    carrera = Carrera(
        tenant_id=tenant_id,
        codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
        nombre="Carrera Test",
    )
    db_session.add(carrera)
    await db_session.flush()

    cohorte = Cohorte(
        tenant_id=tenant_id,
        carrera_id=carrera.id,
        nombre=f"COH-{uuid.uuid4().hex[:6].upper()}",
        anio=2026,
    )
    db_session.add(cohorte)
    await db_session.flush()

    materias = []
    for i in range(num_comisiones):
        materia = Materia(
            tenant_id=tenant_id,
            codigo=f"MAT-{uuid.uuid4().hex[:6].upper()}-{i}",
            nombre=f"Materia {i} {grupo_plus}",
            grupo_plus=grupo_plus,
        )
        db_session.add(materia)
        await db_session.flush()
        materias.append(materia)

        asignacion = Asignacion(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            rol=rol,
            desde=datetime.now(timezone.utc).date() - timedelta(days=30),
            hasta=datetime.now(timezone.utc).date() + timedelta(days=365),
        )
        db_session.add(asignacion)
        await db_session.flush()

    return cohorte, materias[0] if materias else None


async def _seed_salario_base(
    db_session, tenant_id, rol="PROFESOR", monto="150000.00", desde="2026-01-01",
):
    """Create a SalarioBase via the API or direct DB."""
    from app.models.salario_base import SalarioBase
    from datetime import date
    sb = SalarioBase(
        tenant_id=tenant_id,
        rol=rol,
        monto=monto,
        desde=date.fromisoformat(desde),
    )
    db_session.add(sb)
    await db_session.flush()
    await db_session.refresh(sb)
    return sb


async def _seed_salario_plus(
    db_session, tenant_id, grupo="PROG", rol="PROFESOR",
    monto="25000.00", desde="2026-01-01", descripcion="Plus test",
):
    """Create a SalarioPlus directly in DB."""
    from app.models.salario_plus import SalarioPlus
    from datetime import date
    sp = SalarioPlus(
        tenant_id=tenant_id,
        grupo=grupo,
        rol=rol,
        descripcion=descripcion,
        monto=monto,
        desde=date.fromisoformat(desde),
    )
    db_session.add(sp)
    await db_session.flush()
    await db_session.refresh(sp)
    return sp


# =============================================================================
# Tests
# =============================================================================


class TestCalculoSimple:
    """Basic calculation: 1 materia, 1 grupo, 1 comisión."""

    async def test_calculo_1_materia_1_comision(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """1 materia PROG, 1 comisión → total = base + 1×plus."""
        user, tenant, _ = user_finanzas

        # Seed: docente (the user themselves with facturador=False by default)
        cohorte, materia = await _seed_calculo_base(
            db_session, tenant.id, user.id,
            rol="PROFESOR", grupo_plus="PROG",
        )
        await _seed_salario_base(db_session, tenant.id, rol="PROFESOR", monto="150000.00")
        await _seed_salario_plus(db_session, tenant.id, grupo="PROG", rol="PROFESOR", monto="25000.00")

        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["creadas"] == 1
        item = data["items"][0]
        assert item["monto_base"] == "150000.00"
        assert item["monto_plus"] == "25000.00"
        assert item["total"] == "175000.00"
        assert item["rol"] == "PROFESOR"
        assert item["estado"] == "Abierta"
        assert item["excluido_por_factura"] is False
        assert item["es_nexo"] is False
        # Verify comisiones JSONB
        assert item["comisiones"] is not None
        assert "items" in item["comisiones"]
        assert len(item["comisiones"]["items"]) == 1
        assert item["comisiones"]["items"][0]["grupo_plus"] == "PROG"

    async def test_calculo_respuesta_contiene_ids_correctos(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """La respuesta incluye cohorte_id, usuario_id, periodo correctos."""
        user, tenant, _ = user_finanzas
        cohorte, _ = await _seed_calculo_base(db_session, tenant.id, user.id)
        await _seed_salario_base(db_session, tenant.id)
        await _seed_salario_plus(db_session, tenant.id)

        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 201
        item = resp.json()["items"][0]
        assert item["cohorte_id"] == str(cohorte.id)
        assert item["usuario_id"] == str(user.id)
        assert item["periodo"] == "2026-06"


class TestCalculoMultiplesComisiones:
    """N comisiones del mismo grupo → N × Plus."""

    async def test_3_comisiones_mismo_grupo(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """3 comisiones PROG → monto_plus = 3 × 25000 = 75000."""
        user, tenant, _ = user_finanzas
        cohorte, _ = await _seed_calculo_base(
            db_session, tenant.id, user.id,
            grupo_plus="PROG", num_comisiones=3,
        )
        await _seed_salario_base(db_session, tenant.id, monto="150000.00")
        await _seed_salario_plus(db_session, tenant.id, grupo="PROG", monto="25000.00")

        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 201
        item = resp.json()["items"][0]
        assert item["monto_plus"] == "75000.00"  # 3 × 25000
        assert item["total"] == "225000.00"  # 150000 + 75000

    async def test_grupos_distintos(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """2 PROG + 1 MAT → monto_plus = 2×25000 + 1×30000 = 80000."""
        user, tenant, _ = user_finanzas

        # Create cohorte + carrera
        carrera = Carrera(
            tenant_id=tenant.id,
            codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
            nombre="Carrera Test",
        )
        db_session.add(carrera)
        await db_session.flush()

        cohorte = Cohorte(
            tenant_id=tenant.id, carrera_id=carrera.id,
            nombre=f"COH-{uuid.uuid4().hex[:6].upper()}", anio=2026,
        )
        db_session.add(cohorte)
        await db_session.flush()

        # 2 PROG materias
        for _ in range(2):
            m = Materia(tenant_id=tenant.id, codigo=f"MAT-PROG-{uuid.uuid4().hex[:4]}", nombre="PROG", grupo_plus="PROG")
            db_session.add(m)
            await db_session.flush()
            a = Asignacion(tenant_id=tenant.id, usuario_id=user.id, materia_id=m.id, cohorte_id=cohorte.id, rol="PROFESOR",
                           desde=datetime.now(timezone.utc).date() - timedelta(days=30),
                           hasta=datetime.now(timezone.utc).date() + timedelta(days=365))
            db_session.add(a)
            await db_session.flush()

        # 1 MAT materia
        m_mat = Materia(tenant_id=tenant.id, codigo=f"MAT-MAT-{uuid.uuid4().hex[:4]}", nombre="MAT", grupo_plus="MAT")
        db_session.add(m_mat)
        await db_session.flush()
        a_mat = Asignacion(tenant_id=tenant.id, usuario_id=user.id, materia_id=m_mat.id, cohorte_id=cohorte.id, rol="PROFESOR",
                           desde=datetime.now(timezone.utc).date() - timedelta(days=30),
                           hasta=datetime.now(timezone.utc).date() + timedelta(days=365))
        db_session.add(a_mat)
        await db_session.flush()

        await _seed_salario_base(db_session, tenant.id, monto="150000.00")
        await _seed_salario_plus(db_session, tenant.id, grupo="PROG", monto="25000.00")
        await _seed_salario_plus(db_session, tenant.id, grupo="MAT", monto="30000.00")

        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 201
        item = resp.json()["items"][0]
        assert item["monto_plus"] == "80000.00"  # 2×25000 + 1×30000
        assert item["total"] == "230000.00"  # 150000 + 80000


class TestCalculoCasosBorde:
    """Edge cases: missing data, special roles, etc."""

    async def test_sin_salario_base_retorna_422(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Docente sin SalarioBase vigente → 422."""
        user, tenant, _ = user_finanzas
        cohorte, _ = await _seed_calculo_base(db_session, tenant.id, user.id)
        # Do NOT create SalarioBase

        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 422

    async def test_sin_salario_plus_no_bloquea(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Sin SalarioPlus para (grupo, rol) → monto_plus = 0, no error."""
        user, tenant, _ = user_finanzas
        cohorte, _ = await _seed_calculo_base(db_session, tenant.id, user.id, grupo_plus="PROG")
        await _seed_salario_base(db_session, tenant.id, monto="150000.00")
        # Do NOT create SalarioPlus

        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 201
        item = resp.json()["items"][0]
        assert item["monto_plus"] == "0.00"
        assert item["total"] == "150000.00"

    async def test_cohorte_sin_asignaciones_retorna_lista_vacia(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Cohorte sin docentes asignados → 200 con lista vacía."""
        _, tenant, _ = user_finanzas

        # Create a cohorte with no asignaciones
        carrera = Carrera(
            tenant_id=tenant.id,
            codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
            nombre="Carrera Empty",
        )
        db_session.add(carrera)
        await db_session.flush()
        cohorte = Cohorte(tenant_id=tenant.id, carrera_id=carrera.id,
                          nombre=f"COH-{uuid.uuid4().hex[:6].upper()}", anio=2026)
        db_session.add(cohorte)
        await db_session.flush()

        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["creadas"] == 0
        assert data["items"] == []

    async def test_docente_facturante_excluido(
        self, client: AsyncClient, db_session, auth_headers_finanzas
    ):
        """Docente facturante → excluido_por_factura = true."""
        # Create a facturador user
        from app.models import Tenant, User, UserTenant, Role, UserRole, Permission, RolePermission
        from app.core.security import PasswordService, create_access_token
        from sqlalchemy import select
        import uuid

        code = f"FACT{uuid.uuid4().hex[:6].upper()}"
        tenant = Tenant(name="Fact Test", code=code)
        db_session.add(tenant)
        await db_session.flush()

        facturador_user = User(
            tenant_id=tenant.id,
            email=f"fact-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Facturador",
            apellido="Test",
            password_hash=PasswordService.hash("pass"),
            facturador=True,
        )
        db_session.add(facturador_user)
        await db_session.flush()

        ut = UserTenant(user_id=facturador_user.id, tenant_id=tenant.id, is_active=True)
        db_session.add(ut)
        await db_session.flush()

        role = Role(name="FINANZAS", tenant_id=tenant.id)
        db_session.add(role)
        await db_session.flush()
        ur = UserRole(user_id=facturador_user.id, tenant_id=tenant.id, role_id=role.id)
        db_session.add(ur)
        await db_session.flush()

        # Assign permissions
        for perm_name in ["liquidaciones:calcular", "liquidaciones:ver"]:
            stmt = select(Permission).where(Permission.name == perm_name)
            perm = (await db_session.execute(stmt)).scalar_one_or_none()
            if perm is None:
                module, action = perm_name.split(":", 1)
                perm = Permission(name=perm_name, module=module, action=action)
                db_session.add(perm)
                await db_session.flush()
            rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
            db_session.add(rp)
            await db_session.flush()

        token = create_access_token(facturador_user.id, tenant.id, ["FINANZAS"])
        headers = {"Authorization": f"Bearer {token}"}

        cohorte, _ = await _seed_calculo_base(db_session, tenant.id, facturador_user.id)
        await _seed_salario_base(db_session, tenant.id, monto="150000.00")
        await _seed_salario_plus(db_session, tenant.id, monto="25000.00")

        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=headers,
        )
        assert resp.status_code == 201
        item = resp.json()["items"][0]
        assert item["excluido_por_factura"] is True
        # The total is still calculated
        assert item["total"] == "175000.00"

    async def test_docente_rol_nexo(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """Docente con rol NEXO → es_nexo = true."""
        user, tenant, _ = user_finanzas
        # Create asignacion with rol=NEXO instead of PROFESOR
        cohorte, _ = await _seed_calculo_base(db_session, tenant.id, user.id, rol="NEXO")
        await _seed_salario_base(db_session, tenant.id, rol="NEXO", monto="120000.00")
        await _seed_salario_plus(db_session, tenant.id, grupo="PROG", rol="NEXO", monto="15000.00")

        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 201
        item = resp.json()["items"][0]
        assert item["es_nexo"] is True
        assert item["rol"] == "NEXO"

    async def test_calculo_multi_tenant_aislamiento(
        self, client: AsyncClient, db_session, user_finanzas, tenant_b
    ):
        """Tenant B no puede calcular sobre cohorte de Tenant A."""
        user_a, tenant_a, token_a = user_finanzas
        user_b, tenant_b_data, token_b = tenant_b

        # Create cohorte in tenant A
        cohorte, _ = await _seed_calculo_base(db_session, tenant_a.id, user_a.id)
        await _seed_salario_base(db_session, tenant_a.id)
        await _seed_salario_plus(db_session, tenant_a.id)

        headers_b = {"Authorization": f"Bearer {token_b}"}
        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=headers_b,
        )
        # Tenant B has no access to Tenant A's cohorte → 404 or empty
        # (the cohorte will not be found since the service scopes by tenant)
        assert resp.status_code in (404, 422, 201)
        # If it returns 201, items should be 0
        if resp.status_code == 201:
            assert resp.json()["creadas"] == 0


class TestCalculoMultiplesUsuarios:
    """Multiple users in same cohorte."""

    async def test_dos_usuarios_en_cohorte_genera_dos_liquidaciones(
        self, client: AsyncClient, db_session, user_finanzas, auth_headers_finanzas
    ):
        """2 usuarios con asignaciones en la cohorte generan 2 liquidaciones."""
        user_a, tenant, _ = user_finanzas

        # Create a second user in the same tenant
        from app.models import Tenant, User, UserTenant, Role, UserRole, Permission, RolePermission
        from app.core.security import PasswordService
        from sqlalchemy import select

        user_b = User(tenant_id=tenant.id, email=f"multi-{uuid.uuid4().hex[:8]}@test.com",
                       legajo=f"LEG-{uuid.uuid4().hex[:8]}", nombre="Multi", apellido="User",
                       password_hash=PasswordService.hash("pass"))
        db_session.add(user_b)
        await db_session.flush()
        ut_b = UserTenant(user_id=user_b.id, tenant_id=tenant.id, is_active=True)
        db_session.add(ut_b)
        await db_session.flush()

        carrera = Carrera(tenant_id=tenant.id, codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}", nombre="Carrera Multi")
        db_session.add(carrera)
        await db_session.flush()

        cohorte = Cohorte(tenant_id=tenant.id, carrera_id=carrera.id,
                          nombre=f"COH-{uuid.uuid4().hex[:6].upper()}", anio=2026)
        db_session.add(cohorte)
        await db_session.flush()

        # Asignacion for user_a
        m1 = Materia(tenant_id=tenant.id, codigo=f"M1-{uuid.uuid4().hex[:4]}", nombre="M1", grupo_plus="PROG")
        db_session.add(m1)
        await db_session.flush()
        a1 = Asignacion(tenant_id=tenant.id, usuario_id=user_a.id, materia_id=m1.id, cohorte_id=cohorte.id, rol="PROFESOR",
                        desde=datetime.now(timezone.utc).date() - timedelta(days=30),
                        hasta=datetime.now(timezone.utc).date() + timedelta(days=365))
        db_session.add(a1)
        await db_session.flush()

        # Asignacion for user_b
        m2 = Materia(tenant_id=tenant.id, codigo=f"M2-{uuid.uuid4().hex[:4]}", nombre="M2", grupo_plus="PROG")
        db_session.add(m2)
        await db_session.flush()
        a2 = Asignacion(tenant_id=tenant.id, usuario_id=user_b.id, materia_id=m2.id, cohorte_id=cohorte.id, rol="PROFESOR",
                        desde=datetime.now(timezone.utc).date() - timedelta(days=30),
                        hasta=datetime.now(timezone.utc).date() + timedelta(days=365))
        db_session.add(a2)
        await db_session.flush()

        await _seed_salario_base(db_session, tenant.id, rol="PROFESOR", monto="150000.00")
        await _seed_salario_plus(db_session, tenant.id, grupo="PROG", rol="PROFESOR", monto="25000.00")

        resp = await client.post(
            "/api/v1/liquidaciones/calcular",
            json={"cohorte_id": str(cohorte.id), "periodo": "2026-06"},
            headers=auth_headers_finanzas,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["creadas"] == 2
        assert len(data["items"]) == 2
