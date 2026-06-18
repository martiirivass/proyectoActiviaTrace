import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class AlcanceAviso(str, enum.Enum):
    Global = "Global"
    PorMateria = "PorMateria"
    PorCohorte = "PorCohorte"
    PorRol = "PorRol"


class SeveridadAviso(str, enum.Enum):
    Info = "Info"
    Advertencia = "Advertencia"
    Critico = "Critico"


class Aviso(SoftDeleteMixin, Base):
    __tablename__ = "avisos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    alcance: Mapped[AlcanceAviso] = mapped_column(SAEnum(AlcanceAviso, name="alcance_aviso"), nullable=False)
    materia_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("materias.id"), nullable=True)
    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cohortes.id"), nullable=True)
    rol_destino: Mapped[str | None] = mapped_column(String(50), nullable=True)
    severidad: Mapped[SeveridadAviso] = mapped_column(SAEnum(SeveridadAviso, name="severidad_aviso"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    inicio_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requiere_ack: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    acknowledgments = relationship("AcknowledgmentAviso", back_populates="aviso", lazy="selectin")

    __table_args__ = (
        {"extend_existing": True},
    )
