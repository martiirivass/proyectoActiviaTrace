import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class TipoFecha(str, enum.Enum):
    PARCIAL = "Parcial"
    TP = "TP"
    COLOQUIO = "Coloquio"
    RECUPERATORIO = "Recuperatorio"


class FechaAcademica(SoftDeleteMixin, Base):
    __tablename__ = "fechas_academicas"

    __table_args__ = (
        UniqueConstraint(
            "materia_id", "cohorte_id", "tipo", "numero", "periodo",
            name="uq_fecha_materia_cohorte_tipo_numero_periodo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    materia_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("materias.id"), nullable=False, index=True)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cohortes.id"), nullable=False, index=True)
    tipo: Mapped[TipoFecha] = mapped_column(Enum(TipoFecha, name="tipo_fecha"), nullable=False, index=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
