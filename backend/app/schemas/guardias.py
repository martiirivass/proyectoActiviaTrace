from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class GuardiaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignacion_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    dia: str
    horario: str
    comentarios: str | None = None

    @field_validator("dia")
    @classmethod
    def validate_dia(cls, v: str) -> str:
        dias_validos = {"Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"}
        if v not in dias_validos:
            raise ValueError(f"Día inválido. Debe ser uno de: {', '.join(sorted(dias_validos))}")
        return v

    @field_validator("horario")
    @classmethod
    def validate_horario(cls, v: str) -> str:
        if not v or len(v) > 50:
            raise ValueError("Horario debe tener entre 1 y 50 caracteres")
        return v


class GuardiaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str
    comentarios: str | None = None

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, v: str) -> str:
        if v not in ("Pendiente", "Realizada", "Cancelada"):
            raise ValueError("Estado debe ser Pendiente, Realizada o Cancelada")
        return v


class GuardiaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    asignacion_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    dia: str
    horario: str
    estado: str
    comentarios: str | None = None
    creada_at: datetime
    is_deleted: bool


class GuardiaListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[GuardiaResponse]
    total: int
