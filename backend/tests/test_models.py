import uuid

import pytest
from sqlalchemy import inspect

from app.core.database import Base
from app.models import Permission, Role, Tenant, User, UserRole, UserTenant
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

    def test_has_relationships(self):
        mapper = inspect(Role)
        rel_names = [r.key for r in mapper.relationships]
        assert "user_roles" in rel_names


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
