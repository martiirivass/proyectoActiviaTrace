import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin


class RolLiquidacion(str, enum.Enum):
    PROFESOR = "PROFESOR"
    TUTOR = "TUTOR"
    NEXO = "NEXO"
    COORDINADOR = "COORDINADOR"


class EstadoLiquidacion(str, enum.Enum):
    Abierta = "Abierta"
    Cerrada = "Cerrada"


class EstadoFactura(str, enum.Enum):
    Pendiente = "Pendiente"
    Abonada = "Abonada"


class Liquidacion(SoftDeleteMixin, Base):
    __tablename__ = "liquidaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cohortes.id"), nullable=False)
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rol: Mapped[RolLiquidacion] = mapped_column(String(50), nullable=False)
    comisiones: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    monto_base: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    monto_plus: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    es_nexo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    excluido_por_factura: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estado: Mapped[EstadoLiquidacion] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "cohorte_id", "periodo", "usuario_id", name="uq_liquidacion_tenant_cohorte_periodo_usuario"),
        {"extend_existing": True},
    )
