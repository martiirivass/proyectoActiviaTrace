import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.encrypted_types import EncryptedString
from app.models.mixins import SoftDeleteMixin


class EstadoComunicacion(str, enum.Enum):
    PENDIENTE = "Pendiente"
    ENVIANDO = "Enviando"
    ENVIADO = "Enviado"
    ERROR = "Error"
    CANCELADO = "Cancelado"


class Comunicacion(SoftDeleteMixin, Base):
    __tablename__ = "comunicacion"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lote_comunicacion.id"), nullable=True, index=True
    )
    enviado_por: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materias.id"), nullable=False, index=True
    )
    destinatario: Mapped[str] = mapped_column(EncryptedString(255), nullable=False)
    asunto: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo: Mapped[str] = mapped_column(String(5000), nullable=False)
    estado: Mapped[EstadoComunicacion] = mapped_column(
        Enum(EstadoComunicacion, name="estado_comunicacion"),
        nullable=False,
        default=EstadoComunicacion.PENDIENTE,
    )
    error_msg: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    enviado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
