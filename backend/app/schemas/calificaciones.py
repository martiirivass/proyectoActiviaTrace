from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class ActividadDetectadaItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str
    tipo: str  # "numerica" or "textual"


class CalificacionPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actividades: list[ActividadDetectadaItem]
    alumnos_count: int
    total_filas: int


class CalificacionConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID
    cohorte_id: UUID
    actividades_seleccionadas: list[str]
    entries: list[dict]


class CalificacionConfirmResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    registros_creados: int
    materia_id: UUID
    cohorte_id: UUID


class UmbralMateriaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asignacion_id: UUID | None = None
    materia_id: UUID
    umbral_pct: int
    valores_aprobatorios: list[str] = []

    @field_validator("umbral_pct")
    @classmethod
    def validate_umbral(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError("umbral_pct debe estar entre 0 y 100")
        return v


class UmbralMateriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    asignacion_id: UUID
    materia_id: UUID
    umbral_pct: int
    valores_aprobatorios: list[str] | None = None


class ReporteFinalizacionPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actividades_textuales: list[str]
    entries: list[dict]


class EntradaSinCorregirItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alumno_nombre: str
    actividad: str
    fecha_finalizacion: str | None = None


class ReporteFinalizacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sin_corregir: list[EntradaSinCorregirItem]
    total: int
