from typing import Generic, TypeVar

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mixins import SoftDeleteMixin

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def get(self, id: int | str) -> T | None:
        stmt = select(self.model).where(self.model.id == id)
        if issubclass(self.model, SoftDeleteMixin):
            stmt = stmt.where(self.model.is_deleted == False)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, include_deleted: bool = False, **filters) -> list[T]:
        stmt = select(self.model)
        if issubclass(self.model, SoftDeleteMixin) and not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int | str, **kwargs) -> T:
        stmt = select(self.model).where(self.model.id == id)
        if issubclass(self.model, SoftDeleteMixin):
            stmt = stmt.where(self.model.is_deleted == False)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise ValueError(f"{self.model.__name__} with id {id} not found")
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def soft_delete(self, id: int | str) -> None:
        if not issubclass(self.model, SoftDeleteMixin):
            raise TypeError(f"{self.model.__name__} does not support soft delete")
        stmt = select(self.model).where(self.model.id == id).where(self.model.is_deleted == False)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise ValueError(f"{self.model.__name__} with id {id} not found")
        if hasattr(obj, "is_system") and obj.is_system:
            raise ValueError("Cannot delete system role")
        obj.soft_delete()
        await self.session.flush()


class TenantScopedRepository(BaseRepository[T]):
    def __init__(self, model: type[T], session: AsyncSession, tenant_id):
        super().__init__(model, session)
        self.tenant_id = tenant_id

    async def create(self, **kwargs) -> T:
        return await super().create(tenant_id=self.tenant_id, **kwargs)

    async def get(self, id: int | str) -> T | None:
        stmt = select(self.model).where(self.model.id == id, self.model.tenant_id == self.tenant_id)
        if issubclass(self.model, SoftDeleteMixin):
            stmt = stmt.where(self.model.is_deleted == False)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, include_deleted: bool = False, **filters) -> list[T]:
        stmt = select(self.model).where(self.model.tenant_id == self.tenant_id)
        if issubclass(self.model, SoftDeleteMixin) and not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int | str, **kwargs) -> T:
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.tenant_id == self.tenant_id,
        )
        if issubclass(self.model, SoftDeleteMixin):
            stmt = stmt.where(self.model.is_deleted == False)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise ValueError(f"{self.model.__name__} with id {id} not found")
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def soft_delete(self, id: int | str) -> None:
        if not issubclass(self.model, SoftDeleteMixin):
            raise TypeError(f"{self.model.__name__} does not support soft delete")
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.tenant_id == self.tenant_id,
            self.model.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise ValueError(f"{self.model.__name__} with id {id} not found")
        obj.soft_delete()
        await self.session.flush()
