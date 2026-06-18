from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entrada_padron import EntradaPadron
from app.models.version_padron import VersionPadron
from app.repositories.base import TenantScopedRepository


class PadronRepository(TenantScopedRepository[VersionPadron]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(VersionPadron, session, tenant_id)

    async def create_version(
        self, materia_id: UUID, cohorte_id: UUID, cargado_por: UUID
    ) -> VersionPadron:
        await self._desactivar_activa(materia_id, cohorte_id)
        return await self.create(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=cargado_por,
            activa=True,
        )

    async def _desactivar_activa(self, materia_id: UUID, cohorte_id: UUID) -> None:
        stmt = (
            update(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.activa == True,
                VersionPadron.is_deleted == False,
            )
            .values(activa=False)
        )
        await self.session.execute(stmt)

    async def bulk_create_entries(
        self, version_id: UUID, entries: list[dict]
    ) -> list[EntradaPadron]:
        objs = []
        for entry in entries:
            obj = EntradaPadron(tenant_id=self.tenant_id, version_id=version_id, **entry)
            self.session.add(obj)
            objs.append(obj)
        await self.session.flush()
        for obj in objs:
            await self.session.refresh(obj)
        return objs

    async def get_versions(
        self, materia_id: UUID, cohorte_id: UUID
    ) -> list[dict]:
        stmt = (
            select(
                VersionPadron,
                func.count(EntradaPadron.id).label("entrada_count"),
            )
            .outerjoin(
                EntradaPadron,
                EntradaPadron.version_id == VersionPadron.id,
            )
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.is_deleted == False,
            )
            .group_by(VersionPadron.id)
            .order_by(VersionPadron.cargado_at.desc())
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "version": row.VersionPadron,
                "entrada_count": row.entrada_count,
            }
            for row in rows
        ]

    async def get_active_version(
        self, materia_id: UUID, cohorte_id: UUID
    ) -> VersionPadron | None:
        stmt = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.activa == True,
                VersionPadron.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def vaciar_materia(self, materia_id: UUID) -> int:
        now = datetime.now(timezone.utc)
        versions_stmt = (
            select(VersionPadron.id)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.is_deleted == False,
            )
        )
        result = await self.session.execute(versions_stmt)
        version_ids = [row[0] for row in result.all()]

        if not version_ids:
            return 0

        await self.session.execute(
            update(EntradaPadron)
            .where(
                EntradaPadron.version_id.in_(version_ids),
                EntradaPadron.is_deleted == False,
            )
            .values(is_deleted=True, deleted_at=now)
        )

        await self.session.execute(
            update(VersionPadron)
            .where(
                VersionPadron.id.in_(version_ids),
                VersionPadron.is_deleted == False,
            )
            .values(is_deleted=True, deleted_at=now, activa=False)
        )

        return len(version_ids)

    async def find_entries_by_email(
        self, email_cifrado: str
    ) -> list[EntradaPadron]:
        stmt = (
            select(EntradaPadron)
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.email == email_cifrado,
                EntradaPadron.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
