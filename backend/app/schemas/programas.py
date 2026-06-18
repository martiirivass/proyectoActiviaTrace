from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProgramaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str
    referencia_archivo: str | None = None


class ProgramaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titulo: str | None = None
    referencia_archivo: str | None = None


class ProgramaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    tenant_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str
    referencia_archivo: str | None
    cargado_at: datetime
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
