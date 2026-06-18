from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EntradaPreviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str
    apellidos: str
    email: str | None = None
    comision: str | None = None
    regional: str | None = None


class PadronPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entries: list[EntradaPreviewItem]
    total_filas: int


class EntradaConfirmItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str
    apellidos: str
    email: str | None = None
    comision: str | None = None
    regional: str | None = None


class PadronConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID
    cohorte_id: UUID
    entries: list[EntradaConfirmItem]


class PadronConfirmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    version_id: UUID
    activa: bool
    filas_creadas: int


class VersionPadronResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    cargado_por: UUID
    cargado_at: datetime
    activa: bool
    entrada_count: int
    created_at: datetime


class VersionPadronListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versiones: list[VersionPadronResponse]
    total: int


class MoodleSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID
    cohorte_id: UUID


class MoodleSyncResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    message: str
    version_id: UUID | None = None


class VaciarMateriaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID
    versiones_afectadas: int
