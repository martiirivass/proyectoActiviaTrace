from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class SoftDeleteMixin:
    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        return mapped_column(Boolean, default=False, nullable=False)

    @declared_attr
    def deleted_at(cls) -> Mapped[datetime | None]:
        return mapped_column(DateTime(timezone=True), nullable=True, default=None)

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
