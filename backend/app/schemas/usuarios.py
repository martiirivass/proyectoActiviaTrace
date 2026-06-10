from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    password: str
    nombre: str
    apellido: str
    legajo: str | None = None
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo_profesional: str | None = None
    facturador: bool = False
    estado: str = "Activo"


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str | None = None
    password: str | None = None
    nombre: str | None = None
    apellido: str | None = None
    legajo: str | None = None
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None
    estado: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    tenant_id: UUID
    email: str
    legajo: str | None = None
    nombre: str
    apellido: str
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo_profesional: str | None = None
    facturador: bool
    estado: str
    is_2fa_enabled: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class UserList(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    items: list[UserResponse]
    total: int
