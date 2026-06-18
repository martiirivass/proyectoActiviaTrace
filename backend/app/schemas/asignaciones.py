from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


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


class AsignacionMasivaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dictado_id: UUID
    rol: str
    desde: date
    hasta: date | None = None
    usuario_ids: list[UUID]

    @field_validator("usuario_ids")
    @classmethod
    def check_not_empty(cls, v: list[UUID]) -> list[UUID]:
        if not v:
            raise ValueError("La lista de usuarios no puede estar vacía")
        return v


class ClonarEquipoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dictado_origen_id: UUID
    dictado_destino_id: UUID
    force: bool = False


class VigenciaUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    desde: date
    hasta: date | None = None

    @model_validator(mode="after")
    def validate_fechas(self) -> "VigenciaUpdateRequest":
        if self.hasta is not None and self.desde > self.hasta:
            raise ValueError("La fecha 'desde' no puede ser posterior a 'hasta'")
        return self


class DictadoInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    nombre: str
    materia_nombre: str
    carrera_nombre: str
    cohorte_nombre: str


class AsignacionConDictadoResponse(BaseModel):
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
    dictado: DictadoInfoResponse | None = None


class VigenciaUpdateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actualizadas: int
