from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import joinedload

from app.models.mensaje import Mensaje
from app.models.user import User
from app.repositories.base import TenantScopedRepository


class MensajeRepository(TenantScopedRepository[Mensaje]):
    async def create(self, **kwargs) -> Mensaje:
        return await super().create(**kwargs)

    async def find_hilos(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[dict]:
        """Return latest message per hilo where user is sender or recipient."""
        subq = (
            select(
                Mensaje.hilo_id,
                func.max(Mensaje.created_at).label("max_created"),
            )
            .where(
                Mensaje.tenant_id == self.tenant_id,
                Mensaje.is_deleted == False,
                (Mensaje.remitente_id == user_id)
                | (Mensaje.destinatario_id == user_id),
            )
            .group_by(Mensaje.hilo_id)
            .subquery()
        )

        stmt = (
            select(Mensaje)
            .join(
                subq,
                (Mensaje.hilo_id == subq.c.hilo_id)
                & (Mensaje.created_at == subq.c.max_created),
            )
            .where(Mensaje.is_deleted == False)
            .options(joinedload(Mensaje.remitente), joinedload(Mensaje.destinatario))
            .order_by(Mensaje.created_at.desc(), Mensaje.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = result.unique().scalars().all()

        # Build enriched response with no_leidos count per hilo
        hilos = []
        for msg in messages:
            no_leidos = await self._count_no_leidos_por_hilo(msg.hilo_id, user_id)
            hilos.append({
                "mensaje": msg,
                "remitente_nombre": f"{msg.remitente.nombre} {msg.remitente.apellido}" if msg.remitente else "Unknown",
                "no_leidos": no_leidos,
            })
        return hilos

    async def _count_no_leidos_por_hilo(self, hilo_id: UUID, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(Mensaje).where(
            Mensaje.tenant_id == self.tenant_id,
            Mensaje.hilo_id == hilo_id,
            Mensaje.destinatario_id == user_id,
            Mensaje.leido == False,
            Mensaje.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def find_mensajes_por_hilo(
        self, hilo_id: UUID, user_id: UUID
    ) -> list[Mensaje]:
        """Return all messages in a hilo where user is sender or recipient."""
        stmt = (
            select(Mensaje)
            .where(
                Mensaje.tenant_id == self.tenant_id,
                Mensaje.hilo_id == hilo_id,
                Mensaje.is_deleted == False,
                (Mensaje.remitente_id == user_id)
                | (Mensaje.destinatario_id == user_id),
            )
            .order_by(Mensaje.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def marcar_hilo_leido(self, hilo_id: UUID, user_id: UUID) -> None:
        """Mark all messages as read in a hilo where user is recipient."""
        stmt = (
            update(Mensaje)
            .where(
                Mensaje.tenant_id == self.tenant_id,
                Mensaje.hilo_id == hilo_id,
                Mensaje.destinatario_id == user_id,
                Mensaje.leido == False,
                Mensaje.is_deleted == False,
            )
            .values(leido=True)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def count_no_leidos(self, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(Mensaje).where(
            Mensaje.tenant_id == self.tenant_id,
            Mensaje.destinatario_id == user_id,
            Mensaje.leido == False,
            Mensaje.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def find_hilo_remitente(self, hilo_id: UUID) -> UUID | None:
        """Return the remitente_id of the first message in a hilo."""
        stmt = (
            select(Mensaje.remitente_id)
            .where(
                Mensaje.tenant_id == self.tenant_id,
                Mensaje.hilo_id == hilo_id,
                Mensaje.is_deleted == False,
            )
            .order_by(Mensaje.created_at.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        return row[0] if row else None

    async def get_hilo_ultimo_mensaje(self, hilo_id: UUID) -> Mensaje | None:
        """Return the latest message in a hilo."""
        stmt = (
            select(Mensaje)
            .where(
                Mensaje.tenant_id == self.tenant_id,
                Mensaje.hilo_id == hilo_id,
                Mensaje.is_deleted == False,
            )
            .order_by(Mensaje.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_destinatario_en_tenant(self, destinatario_id: UUID) -> User | None:
        """Verify a user exists and is not deleted in the same tenant."""
        stmt = select(User).where(
            User.id == destinatario_id,
            User.tenant_id == self.tenant_id,
            User.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
