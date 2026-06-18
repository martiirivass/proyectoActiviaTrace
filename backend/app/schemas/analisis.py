"""Pydantic schemas for analisis endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AtrasadoItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: str
    alumno_nombre: str
    alumno_apellido: str
    email: str
    actividad: str
    nota: float | None = None
    causa: str  # "actividad_faltante" | "nota_bajo_umbral"


class AtrasadosResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AtrasadoItem]
    total: int


class RankingItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: str
    alumno_nombre: str
    alumno_apellido: str
    email: str
    comision: str | None = None
    posicion: int = 0
    aprobadas: int
    total: int
    porcentaje: float


class RankingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RankingItem]
    total: int


class ActividadReporteItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str
    alumnos_con_nota: int
    promedio: float | None = None
    aprobados: int
    desaprobados: int


class ReporteRapidoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_alumnos: int
    total_actividades: int
    promedio_general: float | None = None
    total_aprobados: int
    total_desaprobados: int
    porcentaje_aprobacion: float | None = None
    actividades: list[ActividadReporteItem]


class ActividadDetalleItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str
    nota: str | float | None = None


class NotaFinalItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: str
    alumno_nombre: str
    alumno_apellido: str
    email: str
    comision: str | None = None
    actividades_consideradas: int
    nota_final: float | None = None
    actividades: list[ActividadDetalleItem] = []


class NotasFinalesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[NotaFinalItem]
    total: int


class MonitorGeneralItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_nombre: str
    email: str | None = None
    comision: str | None = None
    regional: str | None = None
    materia_nombre: str | None = None
    total_actividades: int
    aprobadas: int
    desaprobadas: int
    pendientes: int
    porcentaje_avance: float


class MonitorGeneralResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[MonitorGeneralItem]
    total: int
    page: int
    page_size: int
    next_page: int | None = None
    prev_page: int | None = None


class MonitorSeguimientoItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_nombre: str
    email: str | None = None
    comision: str | None = None
    regional: str | None = None
    total_actividades: int
    aprobadas: int
    desaprobadas: int
    pendientes: int
    porcentaje_aprobacion: float
