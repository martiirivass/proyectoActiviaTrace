from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.fecha_academica import TipoFecha


class FechaAcademicaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID
    cohorte_id: UUID
    tipo: TipoFecha
    numero: int
    periodo: str
    fecha: date
    titulo: str

    @field_validator("numero")
    @classmethod
    def numero_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("numero must be positive")
        return v

    @field_validator("periodo")
    @classmethod
    def periodo_must_match_format(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{4}-[12]$", v):
            raise ValueError('periodo must match format YYYY-S (e.g. "2026-1")')
        return v


class FechaAcademicaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: TipoFecha | None = None
    numero: int | None = None
    periodo: str | None = None
    fecha: date | None = None
    titulo: str | None = None


class FechaAcademicaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: TipoFecha
    numero: int
    periodo: str
    fecha: date
    titulo: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class FechasExportLMSResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contenido: str
