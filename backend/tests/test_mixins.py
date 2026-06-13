from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class SoftDeleteItem(SoftDeleteMixin, Base):
    __tablename__ = "soft_delete_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)


async def _ensure_table(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class TestSoftDeleteMixinColumns:
    def test_has_is_deleted_column(self):
        col = SoftDeleteItem.__table__.c["is_deleted"]
        assert isinstance(col.type, Boolean)
        assert not col.nullable

    def test_has_deleted_at_column(self):
        col = SoftDeleteItem.__table__.c["deleted_at"]
        assert isinstance(col.type, DateTime)
        assert col.nullable


class TestSoftDeleteMixinBehavior:
    async def test_defaults_after_persist(self, db_session, test_engine):
        await _ensure_table(test_engine)
        item = SoftDeleteItem(name="test-defaults")
        db_session.add(item)
        await db_session.flush()

        assert item.is_deleted is False
        assert item.deleted_at is None

    async def test_soft_delete_updates_attributes(self, db_session, test_engine):
        await _ensure_table(test_engine)
        item = SoftDeleteItem(name="test-soft-delete")
        db_session.add(item)
        await db_session.flush()

        item.soft_delete()
        await db_session.flush()

        assert item.is_deleted is True
        assert item.deleted_at is not None
        assert isinstance(item.deleted_at, datetime)

    async def test_soft_delete_sets_recent_timestamp(self, db_session, test_engine):
        await _ensure_table(test_engine)
        item = SoftDeleteItem(name="test-timestamp")
        db_session.add(item)
        await db_session.flush()

        before = datetime.now(timezone.utc)
        item.soft_delete()
        await db_session.flush()
        after = datetime.now(timezone.utc)

        assert before <= item.deleted_at <= after
