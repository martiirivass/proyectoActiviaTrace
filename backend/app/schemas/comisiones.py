from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ComisionResponse(BaseModel):
    """Comisión (materia + cohorte) visible para un docente."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    materia_nombre: str
    cohorte_nombre: str
    alumnos_count: int
    atrasados_count: int = 0
    pendientes_count: int = 0
