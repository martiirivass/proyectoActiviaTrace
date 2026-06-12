import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class EstadoReserva(str, enum.Enum):
    ACTIVA = "Activa"
    CANCELADA = "Cancelada"


class ReservaEvaluacion(SoftDeleteMixin, Base):
    __tablename__ = "reservas_evaluacion"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    evaluacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluaciones.id"), nullable=False, index=True)
    dia_convocatoria_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dias_convocatoria.id"), nullable=False, index=True)
    alumno_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    estado: Mapped[EstadoReserva] = mapped_column(SAEnum(EstadoReserva, name="estado_reserva"), nullable=False, default=EstadoReserva.ACTIVA)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        {"extend_existing": True},
    )
