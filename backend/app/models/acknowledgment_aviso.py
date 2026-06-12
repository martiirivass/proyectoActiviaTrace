import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AcknowledgmentAviso(Base):
    __tablename__ = "acknowledgment_aviso"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aviso_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("avisos.id"), nullable=False, index=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    confirmado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("aviso_id", "usuario_id", name="uq_aviso_usuario_ack"),
        {"extend_existing": True},
    )

    # Relationships
    aviso = relationship("Aviso", back_populates="acknowledgments")
