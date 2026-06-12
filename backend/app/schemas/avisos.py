from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class AvisoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str
    cuerpo: str
    alcance: str
    severidad: str
    inicio_en: datetime
    fin_en: datetime
    orden: int = 0
    activo: bool = True
    requiere_ack: bool = False
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = None

    @field_validator("alcance")
    @classmethod
    def validate_alcance(cls, v: str) -> str:
        allowed = {"Global", "PorMateria", "PorCohorte", "PorRol"}
        if v not in allowed:
            raise ValueError(f"Alcance debe ser uno de: {', '.join(sorted(allowed))}")
        return v

    @field_validator("severidad")
    @classmethod
    def validate_severidad(cls, v: str) -> str:
        allowed = {"Info", "Advertencia", "Critico"}
        if v not in allowed:
            raise ValueError(f"Severidad debe ser uno de: {', '.join(sorted(allowed))}")
        return v

    @field_validator("rol_destino")
    @classmethod
    def validate_rol_destino(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"}
            if v not in allowed:
                raise ValueError(f"Rol destino debe ser uno de: {', '.join(sorted(allowed))}")
        return v

    @model_validator(mode="after")
    def validate_alcance_fields(self) -> "AvisoCreate":
        if self.alcance == "PorMateria" and not self.materia_id:
            raise ValueError("materia_id es requerido cuando alcance = PorMateria")
        if self.alcance == "PorCohorte" and not self.cohorte_id:
            raise ValueError("cohorte_id es requerido cuando alcance = PorCohorte")
        if self.alcance == "PorRol" and not self.rol_destino:
            raise ValueError("rol_destino es requerido cuando alcance = PorRol")
        return self

    @model_validator(mode="after")
    def validate_fechas(self) -> "AvisoCreate":
        if self.inicio_en >= self.fin_en:
            raise ValueError("inicio_en debe ser anterior a fin_en")
        return self


class AvisoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = None
    cuerpo: str | None = None
    alcance: str | None = None
    severidad: str | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = None
    activo: bool | None = None
    requiere_ack: bool | None = None
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = None

    @field_validator("alcance")
    @classmethod
    def validate_alcance(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"Global", "PorMateria", "PorCohorte", "PorRol"}
            if v not in allowed:
                raise ValueError(f"Alcance debe ser uno de: {', '.join(sorted(allowed))}")
        return v

    @field_validator("severidad")
    @classmethod
    def validate_severidad(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"Info", "Advertencia", "Critico"}
            if v not in allowed:
                raise ValueError(f"Severidad debe ser uno de: {', '.join(sorted(allowed))}")
        return v

    @field_validator("rol_destino")
    @classmethod
    def validate_rol_destino(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"}
            if v not in allowed:
                raise ValueError(f"Rol destino debe ser uno de: {', '.join(sorted(allowed))}")
        return v

    @model_validator(mode="after")
    def validate_alcance_fields(self) -> "AvisoUpdate":
        if self.alcance == "PorMateria" and not self.materia_id:
            raise ValueError("materia_id es requerido cuando alcance = PorMateria")
        if self.alcance == "PorCohorte" and not self.cohorte_id:
            raise ValueError("cohorte_id es requerido cuando alcance = PorCohorte")
        if self.alcance == "PorRol" and not self.rol_destino:
            raise ValueError("rol_destino es requerido cuando alcance = PorRol")
        return self

    @model_validator(mode="after")
    def validate_fechas(self) -> "AvisoUpdate":
        if self.inicio_en is not None and self.fin_en is not None and self.inicio_en >= self.fin_en:
            raise ValueError("inicio_en debe ser anterior a fin_en")
        return self


class AvisoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    alcance: str
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = None
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    acknowledged: bool = False

    @classmethod
    def from_orm_with_ack(cls, aviso, acknowledged: bool = False) -> "AvisoResponse":
        data = cls.model_validate(aviso).model_dump()
        data["acknowledged"] = acknowledged
        return cls(**data)


class AvisoListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AvisoResponse]
    total: int
    offset: int = 0
    limit: int = 20


class AckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = "Lectura confirmada"


class AckUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    usuario_id: UUID
    nombre: str
    apellidos: str
    email: str
    confirmado_at: datetime


class AckUserListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AckUserResponse]
    total: int
    offset: int = 0
    limit: int = 20


class AvisoStatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aviso_id: UUID
    total_usuarios_alcanzados: int
    total_acknowledgments: int
    porcentaje_confirmacion: float
