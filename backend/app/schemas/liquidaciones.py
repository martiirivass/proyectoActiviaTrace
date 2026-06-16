from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

import re


# =============================================================================
# SalarioBase
# =============================================================================


class SalarioBaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rol: str
    monto: Decimal = Field(max_digits=10, decimal_places=2)
    desde: date
    hasta: date | None = None

    @field_validator("rol")
    @classmethod
    def validate_rol(cls, v: str) -> str:
        allowed = {"PROFESOR", "TUTOR", "NEXO", "COORDINADOR"}
        if v not in allowed:
            raise ValueError(f"Rol debe ser uno de: {', '.join(sorted(allowed))}")
        return v


class SalarioBaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monto: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    hasta: date | None = None  # None = no change, explicit sentinel if needed


class SalarioBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    rol: str
    monto: Decimal
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# SalarioPlus
# =============================================================================


class SalarioPlusCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grupo: str = Field(max_length=50)
    rol: str
    descripcion: str = Field(max_length=255)
    monto: Decimal = Field(max_digits=10, decimal_places=2)
    desde: date
    hasta: date | None = None

    @field_validator("rol")
    @classmethod
    def validate_rol(cls, v: str) -> str:
        allowed = {"PROFESOR", "TUTOR", "NEXO", "COORDINADOR"}
        if v not in allowed:
            raise ValueError(f"Rol debe ser uno de: {', '.join(sorted(allowed))}")
        return v


class SalarioPlusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monto: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    descripcion: str | None = Field(default=None, max_length=255)
    hasta: date | None = None


class SalarioPlusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Liquidacion
# =============================================================================


class LiquidacionCalcularRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohorte_id: UUID
    periodo: str  # AAAA-MM

    @field_validator("periodo")
    @classmethod
    def validate_periodo(cls, v: str) -> str:
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError("Periodo debe tener formato AAAA-MM (ej: 2026-06)")
        return v


class LiquidacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    cohorte_id: UUID
    periodo: str
    usuario_id: UUID
    rol: str
    comisiones: dict | None
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: str
    created_at: datetime
    updated_at: datetime


class LiquidacionCalcularResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    creadas: int
    items: list[LiquidacionResponse]


class LiquidacionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[LiquidacionResponse]
    total: int
    offset: int
    limit: int


# =============================================================================
# Factura
# =============================================================================


class FacturaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    periodo: str
    detalle: str
    referencia_archivo: str = Field(max_length=512)
    tamano_kb: Decimal = Field(max_digits=10, decimal_places=2)
    materia_id: UUID | None = None  # PA-24: optional comisión association

    @field_validator("periodo")
    @classmethod
    def validate_periodo(cls, v: str) -> str:
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError("Periodo debe tener formato AAAA-MM (ej: 2026-06)")
        return v


class FacturaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    periodo: str
    detalle: str
    referencia_archivo: str
    tamano_kb: Decimal
    estado: str
    materia_id: UUID | None
    cargada_at: datetime | None
    abonada_at: datetime | None


class FacturaListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[FacturaResponse]
    total: int
    offset: int
    limit: int


# =============================================================================
# KPIs
# =============================================================================


class KPIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periodo: str
    cohorte_id: UUID | None
    total_facturantes_count: int
    total_facturantes_sum: Decimal
    total_no_facturantes_count: int
    total_no_facturantes_sum: Decimal
