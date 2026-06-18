import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class OrigenCalificacion(str, enum.Enum):
    IMPORTADO = "Importado"
    MANUAL = "Manual"


class Calificacion(SoftDeleteMixin, Base):
    __tablename__ = "calificacion"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    entrada_padron_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entrada_padron.id"), nullable=False, index=True
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materias.id"), nullable=False, index=True
    )
    actividad: Mapped[str] = mapped_column(String(255), nullable=False)
    nota_numerica: Mapped[float | None] = mapped_column(Float, nullable=True)
    nota_textual: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    origen: Mapped[OrigenCalificacion] = mapped_column(
        Enum(OrigenCalificacion, name="origen_calificacion"), nullable=False, default=OrigenCalificacion.IMPORTADO
    )
    importado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
