from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class MensajeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destinatario_id: UUID
    asunto: str
    cuerpo: str

    @field_validator("asunto")
    @classmethod
    def asunto_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("asunto must not be empty")
        return v.strip()

    @field_validator("cuerpo")
    @classmethod
    def cuerpo_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("cuerpo must not be empty")
        return v.strip()


class MensajeResponderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cuerpo: str

    @field_validator("cuerpo")
    @classmethod
    def cuerpo_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("cuerpo must not be empty")
        return v.strip()


class MensajeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    tenant_id: UUID
    hilo_id: UUID
    remitente_id: UUID
    destinatario_id: UUID
    asunto: str
    cuerpo: str
    leido: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class HiloResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hilo_id: UUID
    remitente_id: UUID
    remitente_nombre: str
    asunto: str
    ultimo_mensaje: str
    ultima_fecha: datetime
    no_leidos: int
