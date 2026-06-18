from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class SlotEncuentroCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    asignacion_id: UUID
    titulo: str
    hora: time
    dia_semana: str | None = None
    fecha_inicio: date | None = None
    cant_semanas: int = 0
    fecha_unica: date | None = None
    meet_url: str | None = None

    @model_validator(mode="after")
    def validate_modo(self) -> "SlotEncuentroCreate":
        es_recurrente = self.cant_semanas > 0
        es_unico = self.fecha_unica is not None

        if es_recurrente and es_unico:
            raise ValueError("Los modos recurrente y único son mutuamente excluyentes. "
                             "No puede haber cant_semanas > 0 y fecha_unica simultáneamente.")
        if es_recurrente:
            if not self.dia_semana:
                raise ValueError("Para modo recurrente se requiere dia_semana y fecha_inicio.")
            if not self.fecha_inicio:
                raise ValueError("Para modo recurrente se requiere fecha_inicio.")
        if es_unico:
            if self.dia_semana:
                raise ValueError("Para modo único no debe enviarse dia_semana.")
            if self.fecha_inicio:
                raise ValueError("Para modo único no debe enviarse fecha_inicio.")
        if not es_recurrente and not es_unico:
            raise ValueError("Debe especificarse modo recurrente (cant_semanas > 0 con dia_semana y fecha_inicio) "
                             "o único (fecha_unica).")
        return self


class SlotEncuentroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    asignacion_id: UUID
    materia_id: UUID
    titulo: str
    hora: time
    dia_semana: str | None = None
    fecha_inicio: date | None = None
    cant_semanas: int
    fecha_unica: date | None = None
    meet_url: str | None = None
    vig_desde: date
    vig_hasta: date | None = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class SlotEncuentroDetail(SlotEncuentroResponse):
    """Slot detail with nested instancias."""
    instancias: list["InstanciaResponse"] = []


class InstanciaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str | None = None
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, v: str | None) -> str | None:
        if v is not None and v not in ("Programado", "Realizado", "Cancelado"):
            raise ValueError("Estado debe ser Programado, Realizado o Cancelado")
        return v


class InstanciaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    slot_id: UUID | None = None
    materia_id: UUID
    fecha: date
    hora: time
    titulo: str
    estado: str
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class InstanciaListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[InstanciaResponse]
    total: int


class EncuentroAdminResponse(BaseModel):
    """Instancia con datos del slot, materia y docente."""
    model_config = ConfigDict(extra="forbid")

    id: UUID
    fecha: date
    hora: time
    titulo: str
    estado: str
    meet_url: str | None = None
    video_url: str | None = None
    materia_id: UUID
    materia_nombre: str = ""
    docente_nombre: str = ""
    slot_id: UUID | None = None


class EncuentroAdminListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[EncuentroAdminResponse]
    total: int
