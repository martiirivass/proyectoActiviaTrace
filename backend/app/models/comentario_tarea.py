import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class ComentarioTarea(SoftDeleteMixin, Base):
    __tablename__ = "comentarios_tarea"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    tarea_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tareas.id"), nullable=False)
    autor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    creado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tarea = relationship("Tarea", back_populates="comentarios")

    __table_args__ = (
        {"extend_existing": True},
    )
