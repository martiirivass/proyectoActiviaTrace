import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.encrypted_types import EncryptedString
from app.models.mixins import SoftDeleteMixin


class User(SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    legajo: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    apellido: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dni: Mapped[str | None] = mapped_column(EncryptedString(255), nullable=True)
    cuil: Mapped[str | None] = mapped_column(EncryptedString(255), nullable=True)
    cbu: Mapped[str | None] = mapped_column(EncryptedString(500), nullable=True)
    alias_cbu: Mapped[str | None] = mapped_column(EncryptedString(255), nullable=True)
    banco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    regional: Mapped[str | None] = mapped_column(String(255), nullable=True)
    legajo_profesional: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sexo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    facturador: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estado: Mapped[str] = mapped_column(String(50), default="Activo", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user_tenants = relationship("UserTenant", back_populates="user", lazy="selectin")
    user_roles = relationship("UserRole", back_populates="user", lazy="selectin")
