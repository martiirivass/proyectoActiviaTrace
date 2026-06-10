from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class AsignacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usuario_id: UUID
    rol: str
    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    dictado_id: UUID | None = None
    comisiones: dict | None = None
    responsable_id: UUID | None = None
    desde: date
    hasta: date | None = None


class AsignacionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rol: str | None = None
    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    dictado_id: UUID | None = None
    comisiones: dict | None = None
    responsable_id: UUID | None = None
    desde: date | None = None
    hasta: date | None = None


class AsignacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    rol: str
    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    dictado_id: UUID | None = None
    comisiones: dict | None = None
    responsable_id: UUID | None = None
    desde: date
    hasta: date | None = None
    estado_vigencia: str = ""
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class AsignacionList(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    items: list[AsignacionResponse]
    total: int
