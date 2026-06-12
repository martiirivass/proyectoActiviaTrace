import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


# ===== Días de convocatoria =====

class DiaConvocatoriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    cupo_maximo: int


class DiaConvocatoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    evaluacion_id: uuid.UUID
    fecha: date
    cupo_maximo: int
    cupos_ocupados: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


# ===== Convocatoria (Evaluacion) =====

class EvaluacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str = "Coloquio"
    instancia: str
    dias: list[DiaConvocatoriaCreate]

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, v: str) -> str:
        allowed = ("Parcial", "TP", "Coloquio", "Recuperatorio")
        if v not in allowed:
            raise ValueError(f"tipo debe ser uno de {allowed}")
        return v

    @field_validator("dias")
    @classmethod
    def validate_dias(cls, v: list[DiaConvocatoriaCreate]) -> list[DiaConvocatoriaCreate]:
        if not v:
            raise ValueError("Debe especificar al menos un día de convocatoria")
        return v


class EvaluacionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instancia: str | None = None


class EvaluacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    tenant_id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    instancia: str
    activa: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class EvaluacionListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    instancia: str
    activa: bool
    total_convocados: int
    reservas_activas: int
    cupos_libres: int
    created_at: datetime
    updated_at: datetime


class EvaluacionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[EvaluacionListItem]
    total: int


class AlumnoConvocadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    alumno_id: uuid.UUID
    evaluacion_id: uuid.UUID


class ConvocadosUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_ids: list[uuid.UUID]


class EvaluacionDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    instancia: str
    activa: bool
    dias: list[DiaConvocatoriaResponse]
    convocados: list[AlumnoConvocadoResponse]
    total_convocados: int
    reservas_activas: int
    cupos_libres: int
    created_at: datetime
    updated_at: datetime


# ===== Reservas =====

class ReservaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluacion_id: uuid.UUID
    dia_convocatoria_id: uuid.UUID


class ReservaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    evaluacion_id: uuid.UUID
    dia_convocatoria_id: uuid.UUID
    alumno_id: uuid.UUID
    fecha_hora: datetime
    estado: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class ReservaListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    evaluacion_id: uuid.UUID
    dia_convocatoria_id: uuid.UUID
    alumno_id: uuid.UUID
    fecha_hora: datetime
    estado: str
    alumno_nombre: str = ""
    alumno_apellido: str = ""
    evaluacion_instancia: str = ""
    materia_nombre: str = ""


class ReservaListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ReservaListItem]
    total: int


class ReservaAgendaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ReservaListItem]
    total: int


# ===== Resultados =====

class ResultadoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    nota_final: str


class ResultadoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nota_final: str | None = None
    estado: str | None = None

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, v: str | None) -> str | None:
        if v is not None and v not in ("Borrador", "Definitivo"):
            raise ValueError("Estado debe ser Borrador o Definitivo")
        return v


class ResultadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    nota_final: str
    estado: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class ResultadoListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    nota_final: str
    estado: str
    alumno_nombre: str = ""
    alumno_apellido: str = ""
    evaluacion_instancia: str = ""
    materia_nombre: str = ""


class ResultadoListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ResultadoListItem]
    total: int


# ===== Métricas =====

class MetricasResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_alumnos_cargados: int
    instancias_activas: int
    reservas_activas: int
    notas_registradas: int
