import uuid

import pytest
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class RepoItem(SoftDeleteMixin, Base):
    __tablename__ = "repo_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class TenantRepoItem(SoftDeleteMixin, Base):
    __tablename__ = "tenant_repo_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)


async def _ensure_table(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class TestBaseRepository:
    async def test_create_and_get(self, db_session, test_engine):
        await _ensure_table(test_engine)
        from app.repositories.base import BaseRepository

        repo = BaseRepository(RepoItem, db_session)

        item = await repo.create(name="test-item")
        assert item.id is not None
        assert item.name == "test-item"
        assert item.is_deleted is False

        fetched = await repo.get(item.id)
        assert fetched is not None
        assert fetched.id == item.id
        assert fetched.name == "test-item"

    async def test_get_not_found(self, db_session, test_engine):
        await _ensure_table(test_engine)
        from app.repositories.base import BaseRepository

        repo = BaseRepository(RepoItem, db_session)
        result = await repo.get(9999)
        assert result is None

    async def test_list(self, db_session, test_engine):
        await _ensure_table(test_engine)
        from app.repositories.base import BaseRepository

        repo = BaseRepository(RepoItem, db_session)
        item1 = await repo.create(name="list-a")
        item2 = await repo.create(name="list-b")

        items = await repo.list()
        ids = [i.id for i in items]
        assert item1.id in ids
        assert item2.id in ids

    async def test_update(self, db_session, test_engine):
        await _ensure_table(test_engine)
        from app.repositories.base import BaseRepository

        repo = BaseRepository(RepoItem, db_session)
        item = await repo.create(name="before")

        updated = await repo.update(item.id, name="after")
        assert updated.name == "after"

        fetched = await repo.get(item.id)
        assert fetched.name == "after"

    async def test_soft_delete(self, db_session, test_engine):
        await _ensure_table(test_engine)
        from app.repositories.base import BaseRepository

        repo = BaseRepository(RepoItem, db_session)
        item = await repo.create(name="to-delete")

        await repo.soft_delete(item.id)
        fetched = await repo.get(item.id)
        assert fetched is None

        items = await repo.list()
        ids = [i.id for i in items]
        assert item.id not in ids

    async def test_include_deleted(self, db_session, test_engine):
        await _ensure_table(test_engine)
        from app.repositories.base import BaseRepository

        repo = BaseRepository(RepoItem, db_session)
        item = await repo.create(name="include-test")
        await repo.soft_delete(item.id)

        with_deleted = await repo.list(include_deleted=True)
        ids = [i.id for i in with_deleted]
        assert item.id in ids


class TestTenantScopedRepository:
    async def test_tenant_scoped_create(self, db_session, test_engine):
        await _ensure_table(test_engine)
        from app.repositories.base import TenantScopedRepository

        tid1 = uuid.uuid4()
        repo = TenantScopedRepository(TenantRepoItem, db_session, tid1)

        item = await repo.create(name="tenant-item")
        assert item.tenant_id == tid1

    async def test_tenant_scoped_get(self, db_session, test_engine):
        await _ensure_table(test_engine)
        from app.repositories.base import TenantScopedRepository

        tid1 = uuid.uuid4()
        repo1 = TenantScopedRepository(TenantRepoItem, db_session, tid1)

        item = await repo1.create(name="ten-a-item")

        fetched = await repo1.get(item.id)
        assert fetched is not None
        assert fetched.id == item.id

    async def test_cross_tenant_isolation(self, db_session, test_engine):
        await _ensure_table(test_engine)
        from app.repositories.base import TenantScopedRepository

        tid_a = uuid.uuid4()
        tid_b = uuid.uuid4()

        repo_a = TenantScopedRepository(TenantRepoItem, db_session, tid_a)
        repo_b = TenantScopedRepository(TenantRepoItem, db_session, tid_b)

        item_a = await repo_a.create(name="item-a")
        item_b = await repo_b.create(name="item-b")

        assert item_a.tenant_id == tid_a
        assert item_b.tenant_id == tid_b

        items_a = await repo_a.list()
        a_ids = [i.id for i in items_a]
        assert item_a.id in a_ids
        assert item_b.id not in a_ids

        items_b = await repo_b.list()
        b_ids = [i.id for i in items_b]
        assert item_b.id in b_ids
        assert item_a.id not in b_ids

    async def test_tenant_scoped_soft_delete_isolation(self, db_session, test_engine):
        await _ensure_table(test_engine)
        from app.repositories.base import TenantScopedRepository

        tid = uuid.uuid4()
        repo = TenantScopedRepository(TenantRepoItem, db_session, tid)

        item = await repo.create(name="delete-isolation")
        await repo.soft_delete(item.id)

        fetched = await repo.get(item.id)
        assert fetched is None

        with_deleted = await repo.list(include_deleted=True)
        ids = [i.id for i in with_deleted]
        assert item.id in ids
