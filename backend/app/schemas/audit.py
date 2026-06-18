from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    fecha_hora: datetime
    actor_id: UUID
    impersonado_id: UUID | None = None
    materia_id: UUID | None = None
    accion: str
    detalle: dict | None = None
    filas_afectadas: int = 0
    ip: str | None = None
    user_agent: str | None = None
    created_at: datetime
    updated_at: datetime


class AccionesPorDiaItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    total: int


class ComunicacionesPorDocenteItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    docente_id: UUID
    docente_nombre: str
    pendiente: int = 0
    enviando: int = 0
    enviado: int = 0
    error: int = 0
    cancelado: int = 0


class InteraccionesPorDocenteMateriaItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    docente_id: UUID
    docente_nombre: str
    materia_id: UUID
    materia_nombre: str
    total_acciones: int
    acciones: dict[str, int]


class UltimasAccionesItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    fecha_hora: datetime
    actor_id: UUID
    materia_id: UUID | None = None
    accion: str
    filas_afectadas: int = 0
    ip: str | None = None
    user_agent: str | None = None


class DashboardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acciones_por_dia: list[AccionesPorDiaItem]
    comunicaciones_por_docente: list[ComunicacionesPorDocenteItem]
    interacciones_por_docente_materia: list[InteraccionesPorDocenteMateriaItem]
    ultimas_acciones: list[UltimasAccionesItem]
    total: int
