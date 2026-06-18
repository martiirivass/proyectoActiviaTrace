import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.liquidacion import EstadoFactura
from app.models.mixins import SoftDeleteMixin


class Factura(SoftDeleteMixin, Base):
    __tablename__ = "facturas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    periodo: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    referencia_archivo: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tamano_kb: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estado: Mapped[EstadoFactura] = mapped_column(String(20), nullable=False)
    cargada_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    abonada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    materia_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("materias.id"), nullable=True)

    __table_args__ = (
        {"extend_existing": True},
    )
