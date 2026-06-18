from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class ComunicacionPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asunto: str
    cuerpo: str
    materia_id: UUID
    destinatarios: list[str]

    @field_validator("asunto")
    @classmethod
    def asunto_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El asunto no puede estar vacío")
        return v.strip()

    @field_validator("cuerpo")
    @classmethod
    def cuerpo_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El cuerpo no puede estar vacío")
        return v.strip()

    @field_validator("destinatarios")
    @classmethod
    def destinatarios_no_vacio(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Debe haber al menos un destinatario")
        return v


class ComunicacionPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asunto: str
    cuerpo_renderizado: str
    cantidad_destinatarios: int


class ComunicacionIndividualRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asunto: str
    cuerpo: str
    materia_id: UUID
    destinatario_email: str

    @field_validator("asunto")
    @classmethod
    def asunto_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El asunto no puede estar vacío")
        return v.strip()

    @field_validator("cuerpo")
    @classmethod
    def cuerpo_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El cuerpo no puede estar vacío")
        return v.strip()

    @field_validator("destinatario_email")
    @classmethod
    def email_valido(cls, v: str) -> str:
        if "@" not in v or not v.strip():
            raise ValueError("Email inválido")
        return v.strip()


class ComunicacionIndividualResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    estado: str


class ComunicacionMasivaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asunto: str
    cuerpo: str
    materia_id: UUID
    destinatarios: list[str]

    @field_validator("asunto")
    @classmethod
    def asunto_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El asunto no puede estar vacío")
        return v.strip()

    @field_validator("cuerpo")
    @classmethod
    def cuerpo_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El cuerpo no puede estar vacío")
        return v.strip()

    @field_validator("destinatarios")
    @classmethod
    def destinatarios_no_vacio(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Debe haber al menos un destinatario")
        return v


class ComunicacionMasivaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lote_id: UUID
    total_mensajes: int
    estado_lote: str


class ComunicacionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    destinatario: str
    asunto: str
    estado: str
    created_at: datetime
    enviado_at: datetime | None = None
    error_msg: str | None = None


class ComunicacionDetalle(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    destinatario: str
    asunto: str
    cuerpo: str
    estado: str
    materia_id: UUID
    created_at: datetime
    enviado_at: datetime | None = None
    error_msg: str | None = None


class LotePendienteItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    materia_id: UUID
    enviado_por: UUID
    total_mensajes: int
    created_at: datetime


class DistribucionEstados(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pendiente: int = 0
    enviando: int = 0
    enviado: int = 0
    error: int = 0
    cancelado: int = 0


class LoteDetalle(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    materia_id: UUID
    total_mensajes: int
    estado: str
    aprobado_por: UUID | None = None
    aprobado_en: datetime | None = None
    distribucion_estados: DistribucionEstados


class AprobarLoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lote_id: UUID


class AprobarLoteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lote_id: UUID
    estado: str
    mensajes_liberados: int


class RechazarLoteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lote_id: UUID
    estado: str
    mensajes_cancelados: int


class ComunicacionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ComunicacionItem]
    total: int
    offset: int
    limit: int
