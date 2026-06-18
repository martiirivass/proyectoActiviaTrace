import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect

from app.core.database import Base
from app.models import (
    Permission,
    RecoveryToken,
    RefreshToken,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
    UserTenant,
)
from app.models.mixins import SoftDeleteMixin


async def _ensure_table(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class TestUserModel:
    def test_inherits_soft_delete(self):
        assert issubclass(User, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = User.__table__.c["id"]
        assert col.primary_key

    def test_email_unique_and_indexed(self):
        col = User.__table__.c["email"]
        assert col.unique
        assert col.index

    def test_legajo_unique_and_indexed(self):
        col = User.__table__.c["legajo"]
        assert col.unique
        assert col.index

    def test_password_hash_not_nullable(self):
        col = User.__table__.c["password_hash"]
        assert not col.nullable

    def test_has_timestamps(self):
        assert "created_at" in User.__table__.c
        assert "updated_at" in User.__table__.c

    def test_has_relationships(self):
        mapper = inspect(User)
        rel_names = [r.key for r in mapper.relationships]
        assert "user_tenants" in rel_names
        assert "user_roles" in rel_names


class TestTenantModel:
    def test_inherits_soft_delete(self):
        assert issubclass(Tenant, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = Tenant.__table__.c["id"]
        assert col.primary_key

    def test_code_unique_and_indexed(self):
        col = Tenant.__table__.c["code"]
        assert col.unique
        assert col.index

    def test_is_active_column_not_nullable(self):
        col = Tenant.__table__.c["is_active"]
        assert not col.nullable

    def test_has_relationships(self):
        mapper = inspect(Tenant)
        rel_names = [r.key for r in mapper.relationships]
        assert "user_tenants" in rel_names
        assert "user_roles" in rel_names


class TestRoleModel:
    def test_inherits_soft_delete(self):
        assert issubclass(Role, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = Role.__table__.c["id"]
        assert col.primary_key

    def test_name_tenant_id_unique_constraint(self):
        constraints = [c for c in Role.__table__.constraints if "uq_role_name_per_tenant" in str(c.name or "")]
        assert len(constraints) == 1
        uq = constraints[0]
        cols = [c.name for c in uq.columns]
        assert "name" in cols
        assert "tenant_id" in cols

    def test_has_tenant_id_fk(self):
        col = Role.__table__.c["tenant_id"]
        assert len(col.foreign_keys) > 0

    def test_has_is_system_column(self):
        col = Role.__table__.c["is_system"]
        assert col is not None
        assert col.default is not None
        assert col.default.arg is False

    def test_has_description_column(self):
        col = Role.__table__.c["description"]
        assert col is not None
        assert col.nullable

    def test_has_relationships(self):
        mapper = inspect(Role)
        rel_names = [r.key for r in mapper.relationships]
        assert "user_roles" in rel_names
        assert "role_permissions" in rel_names


class TestPermissionModel:
    def test_inherits_soft_delete(self):
        assert issubclass(Permission, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = Permission.__table__.c["id"]
        assert col.primary_key

    def test_name_unique(self):
        col = Permission.__table__.c["name"]
        assert col.unique

    def test_name_comment(self):
        col = Permission.__table__.c["name"]
        assert col.comment is not None
        assert "modulo:accion" in col.comment

    def test_has_module_column(self):
        col = Permission.__table__.c["module"]
        assert col is not None
        assert not col.nullable

    def test_has_action_column(self):
        col = Permission.__table__.c["action"]
        assert col is not None
        assert not col.nullable

    def test_has_timestamps(self):
        assert "created_at" in Permission.__table__.c
        assert "updated_at" in Permission.__table__.c


class TestRolePermissionModel:
    def test_no_soft_delete(self):
        assert not issubclass(RolePermission, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = RolePermission.__table__.c["id"]
        assert col.primary_key

    def test_has_role_id_fk(self):
        col = RolePermission.__table__.c["role_id"]
        assert len(col.foreign_keys) > 0

    def test_has_permission_id_fk(self):
        col = RolePermission.__table__.c["permission_id"]
        assert len(col.foreign_keys) > 0

    def test_has_tenant_id_fk(self):
        col = RolePermission.__table__.c["tenant_id"]
        assert len(col.foreign_keys) > 0

    def test_has_scope_column(self):
        col = RolePermission.__table__.c["scope"]
        assert col is not None
        assert not col.nullable

    def test_unique_role_permission(self):
        constraints = [c for c in RolePermission.__table__.constraints if "uq_role_permission" in str(c.name or "")]
        assert len(constraints) == 1
        uq = constraints[0]
        cols = [c.name for c in uq.columns]
        assert "role_id" in cols
        assert "permission_id" in cols

    def test_has_relationships(self):
        mapper = inspect(RolePermission)
        rel_names = [r.key for r in mapper.relationships]
        assert "role" in rel_names
        assert "permission" in rel_names


class TestUserRoleModel:
    def test_no_soft_delete(self):
        assert not issubclass(UserRole, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = UserRole.__table__.c["id"]
        assert col.primary_key

    def test_has_user_id_fk(self):
        col = UserRole.__table__.c["user_id"]
        assert len(col.foreign_keys) > 0

    def test_has_tenant_id_fk(self):
        col = UserRole.__table__.c["tenant_id"]
        assert len(col.foreign_keys) > 0

    def test_has_role_id_fk(self):
        col = UserRole.__table__.c["role_id"]
        assert len(col.foreign_keys) > 0

    def test_unique_constraint(self):
        constraints = [c for c in UserRole.__table__.constraints if "uq_user_tenant_role" in str(c.name or "")]
        assert len(constraints) == 1
        uq = constraints[0]
        cols = [c.name for c in uq.columns]
        assert "user_id" in cols
        assert "tenant_id" in cols
        assert "role_id" in cols

    def test_has_relationships(self):
        mapper = inspect(UserRole)
        rel_names = [r.key for r in mapper.relationships]
        assert "user" in rel_names
        assert "tenant" in rel_names
        assert "role" in rel_names


class TestUserTenantModel:
    def test_no_soft_delete(self):
        assert not issubclass(UserTenant, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = UserTenant.__table__.c["id"]
        assert col.primary_key

    def test_has_user_id_fk(self):
        col = UserTenant.__table__.c["user_id"]
        assert len(col.foreign_keys) > 0

    def test_has_tenant_id_fk(self):
        col = UserTenant.__table__.c["tenant_id"]
        assert len(col.foreign_keys) > 0

    def test_is_active_default(self):
        col = UserTenant.__table__.c["is_active"]

    def test_unique_constraint(self):
        constraints = [c for c in UserTenant.__table__.constraints if "uq_user_tenant" in str(c.name or "")]
        assert len(constraints) == 1
        uq = constraints[0]
        cols = [c.name for c in uq.columns]
        assert "user_id" in cols
        assert "tenant_id" in cols

    def test_has_relationships(self):
        mapper = inspect(UserTenant)
        rel_names = [r.key for r in mapper.relationships]
        assert "user" in rel_names
        assert "tenant" in rel_names


@pytest.mark.asyncio
class TestUserModelDB:
    async def test_create_user(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user = User(
            email="test@example.com",
            legajo="LEG-001",
            nombre="Juan",
            apellido="Pérez",
            password_hash="argon2_hash_here",
        )
        db_session.add(user)
        await db_session.flush()

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == "test@example.com"
        assert user.legajo == "LEG-001"
        assert user.is_deleted is False
        assert user.deleted_at is None

    async def test_user_email_unique(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user1 = User(email="duplicate@test.com", legajo="LEG-002", nombre="A", apellido="B", password_hash="h1")
        db_session.add(user1)
        await db_session.flush()

        user2 = User(email="duplicate@test.com", legajo="LEG-003", nombre="C", apellido="D", password_hash="h2")
        db_session.add(user2)
        with pytest.raises(Exception):
            await db_session.flush()

    async def test_user_legajo_unique(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user1 = User(email="e1@test.com", legajo="LEG-UNIQUE", nombre="A", apellido="B", password_hash="h1")
        db_session.add(user1)
        await db_session.flush()

        user2 = User(email="e2@test.com", legajo="LEG-UNIQUE", nombre="C", apellido="D", password_hash="h2")
        db_session.add(user2)
        with pytest.raises(Exception):
            await db_session.flush()

    async def test_user_has_2fa_defaults(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user = User(email="2fa@test.com", legajo="LEG-2FA", nombre="A", apellido="B", password_hash="h")
        db_session.add(user)
        await db_session.flush()
        assert user.totp_secret is None
        assert user.is_2fa_enabled is False

    async def test_user_can_set_2fa_fields(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user = User(
            email="2fa-on@test.com", legajo="LEG-2FA2", nombre="A", apellido="B",
            password_hash="h", totp_secret="encrypted_secret", is_2fa_enabled=True,
        )
        db_session.add(user)
        await db_session.flush()
        assert user.totp_secret == "encrypted_secret"
        assert user.is_2fa_enabled is True


class TestRefreshTokenModelDB:
    async def test_create_refresh_token(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user = User(email="rt@test.com", legajo="LEG-RT", nombre="A", apellido="B", password_hash="h")
        db_session.add(user)
        await db_session.flush()

        token = RefreshToken(user_id=user.id, token_hash="abc123", expires_at=datetime.now(timezone.utc))
        db_session.add(token)
        await db_session.flush()

        assert token.id is not None
        assert isinstance(token.id, uuid.UUID)
        assert token.user_id == user.id
        assert token.token_hash == "abc123"
        assert token.revoked_at is None

    async def test_refresh_token_unique_hash(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user = User(email="rt2@test.com", legajo="LEG-RT2", nombre="A", apellido="B", password_hash="h")
        db_session.add(user)
        await db_session.flush()

        t1 = RefreshToken(user_id=user.id, token_hash="same-hash", expires_at=datetime.now(timezone.utc))
        db_session.add(t1)
        await db_session.flush()

        t2 = RefreshToken(user_id=user.id, token_hash="same-hash", expires_at=datetime.now(timezone.utc))
        db_session.add(t2)
        with pytest.raises(Exception):
            await db_session.flush()

    async def test_refresh_token_hash_indexed(self, test_engine):
        col = RefreshToken.__table__.c["token_hash"]
        assert col.unique
        assert col.index


class TestRecoveryTokenModelDB:
    async def test_create_recovery_token(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user = User(email="rec@test.com", legajo="LEG-REC", nombre="A", apellido="B", password_hash="h")
        db_session.add(user)
        await db_session.flush()

        token = RecoveryToken(user_id=user.id, token_hash="def456", expires_at=datetime.now(timezone.utc))
        db_session.add(token)
        await db_session.flush()

        assert token.id is not None
        assert isinstance(token.id, uuid.UUID)
        assert token.user_id == user.id
        assert token.used_at is None

    async def test_recovery_token_unique_hash(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user = User(email="rec2@test.com", legajo="LEG-REC2", nombre="A", apellido="B", password_hash="h")
        db_session.add(user)
        await db_session.flush()

        t1 = RecoveryToken(user_id=user.id, token_hash="same", expires_at=datetime.now(timezone.utc))
        db_session.add(t1)
        await db_session.flush()

        t2 = RecoveryToken(user_id=user.id, token_hash="same", expires_at=datetime.now(timezone.utc))
        db_session.add(t2)
        with pytest.raises(Exception):
            await db_session.flush()
