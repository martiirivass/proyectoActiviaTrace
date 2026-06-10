from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.dictado import Dictado
from app.models.materia import Materia
from app.repositories.carrera_repository import CarreraRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.dictado_repository import DictadoRepository
from app.repositories.materia_repository import MateriaRepository


class CarreraService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = CarreraRepository(Carrera, session, tenant_id)

    async def create(self, codigo: str, nombre: str) -> Carrera:
        existing = await self.repo.find_by_codigo(codigo)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código de carrera ya existe")
        return await self.repo.create(codigo=codigo, nombre=nombre)

    async def get(self, id: UUID) -> Carrera:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")
        return obj

    async def list(self, offset: int = 0, limit: int = 50) -> list[Carrera]:
        return await self.repo.list(offset=offset, limit=limit)

    async def update(self, id: UUID, **kwargs) -> Carrera:
        if "codigo" in kwargs and kwargs["codigo"] is not None:
            existing = await self.repo.find_by_codigo(kwargs["codigo"])
            if existing and existing.id != id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código de carrera ya existe")
        return await self.repo.update(id, **kwargs)

    async def delete(self, id: UUID) -> None:
        await self.repo.soft_delete(id)


class CohorteService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = CohorteRepository(Cohorte, session, tenant_id)
        self.carrera_repo = CarreraRepository(Carrera, session, tenant_id)

    async def create(self, carrera_id: UUID, nombre: str, anio: int, vig_desde=None, vig_hasta=None) -> Cohorte:
        carrera = await self.carrera_repo.get(carrera_id)
        if carrera is None:
            raise HTTPException(status_code=422, detail="Carrera no encontrada")
        if carrera.estado == "Inactiva":
            raise HTTPException(status_code=422, detail="No se pueden crear cohortes en una carrera inactiva")
        existing = await self.repo.find_by_nombre_and_carrera(nombre, carrera_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe una cohorte con ese nombre en la misma carrera")
        return await self.repo.create(carrera_id=carrera_id, nombre=nombre, anio=anio, vig_desde=vig_desde, vig_hasta=vig_hasta)

    async def get(self, id: UUID) -> Cohorte:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")
        return obj

    async def list(self, carrera_id: UUID | None = None, offset: int = 0, limit: int = 50) -> list[Cohorte]:
        if carrera_id:
            return await self.repo.list(carrera_id=carrera_id, offset=offset, limit=limit)
        return await self.repo.list(offset=offset, limit=limit)

    async def update(self, id: UUID, **kwargs) -> Cohorte:
        return await self.repo.update(id, **kwargs)

    async def delete(self, id: UUID) -> None:
        await self.repo.soft_delete(id)


class MateriaService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = MateriaRepository(Materia, session, tenant_id)

    async def create(self, codigo: str, nombre: str) -> Materia:
        existing = await self.repo.find_by_codigo(codigo)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código de materia ya existe")
        return await self.repo.create(codigo=codigo, nombre=nombre)

    async def get(self, id: UUID) -> Materia:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")
        return obj

    async def list(self, offset: int = 0, limit: int = 50) -> list[Materia]:
        return await self.repo.list(offset=offset, limit=limit)

    async def update(self, id: UUID, **kwargs) -> Materia:
        if "codigo" in kwargs and kwargs["codigo"] is not None:
            existing = await self.repo.find_by_codigo(kwargs["codigo"])
            if existing and existing.id != id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código de materia ya existe")
        return await self.repo.update(id, **kwargs)

    async def delete(self, id: UUID) -> None:
        await self.repo.soft_delete(id)


class DictadoService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = DictadoRepository(Dictado, session, tenant_id)
        self.materia_repo = MateriaRepository(Materia, session, tenant_id)
        self.carrera_repo = CarreraRepository(Carrera, session, tenant_id)
        self.cohorte_repo = CohorteRepository(Cohorte, session, tenant_id)

    async def create(self, materia_id: UUID, carrera_id: UUID, cohorte_id: UUID, nombre: str) -> Dictado:
        existing = await self.repo.find_by_materia_and_cohorte(materia_id, cohorte_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un dictado para esa materia y cohorte")
        return await self.repo.create(materia_id=materia_id, carrera_id=carrera_id, cohorte_id=cohorte_id, nombre=nombre)

    async def get(self, id: UUID) -> Dictado:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dictado no encontrado")
        return obj

    async def list(self, materia_id: UUID | None = None, cohorte_id: UUID | None = None, offset: int = 0, limit: int = 50) -> list[Dictado]:
        if materia_id:
            return await self.repo.list_by_materia(materia_id, offset=offset, limit=limit)
        if cohorte_id:
            return await self.repo.list_by_cohorte(cohorte_id, offset=offset, limit=limit)
        return await self.repo.list(offset=offset, limit=limit)

    async def update(self, id: UUID, **kwargs) -> Dictado:
        return await self.repo.update(id, **kwargs)

    async def delete(self, id: UUID) -> None:
        await self.repo.soft_delete(id)
