from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CarreraCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigo: str
    nombre: str


class CarreraUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigo: str | None = None
    nombre: str | None = None
    estado: str | None = None


class CarreraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    estado: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class CarreraList(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    items: list[CarreraResponse]
    total: int


class CohorteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    carrera_id: UUID
    nombre: str
    anio: int
    vig_desde: datetime | None = None
    vig_hasta: datetime | None = None


class CohorteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str | None = None
    anio: int | None = None
    vig_desde: datetime | None = None
    vig_hasta: datetime | None = None
    estado: str | None = None


class CohorteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    tenant_id: UUID
    carrera_id: UUID
    nombre: str
    anio: int
    vig_desde: datetime | None
    vig_hasta: datetime | None
    estado: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class CohorteList(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    items: list[CohorteResponse]
    total: int


class MateriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigo: str
    nombre: str


class MateriaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigo: str | None = None
    nombre: str | None = None
    estado: str | None = None


class MateriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    estado: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class MateriaList(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    items: list[MateriaResponse]
    total: int


class DictadoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    nombre: str


class DictadoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str | None = None


class DictadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    tenant_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    nombre: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class DictadoList(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    items: list[DictadoResponse]
    total: int
