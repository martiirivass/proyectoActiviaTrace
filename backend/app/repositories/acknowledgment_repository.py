from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.user import User
from app.repositories.base import BaseRepository


class AcknowledgmentRepository(BaseRepository[AcknowledgmentAviso]):
    """Repository for AcknowledgmentAviso.

    Note: Does NOT extend TenantScopedRepository because AcknowledgmentAviso
    does not have a tenant_id (it's linked via aviso_id).
    """

    def __init__(self, session: AsyncSession):
        super().__init__(AcknowledgmentAviso, session)

    async def create_or_ignore(self, aviso_id: UUID, usuario_id: UUID) -> bool:
        """INSERT ... ON CONFLICT DO NOTHING.

        Returns True if a new row was inserted, False if it already existed.
        """
        stmt = (
            pg_insert(AcknowledgmentAviso)
            .values(
                aviso_id=aviso_id,
                usuario_id=usuario_id,
            )
            .on_conflict_do_nothing(
                constraint="uq_aviso_usuario_ack"
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def count_by_aviso(self, aviso_id: UUID) -> int:
        """Count acknowledges by aviso_id."""
        stmt = (
            select(func.count(AcknowledgmentAviso.id))
            .where(AcknowledgmentAviso.aviso_id == aviso_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def list_users_by_aviso(
        self,
        aviso_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """List users who acknowledged this aviso, with profile data."""
        # Count
        count_q = (
            select(func.count(AcknowledgmentAviso.id))
            .where(AcknowledgmentAviso.aviso_id == aviso_id)
        )
        count_result = await self.session.execute(count_q)
        total = count_result.scalar() or 0

        # Data with user join
        stmt = (
            select(
                User.id.label("usuario_id"),
                User.nombre,
                User.apellido,
                User.email,
                AcknowledgmentAviso.confirmado_at,
            )
            .join(AcknowledgmentAviso, AcknowledgmentAviso.usuario_id == User.id)
            .where(
                AcknowledgmentAviso.aviso_id == aviso_id,
                User.is_deleted == False,
            )
            .offset(offset)
            .limit(limit)
            .order_by(AcknowledgmentAviso.confirmado_at.desc())
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        items = []
        for row in rows:
            items.append({
                "usuario_id": row.usuario_id,
                "nombre": row.nombre,
                "apellidos": row.apellido,
                "email": row.email,
                "confirmado_at": row.confirmado_at,
            })

        return items, total

    async def has_acknowledged(self, aviso_id: UUID, usuario_id: UUID) -> bool:
        """Check if a user has already acknowledged a specific aviso."""
        stmt = (
            select(AcknowledgmentAviso)
            .where(
                AcknowledgmentAviso.aviso_id == aviso_id,
                AcknowledgmentAviso.usuario_id == usuario_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
