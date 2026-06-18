import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class DiaSemana(str, enum.Enum):
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"
    SABADO = "Sábado"
    DOMINGO = "Domingo"


class SlotEncuentro(SoftDeleteMixin, Base):
    __tablename__ = "slot_encuentro"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    asignacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("asignaciones.id"), nullable=False, index=True)
    materia_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("materias.id"), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    hora: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    dia_semana: Mapped[DiaSemana | None] = mapped_column(Enum(DiaSemana, name="dia_semana"), nullable=True)
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    cant_semanas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fecha_unica: Mapped[date | None] = mapped_column(Date, nullable=True)
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
