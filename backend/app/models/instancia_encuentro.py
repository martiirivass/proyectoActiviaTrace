import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, String, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class EstadoInstancia(str, enum.Enum):
    PROGRAMADO = "Programado"
    REALIZADO = "Realizado"
    CANCELADO = "Cancelado"


class InstanciaEncuentro(SoftDeleteMixin, Base):
    __tablename__ = "instancia_encuentro"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("slot_encuentro.id"), nullable=True, index=True
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materias.id"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoInstancia] = mapped_column(
        SAEnum(EstadoInstancia, name="estado_instancia"), nullable=False, default=EstadoInstancia.PROGRAMADO
    )
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    comentario: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
