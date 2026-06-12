import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class EstadoResultado(str, enum.Enum):
    BORRADOR = "Borrador"
    DEFINITIVO = "Definitivo"


class ResultadoEvaluacion(SoftDeleteMixin, Base):
    __tablename__ = "resultados_evaluacion"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    evaluacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluaciones.id"), nullable=False, index=True)
    alumno_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    nota_final: Mapped[str] = mapped_column(String(50), nullable=False)
    estado: Mapped[EstadoResultado] = mapped_column(SAEnum(EstadoResultado, name="estado_resultado"), nullable=False, default=EstadoResultado.BORRADOR)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        {"extend_existing": True},
    )
