import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class TipoEvaluacion(str, enum.Enum):
    PARCIAL = "Parcial"
    TP = "TP"
    COLOQUIO = "Coloquio"
    RECUPERATORIO = "Recuperatorio"


class Evaluacion(SoftDeleteMixin, Base):
    __tablename__ = "evaluaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    materia_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("materias.id"), nullable=False, index=True)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cohortes.id"), nullable=False, index=True)
    tipo: Mapped[TipoEvaluacion] = mapped_column(SAEnum(TipoEvaluacion, name="tipo_evaluacion"), nullable=False)
    instancia: Mapped[str] = mapped_column(String(255), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        {"extend_existing": True},
    )


class DiaConvocatoria(SoftDeleteMixin, Base):
    __tablename__ = "dias_convocatoria"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    evaluacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluaciones.id"), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    cupo_maximo: Mapped[int] = mapped_column(Integer, nullable=False)
    cupos_ocupados: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        {"extend_existing": True},
    )


class EvaluacionAlumnoConvocado(SoftDeleteMixin, Base):
    __tablename__ = "evaluacion_alumnos_convocados"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    evaluacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluaciones.id"), nullable=False, index=True)
    alumno_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        {"extend_existing": True},
    )
