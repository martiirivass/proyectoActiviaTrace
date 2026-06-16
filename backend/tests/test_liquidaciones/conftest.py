"""Shared fixtures and helpers for liquidaciones tests.

All tests use Strict TDD: RED → GREEN → REFACTOR.
Fixtures follow the same patterns as test_avisos.py:
- ``client`` comes from parent conftest (get_db overridden)
- ``db_session`` comes from parent conftest (shared with client)
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import PasswordService, create_access_token
from app.models import (
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
    UserTenant,
)

pytestmark = pytest.mark.asyncio


# =============================================================================
# Helper: tenant + user + permissions
# =============================================================================


async def _create_tenant_with_user(
    db_session,
    role_name: str = "FINANZAS",
    permissions: list[str] | None = None,
    facturador: bool = False,
    email_suffix: str = "liq",
):
    """Create a fresh tenant + user with the given role and permissions.

    Returns (user, tenant, token, role).
    Each call creates isolated data so tests never collide.
    """
    code = f"LQ{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Liquidacion Test {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"{email_suffix}-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Liquidacion",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
        facturador=facturador,
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

    # Assign permissions
    if permissions:
        for perm_name in permissions:
            stmt = select(Permission).where(Permission.name == perm_name)
            result = await db_session.execute(stmt)
            perm = result.scalar_one_or_none()
            if perm is None:
                module, action = perm_name.split(":", 1)
                perm = Permission(name=perm_name, module=module, action=action)
                db_session.add(perm)
                await db_session.flush()

            rp = RolePermission(
                role_id=role.id,
                permission_id=perm.id,
                tenant_id=tenant.id,
                scope="global",
            )
            db_session.add(rp)
            await db_session.flush()

    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant.id,
        roles=[role_name],
    )
    return user, tenant, token, role


# =============================================================================
# Fixtures: authenticated users
# =============================================================================

ALL_LIQUIDACIONES_PERMS = [
    "grilla-salarial:ver",
    "grilla-salarial:crear",
    "grilla-salarial:editar",
    "grilla-salarial:eliminar",
    "liquidaciones:ver",
    "liquidaciones:calcular",
    "liquidaciones:cerrar",
    "liquidaciones:exportar",
    "liquidaciones:historial",
    "facturas:gestionar",
]


@pytest_asyncio.fixture
async def user_finanzas(db_session):
    """Create tenant + FINANZAS user with all liquidaciones permissions.

    Returns (user, tenant, token).
    """
    _user, _tenant, token, _ = await _create_tenant_with_user(
        db_session,
        role_name="FINANZAS",
        permissions=ALL_LIQUIDACIONES_PERMS,
    )
    return _user, _tenant, token


@pytest_asyncio.fixture
async def auth_headers_finanzas(user_finanzas):
    """Auth headers for a FINANZAS user with all permissions."""
    _, _, token = user_finanzas
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def user_no_perms(db_session):
    """Create a user with NO liquidaciones permissions at all.

    Returns (user, tenant, token).
    """
    _user, _tenant, token, _ = await _create_tenant_with_user(
        db_session,
        role_name="TUTOR",
        permissions=["estado:ver"],
        email_suffix="noperm",
    )
    return _user, _tenant, token


@pytest_asyncio.fixture
async def auth_headers_no_perms(user_no_perms):
    """Auth headers for a user WITHOUT liquidaciones permissions."""
    _, _, token = user_no_perms
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Fixtures: second tenant for isolation tests
# =============================================================================


@pytest_asyncio.fixture
async def tenant_b(db_session):
    """Create a second, independent tenant with a user.

    Returns (user, tenant, token).
    """
    _user, _tenant, token, _ = await _create_tenant_with_user(
        db_session,
        role_name="FINANZAS",
        permissions=ALL_LIQUIDACIONES_PERMS,
        email_suffix="tenb",
    )
    return _user, _tenant, token


@pytest_asyncio.fixture
async def auth_headers_tenant_b(tenant_b):
    """Auth headers for tenant B's user."""
    _, _, token = tenant_b
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Fixtures: data dicts for convenience
# =============================================================================


@pytest.fixture
def salario_base_data():
    """Sample data for creating a SalarioBase."""
    return {
        "rol": "PROFESOR",
        "monto": "150000.00",
        "desde": "2026-01-01",
        "hasta": None,
    }


@pytest.fixture
def salario_plus_data():
    """Sample data for creating a SalarioPlus."""
    return {
        "grupo": "PROG",
        "rol": "PROFESOR",
        "descripcion": "Plus programación",
        "monto": "25000.00",
        "desde": "2026-01-01",
        "hasta": None,
    }


@pytest.fixture
def factura_data():
    """Sample data for creating a Factura."""
    return {
        "periodo": "2026-06",
        "detalle": "Honorarios junio 2026",
        "referencia_archivo": "factura_001.pdf",
        "tamano_kb": "1024.50",
    }
