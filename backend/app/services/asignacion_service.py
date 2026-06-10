from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.asignacion_repository import AsignacionRepository

ROLES_VALIDOS = {"ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"}


def compute_estado_vigencia(asignacion: Asignacion) -> str:
    today = date.today()
    if asignacion.hasta is not None and today > asignacion.hasta:
        return "Vencida"
    return "Vigente"


class AsignacionService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = AsignacionRepository(Asignacion, session, tenant_id)

    async def create(self, data) -> Asignacion:
        if data.rol not in ROLES_VALIDOS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Rol inválido: {data.rol}")
        return await self.repo.create(**data.model_dump())

    async def get(self, id: UUID) -> Asignacion:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
        return obj

    async def list(
        self,
        usuario_id: UUID | None = None,
        materia_id: UUID | None = None,
        rol: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Asignacion]:
        return await self.repo.list(
            usuario_id=usuario_id,
            materia_id=materia_id,
            rol=rol,
            offset=offset,
            limit=limit,
        )

    async def update(self, id: UUID, data) -> Asignacion:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
        kwargs = data.model_dump(exclude_none=True)
        if "rol" in kwargs and kwargs["rol"] not in ROLES_VALIDOS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Rol inválido: {kwargs['rol']}")
        return await self.repo.update(id, **kwargs)

    async def delete(self, id: UUID) -> None:
        await self.repo.soft_delete(id)

    @staticmethod
    def is_vigente(asignacion: Asignacion) -> bool:
        return compute_estado_vigencia(asignacion) == "Vigente"
