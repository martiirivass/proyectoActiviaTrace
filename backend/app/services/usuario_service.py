from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import PasswordService
from app.models.user import User
from app.repositories.usuario_repository import UsuarioRepository


class UsuarioService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = UsuarioRepository(User, session, tenant_id)

    async def create(self, data) -> User:
        existing = await self.repo.find_by_email(data.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado en este tenant")
        kwargs = data.model_dump(exclude={"password"})
        kwargs["password_hash"] = PasswordService.hash(data.password)
        return await self.repo.create(**kwargs)

    async def get(self, id: UUID) -> User:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return obj

    async def list(self, offset: int = 0, limit: int = 50) -> list[User]:
        return await self.repo.list(offset=offset, limit=limit)

    async def update(self, id: UUID, data) -> User:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        kwargs = data.model_dump(exclude_none=True)
        if "email" in kwargs and kwargs["email"] != obj.email:
            existing = await self.repo.find_by_email(kwargs["email"])
            if existing and existing.id != id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado en este tenant")
        if "password" in kwargs:
            kwargs["password_hash"] = PasswordService.hash(kwargs.pop("password"))
        return await self.repo.update(id, **kwargs)

    async def delete(self, id: UUID) -> None:
        await self.repo.soft_delete(id)
