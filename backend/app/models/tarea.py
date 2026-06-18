import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class EstadoTarea(str, enum.Enum):
    Pendiente = "Pendiente"
    EnProgreso = "EnProgreso"
    Resuelta = "Resuelta"
    Cancelada = "Cancelada"


class Tarea(SoftDeleteMixin, Base):
    __tablename__ = "tareas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    materia_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("materias.id"), nullable=True)
    asignado_a: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    asignado_por: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    estado: Mapped[EstadoTarea] = mapped_column(SAEnum(EstadoTarea, name="estado_tarea"), nullable=False, default=EstadoTarea.Pendiente)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    contexto_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    comentarios = relationship("ComentarioTarea", back_populates="tarea", lazy="selectin")

    __table_args__ = (
        {"extend_existing": True},
    )
