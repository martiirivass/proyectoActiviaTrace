import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class DiaGuardia(str, enum.Enum):
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"
    SABADO = "Sábado"
    DOMINGO = "Domingo"


class EstadoGuardia(str, enum.Enum):
    PENDIENTE = "Pendiente"
    REALIZADA = "Realizada"
    CANCELADA = "Cancelada"


class Guardia(SoftDeleteMixin, Base):
    __tablename__ = "guardias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asignaciones.id"), nullable=False, index=True
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materias.id"), nullable=False, index=True
    )
    carrera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carreras.id"), nullable=False, index=True
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cohortes.id"), nullable=False, index=True
    )
    dia: Mapped[DiaGuardia] = mapped_column(SAEnum(DiaGuardia, name="dia_guardia"), nullable=False)
    horario: Mapped[str] = mapped_column(String(50), nullable=False)
    estado: Mapped[EstadoGuardia] = mapped_column(
        SAEnum(EstadoGuardia, name="estado_guardia"), nullable=False, default=EstadoGuardia.PENDIENTE
    )
    comentarios: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creada_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        {"extend_existing": True},
    )
