from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.programa_materia import ProgramaMateria
from app.repositories.programa_repository import ProgramaMateriaRepository
from app.services.audit_service import AuditService


class ProgramaService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = ProgramaMateriaRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.audit = AuditService(session)

    async def create(
        self,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id: UUID,
        titulo: str,
        referencia_archivo: str | None = None,
        actor_id: UUID | None = None,
    ) -> ProgramaMateria:
        existing = await self.repo.find_by_materia_carrera_cohorte(materia_id, carrera_id, cohorte_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un programa para esa materia, carrera y cohorte",
            )
        obj = await self.repo.create(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            titulo=titulo,
            referencia_archivo=referencia_archivo,
        )
        if actor_id:
            await self.audit.log(
                tenant_id=self.tenant_id,
                actor_id=actor_id,
                accion="PROGRAMA_CREAR",
                materia_id=materia_id,
                detalle={
                    "programa_id": str(obj.id),
                    "titulo": titulo,
                    "carrera_id": str(carrera_id),
                    "cohorte_id": str(cohorte_id),
                },
            )
        return obj

    async def get(self, id: UUID) -> ProgramaMateria:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programa no encontrado")
        return obj

    async def list(
        self,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> list[ProgramaMateria]:
        return await self.repo.list(materia_id=materia_id, carrera_id=carrera_id, cohorte_id=cohorte_id)

    async def update(
        self,
        id: UUID,
        titulo: str | None = None,
        referencia_archivo: str | None = None,
        actor_id: UUID | None = None,
    ) -> ProgramaMateria:
        kwargs = {}
        if titulo is not None:
            kwargs["titulo"] = titulo
        if referencia_archivo is not None:
            kwargs["referencia_archivo"] = referencia_archivo
        obj = await self.repo.update(id, **kwargs)
        if actor_id:
            await self.audit.log(
                tenant_id=self.tenant_id,
                actor_id=actor_id,
                accion="PROGRAMA_EDITAR",
                materia_id=obj.materia_id,
                detalle={
                    "programa_id": str(id),
                    **kwargs,
                },
            )
        return obj

    async def delete(self, id: UUID, actor_id: UUID | None = None) -> None:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programa no encontrado")
        await self.repo.soft_delete(id)
        if actor_id:
            await self.audit.log(
                tenant_id=self.tenant_id,
                actor_id=actor_id,
                accion="PROGRAMA_ELIMINAR",
                materia_id=obj.materia_id,
                detalle={"programa_id": str(id)},
            )
