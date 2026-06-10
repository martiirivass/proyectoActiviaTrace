import uuid

import pytest
from sqlalchemy import select

from app.core.dependencies import get_db
from app.core.security import PasswordService, create_access_token
from app.models import Permission, Role, RolePermission, Tenant, User, UserRole, UserTenant
from app.services.permission_service import PermissionService

pytestmark = pytest.mark.asyncio


async def _seed_full_environment(db_session):
    """Create tenant and seed all 7 roles with their permissions."""
    tenant = Tenant(name="Full Test", code="FULL")
    db_session.add(tenant)
    await db_session.flush()

    roles_data = {
        "ALUMNO": {"is_system": False},
        "TUTOR": {"is_system": False},
        "PROFESOR": {"is_system": False},
        "COORDINADOR": {"is_system": False},
        "NEXO": {"is_system": False},
        "ADMIN": {"is_system": True},
        "FINANZAS": {"is_system": True},
    }

    roles = {}
    for name, attrs in roles_data.items():
        role = Role(name=name, tenant_id=tenant.id, is_system=attrs["is_system"])
        db_session.add(role)
        roles[name] = role
    await db_session.flush()

    perm_defs = [
        ("estado:ver", "estado", "ver"),
        ("evaluacion:reservar", "evaluacion", "reservar"),
        ("avisos:confirmar", "avisos", "confirmar"),
        ("calificaciones:importar", "calificaciones", "importar"),
        ("atrasados:ver", "atrasados", "ver"),
        ("entregas:detectar", "entregas", "detectar"),
        ("comunicacion:enviar", "comunicacion", "enviar"),
        ("comunicacion:aprobar", "comunicacion", "aprobar"),
        ("encuentros:gestionar", "encuentros", "gestionar"),
        ("guardias:registrar", "guardias", "registrar"),
        ("tareas:gestionar", "tareas", "gestionar"),
        ("avisos:publicar", "avisos", "publicar"),
        ("equipos:asignar", "equipos", "asignar"),
        ("estructura:gestionar", "estructura", "gestionar"),
        ("usuarios:gestionar", "usuarios", "gestionar"),
        ("auditoria:ver", "auditoria", "ver"),
        ("liquidaciones:gestionar", "liquidaciones", "gestionar"),
        ("liquidaciones:calcular", "liquidaciones", "calcular"),
        ("facturas:gestionar", "facturas", "gestionar"),
        ("tenant:configurar", "tenant", "configurar"),
        ("impersonacion:usar", "impersonacion", "usar"),
    ]

    perms = {}
    for name, mod, act in perm_defs:
        perm = Permission(name=name, module=mod, action=act)
        db_session.add(perm)
        perms[name] = perm
    await db_session.flush()

    matrix = {
        "ALUMNO": [("estado:ver", "global"), ("evaluacion:reservar", "global"), ("avisos:confirmar", "global")],
        "TUTOR": [("estado:ver", "propio"), ("avisos:confirmar", "global"), ("comunicacion:enviar", "global")],
        "PROFESOR": [
            ("estado:ver", "global"), ("calificaciones:importar", "global"),
            ("atrasados:ver", "propio"), ("entregas:detectar", "global"),
            ("comunicacion:enviar", "global"), ("encuentros:gestionar", "global"),
            ("guardias:registrar", "global"), ("tareas:gestionar", "global"),
            ("avisos:publicar", "global"),
        ],
        "COORDINADOR": [
            ("estado:ver", "global"), ("calificaciones:importar", "global"),
            ("atrasados:ver", "global"), ("entregas:detectar", "global"),
            ("comunicacion:enviar", "global"), ("comunicacion:aprobar", "global"),
            ("encuentros:gestionar", "global"), ("guardias:registrar", "global"),
            ("tareas:gestionar", "global"), ("avisos:publicar", "global"),
            ("equipos:asignar", "global"), ("estructura:gestionar", "global"),
        ],
        "NEXO": [
            ("estado:ver", "global"), ("comunicacion:enviar", "global"),
            ("encuentros:gestionar", "global"),
        ],
        "ADMIN": [
            ("estado:ver", "global"), ("calificaciones:importar", "global"),
            ("atrasados:ver", "global"), ("entregas:detectar", "global"),
            ("comunicacion:enviar", "global"), ("comunicacion:aprobar", "global"),
            ("encuentros:gestionar", "global"), ("guardias:registrar", "global"),
            ("tareas:gestionar", "global"), ("avisos:publicar", "global"),
            ("equipos:asignar", "global"), ("estructura:gestionar", "global"),
            ("usuarios:gestionar", "global"), ("auditoria:ver", "global"),
            ("tenant:configurar", "global"), ("impersonacion:usar", "global"),
        ],
        "FINANZAS": [
            ("liquidaciones:gestionar", "global"), ("liquidaciones:calcular", "global"),
            ("facturas:gestionar", "global"), ("auditoria:ver", "global"),
        ],
    }

    for role_name, perm_list in matrix.items():
        for perm_name, scope in perm_list:
            rp = RolePermission(
                role_id=roles[role_name].id,
                permission_id=perms[perm_name].id,
                scope=scope,
                tenant_id=tenant.id,
            )
            db_session.add(rp)
    await db_session.flush()

    return tenant, roles, perms


