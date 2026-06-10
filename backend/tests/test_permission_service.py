import uuid

import pytest
from sqlalchemy import select

from app.models import Permission, Role, RolePermission, Tenant, User, UserRole, UserTenant
from app.services.permission_service import PermissionService
from app.core.security import PasswordService

pytestmark = pytest.mark.asyncio


async def _create_tenant(db_session):
    tenant = Tenant(name="Test Tenant", code="RBAC-TST")
    db_session.add(tenant)
    await db_session.flush()
    return tenant


async def _create_permission(db_session, name: str, module: str, action: str):
    perm = Permission(name=name, module=module, action=action)
    db_session.add(perm)
    await db_session.flush()
    return perm


async def _create_role(db_session, name: str, tenant_id: uuid.UUID, is_system: bool = False):
    role = Role(name=name, tenant_id=tenant_id, is_system=is_system)
    db_session.add(role)
    await db_session.flush()
    return role


async def _assign_permission(db_session, role_id: uuid.UUID, permission_id: uuid.UUID,
                             tenant_id: uuid.UUID, scope: str = "global"):
    rp = RolePermission(role_id=role_id, permission_id=permission_id,
                        tenant_id=tenant_id, scope=scope)
    db_session.add(rp)
    await db_session.flush()
    return rp


async def _create_user_with_role(db_session, tenant_id: uuid.UUID, role_id: uuid.UUID):
    user = User(
        tenant_id=tenant_id,
        email=f"user-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Test", apellido="User",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()
    ut = UserTenant(user_id=user.id, tenant_id=tenant_id, is_active=True)
    db_session.add(ut)
    await db_session.flush()
    ur = UserRole(user_id=user.id, tenant_id=tenant_id, role_id=role_id)
    db_session.add(ur)
    await db_session.flush()
    return user


class TestGetEffectivePermissions:
    async def test_single_role_returns_its_permissions(self, db_session, test_engine):
        tenant = await _create_tenant(db_session)
        role = await _create_role(db_session, "TEST_ROLE", tenant.id)
        perm1 = await _create_permission(db_session, "modulo:accion1", "modulo", "accion1")
        perm2 = await _create_permission(db_session, "modulo:accion2", "modulo", "accion2")
        await _assign_permission(db_session, role.id, perm1.id, tenant.id)
        await _assign_permission(db_session, role.id, perm2.id, tenant.id)
        user = await _create_user_with_role(db_session, tenant.id, role.id)

        svc = PermissionService(db_session)
        result = await svc.get_effective_permissions(user.id)

        assert "modulo:accion1" in result
        assert "modulo:accion2" in result
        assert len(result) == 2

    async def test_union_of_roles_returns_combined_permissions(self, db_session, test_engine):
        tenant = await _create_tenant(db_session)
        role_a = await _create_role(db_session, "ROLE_A", tenant.id)
        role_b = await _create_role(db_session, "ROLE_B", tenant.id)
        perm_a = await _create_permission(db_session, "modulo:accion_a", "modulo", "accion_a")
        perm_b = await _create_permission(db_session, "modulo:accion_b", "modulo", "accion_b")
        await _assign_permission(db_session, role_a.id, perm_a.id, tenant.id)
        await _assign_permission(db_session, role_b.id, perm_b.id, tenant.id)
        user = await _create_user_with_role(db_session, tenant.id, role_a.id)
        ur2 = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role_b.id)
        db_session.add(ur2)
        await db_session.flush()

        svc = PermissionService(db_session)
        result = await svc.get_effective_permissions(user.id)

        assert "modulo:accion_a" in result
        assert "modulo:accion_b" in result
        assert len(result) == 2

    async def test_no_roles_returns_empty_set(self, db_session, test_engine):
        tenant = await _create_tenant(db_session)
        user = User(
            tenant_id=tenant.id,
            email="nobody@test.com", legajo="LEG-NO-ROLES",
            nombre="No", apellido="Roles",
            password_hash=PasswordService.hash("pass"),
        )
        db_session.add(user)
        await db_session.flush()
        ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
        db_session.add(ut)
        await db_session.flush()

        svc = PermissionService(db_session)
        result = await svc.get_effective_permissions(user.id)

        assert result == set()

    async def test_user_with_multiple_roles_gets_no_duplicates(self, db_session, test_engine):
        tenant = await _create_tenant(db_session)
        role_a = await _create_role(db_session, "ROLE_A2", tenant.id)
        role_b = await _create_role(db_session, "ROLE_B2", tenant.id)
        perm = await _create_permission(db_session, "modulo:compartido", "modulo", "compartido")
        await _assign_permission(db_session, role_a.id, perm.id, tenant.id)
        await _assign_permission(db_session, role_b.id, perm.id, tenant.id)
        user = await _create_user_with_role(db_session, tenant.id, role_a.id)
        ur2 = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role_b.id)
        db_session.add(ur2)
        await db_session.flush()

        svc = PermissionService(db_session)
        result = await svc.get_effective_permissions(user.id)

        assert "modulo:compartido" in result
        assert len(result) == 1


class TestGetEffectiveScope:
    async def test_returns_global_scope(self, db_session, test_engine):
        tenant = await _create_tenant(db_session)
        role = await _create_role(db_session, "SCOPE_ROLE", tenant.id)
        perm = await _create_permission(db_session, "test:global", "test", "global")
        await _assign_permission(db_session, role.id, perm.id, tenant.id, scope="global")
        user = await _create_user_with_role(db_session, tenant.id, role.id)

        svc = PermissionService(db_session)
        scope = await svc.get_effective_scope("test:global", user.id)

        assert scope == "global"

    async def test_returns_propio_scope(self, db_session, test_engine):
        tenant = await _create_tenant(db_session)
        role = await _create_role(db_session, "SCOPE_ROLE2", tenant.id)
        perm = await _create_permission(db_session, "test:propio", "test", "propio")
        await _assign_permission(db_session, role.id, perm.id, tenant.id, scope="propio")
        user = await _create_user_with_role(db_session, tenant.id, role.id)

        svc = PermissionService(db_session)
        scope = await svc.get_effective_scope("test:propio", user.id)

        assert scope == "propio"

    async def test_returns_none_for_unknown_permission(self, db_session, test_engine):
        tenant = await _create_tenant(db_session)
        role = await _create_role(db_session, "SCOPE_ROLE3", tenant.id)
        user = await _create_user_with_role(db_session, tenant.id, role.id)

        svc = PermissionService(db_session)
        scope = await svc.get_effective_scope("no:existe", user.id)

        assert scope is None
