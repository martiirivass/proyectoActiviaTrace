import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class AvisoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alcance: str
    materia_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    rol_destino: str | None = None
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int = 0
    activo: bool = True
    requiere_ack: bool = False

    @field_validator("cuerpo")
    @classmethod
    def cuerpo_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El cuerpo no puede estar vacío")
        return v.strip()


class AvisoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alcance: str | None = None
    materia_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    rol_destino: str | None = None
    severidad: str | None = None
    titulo: str | None = None
    cuerpo: str | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = None
    activo: bool | None = None
    requiere_ack: bool | None = None


class AvisoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    tenant_id: uuid.UUID
    alcance: str
    materia_id: uuid.UUID | None
    cohorte_id: uuid.UUID | None
    rol_destino: str | None
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class AvisoDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    tenant_id: uuid.UUID
    alcance: str
    materia_id: uuid.UUID | None
    cohorte_id: uuid.UUID | None
    rol_destino: str | None
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    total_vistos: int = 0
    total_confirmados: int = 0


class AvisoListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    alcance: str
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    created_at: datetime
    updated_at: datetime


class AvisoListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AvisoListItem]
    total: int


class AcknowledgmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    aviso_id: uuid.UUID
    usuario_id: uuid.UUID
    confirmado_at: datetime
    created_at: datetime


class ConfirmacionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: uuid.UUID
    confirmado_at: datetime | None


class MetricasAvisoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aviso_id: uuid.UUID
    total_vistos: int
    total_confirmados: int
    confirmaciones: list[ConfirmacionItem]