class TestSeedDataPermissions:
    async def test_alumno_has_limited_permissions(self, db_session, test_engine):
        tenant, roles, perms = await _seed_full_environment(db_session)
        user = User(email="alumno@test.com", legajo="LEG-ALUMNO",
                     nombre="Alumno", apellido="Test",
                     password_hash=PasswordService.hash("pass"))
        db_session.add(user)
        await db_session.flush()
        ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
        db_session.add(ut)
        ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=roles["ALUMNO"].id)
        db_session.add(ur)
        await db_session.flush()

        svc = PermissionService(db_session)
        perms_set = await svc.get_effective_permissions(user.id)

        assert "estado:ver" in perms_set
        assert "evaluacion:reservar" in perms_set
        assert "avisos:confirmar" in perms_set
        assert "calificaciones:importar" not in perms_set
        assert "usuarios:gestionar" not in perms_set
        assert "auditoria:ver" not in perms_set
        assert "liquidaciones:gestionar" not in perms_set

    async def test_admin_has_all_management_permissions(self, db_session, test_engine):
        tenant, roles, perms = await _seed_full_environment(db_session)
        user = User(email="admin@test.com", legajo="LEG-ADMIN",
                     nombre="Admin", apellido="Test",
                     password_hash=PasswordService.hash("pass"))
        db_session.add(user)
        await db_session.flush()
        ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
        db_session.add(ut)
        ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=roles["ADMIN"].id)
        db_session.add(ur)
        await db_session.flush()

        svc = PermissionService(db_session)
        perms_set = await svc.get_effective_permissions(user.id)

        management_perms = [
            "estado:ver", "calificaciones:importar", "comunicacion:enviar",
            "comunicacion:aprobar", "usuarios:gestionar", "auditoria:ver",
            "tenant:configurar", "impersonacion:usar",
        ]
        for p in management_perms:
            assert p in perms_set, f"{p} should be in ADMIN permissions"

    async def test_finanzas_has_only_financial_permissions(self, db_session, test_engine):
        tenant, roles, perms = await _seed_full_environment(db_session)
        user = User(email="finanzas@test.com", legajo="LEG-FINANZAS",
                     nombre="Finanzas", apellido="Test",
                     password_hash=PasswordService.hash("pass"))
        db_session.add(user)
        await db_session.flush()
        ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
        db_session.add(ut)
        ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=roles["FINANZAS"].id)
        db_session.add(ur)
        await db_session.flush()

        svc = PermissionService(db_session)
        perms_set = await svc.get_effective_permissions(user.id)

        assert "liquidaciones:gestionar" in perms_set
        assert "liquidaciones:calcular" in perms_set
        assert "facturas:gestionar" in perms_set
        assert "auditoria:ver" in perms_set
        assert "estado:ver" not in perms_set
        assert "calificaciones:importar" not in perms_set
        assert "usuarios:gestionar" not in perms_set


class TestSystemRoleProtection:
    async def test_system_role_cannot_be_deleted(self, db_session, test_engine):
        tenant, roles, perms = await _seed_full_environment(db_session)
        admin_role = roles["ADMIN"]
        assert admin_role.is_system is True

        from app.repositories.base import BaseRepository
        repo = BaseRepository(Role, db_session)
        with pytest.raises(ValueError, match="Cannot delete system role"):
            await repo.soft_delete(admin_role.id)

    async def test_non_system_role_can_be_deleted(self, db_session, test_engine):
        tenant, roles, perms = await _seed_full_environment(db_session)
        alumno_role = roles["ALUMNO"]
        assert alumno_role.is_system is False

        from app.repositories.base import BaseRepository
        repo = BaseRepository(Role, db_session)
        await repo.soft_delete(alumno_role.id)

        stmt = select(Role).where(Role.id == alumno_role.id)
        rows = await db_session.execute(stmt)
        deleted = rows.scalar_one_or_none()
        assert deleted is not None
        assert deleted.is_deleted is True
