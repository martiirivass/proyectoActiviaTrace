from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TareaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignado_a: UUID
    descripcion: str
    materia_id: UUID | None = None
    contexto_id: UUID | None = None


class TareaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str | None = None
    asignado_a: UUID | None = None
    descripcion: str | None = None


class TareaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID | None = None
    asignado_a: UUID
    asignado_por: UUID
    estado: str
    descripcion: str
    contexto_id: UUID | None = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class TareaListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[TareaResponse]
    total: int
    offset: int = 0
    limit: int = 50


class ComentarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str = Field(..., min_length=1)


class ComentarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    tarea_id: UUID
    autor_id: UUID
    texto: str
    creado_at: datetime
    is_deleted: bool
