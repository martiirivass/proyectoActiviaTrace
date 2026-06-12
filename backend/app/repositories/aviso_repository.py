from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aviso import AcknowledgmentAviso, Aviso
from app.repositories.base import TenantScopedRepository


class AvisoRepository(TenantScopedRepository[Aviso]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Aviso, session, tenant_id)

    async def list_with_filters(
        self,
        alcance: str | None = None,
        severidad: str | None = None,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        activo: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Aviso], int]:
        base_where = [
            Aviso.tenant_id == self.tenant_id,
            Aviso.is_deleted == False,
        ]
        if alcance:
            base_where.append(Aviso.alcance == alcance)
        if severidad:
            base_where.append(Aviso.severidad == severidad)
        if materia_id:
            base_where.append(Aviso.materia_id == materia_id)
        if cohorte_id:
            base_where.append(Aviso.cohorte_id == cohorte_id)
        if activo is not None:
            base_where.append(Aviso.activo == activo)

        count_q = select(func.count(Aviso.id)).where(*base_where)
        count_result = await self.session.execute(count_q)
        total = count_result.scalar() or 0

        data_q = (
            select(Aviso)
            .where(*base_where)
            .order_by(Aviso.orden.asc(), Aviso.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        data_result = await self.session.execute(data_q)
        items = list(data_result.scalars().all())

        return items, total

    async def list_visibles_para_usuario(
        self,
        materia_ids: list[UUID],
        cohorte_ids: list[UUID],
        roles: list[str],
        usuario_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Aviso], int]:
        now = datetime.now(timezone.utc)

        ack_subq = (
            select(AcknowledgmentAviso.aviso_id)
            .where(
                AcknowledgmentAviso.usuario_id == usuario_id,
                AcknowledgmentAviso.is_deleted == False,
            )
        ).scalar_subquery()

        alcance_conditions = []
        if materia_ids:
            alcance_conditions.append(
                and_(Aviso.alcance == "PorMateria", Aviso.materia_id.in_(materia_ids))
            )
        if cohorte_ids:
            alcance_conditions.append(
                and_(Aviso.alcance == "PorCohorte", Aviso.cohorte_id.in_(cohorte_ids))
            )
        if roles:
            alcance_conditions.append(
                and_(Aviso.alcance == "PorRol", Aviso.rol_destino.in_(roles))
            )
        alcance_conditions.append(Aviso.alcance == "Global")

        base_where = [
            Aviso.tenant_id == self.tenant_id,
            Aviso.is_deleted == False,
            Aviso.activo == True,
            Aviso.inicio_en <= now,
            Aviso.fin_en >= now,
            or_(*alcance_conditions),
            Aviso.id.notin_(ack_subq),
        ]

        count_q = select(func.count(Aviso.id)).where(*base_where)
        count_result = await self.session.execute(count_q)
        total = count_result.scalar() or 0

        data_q = (
            select(Aviso)
            .where(*base_where)
            .order_by(Aviso.orden.asc(), Aviso.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        data_result = await self.session.execute(data_q)
        items = list(data_result.scalars().all())

        return items, total

    async def get_with_metrics(self, id: UUID) -> dict | None:
        aviso = await self.get(id)
        if not aviso:
            return None

        total_vistos_q = select(func.count(AcknowledgmentAviso.id)).where(
            AcknowledgmentAviso.aviso_id == id,
            AcknowledgmentAviso.is_deleted == False,
        )
        total_vistos = (await self.session.execute(total_vistos_q)).scalar() or 0

        total_confirmados_q = select(func.count(AcknowledgmentAviso.id)).where(
            AcknowledgmentAviso.aviso_id == id,
            AcknowledgmentAviso.is_deleted == False,
            AcknowledgmentAviso.confirmado_at.isnot(None),
        )
        total_confirmados = (await self.session.execute(total_confirmados_q)).scalar() or 0

        return {
            "aviso": aviso,
            "total_vistos": total_vistos,
            "total_confirmados": total_confirmados,
        }

    async def get_metricas(self, id: UUID) -> dict | None:
        aviso = await self.get(id)
        if not aviso:
            return None

        total_vistos_q = select(func.count(AcknowledgmentAviso.id)).where(
            AcknowledgmentAviso.aviso_id == id,
            AcknowledgmentAviso.is_deleted == False,
        )
        total_vistos = (await self.session.execute(total_vistos_q)).scalar() or 0

        total_confirmados_q = select(func.count(AcknowledgmentAviso.id)).where(
            AcknowledgmentAviso.aviso_id == id,
            AcknowledgmentAviso.is_deleted == False,
            AcknowledgmentAviso.confirmado_at.isnot(None),
        )
        total_confirmados = (await self.session.execute(total_confirmados_q)).scalar() or 0

        confirmaciones_q = select(AcknowledgmentAviso).where(
            AcknowledgmentAviso.aviso_id == id,
            AcknowledgmentAviso.is_deleted == False,
        ).order_by(AcknowledgmentAviso.confirmado_at.asc().nullsfirst())
        confirmaciones_result = await self.session.execute(confirmaciones_q)
        confirmaciones = list(confirmaciones_result.scalars().all())

        return {
            "aviso": aviso,
            "total_vistos": total_vistos,
            "total_confirmados": total_confirmados,
            "confirmaciones": confirmaciones,
        }


class AcknowledgmentRepository(TenantScopedRepository[AcknowledgmentAviso]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(AcknowledgmentAviso, session, tenant_id)

    async def crear_ack(self, aviso_id: UUID, usuario_id: UUID) -> AcknowledgmentAviso:
        existing = await self.usuario_ya_ackeo(aviso_id, usuario_id)
        if existing:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya confirmaste este aviso",
            )
        from datetime import datetime, timezone
        obj = AcknowledgmentAviso(
            tenant_id=self.tenant_id,
            aviso_id=aviso_id,
            usuario_id=usuario_id,
            confirmado_at=datetime.now(timezone.utc),
        )
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def usuario_ya_ackeo(self, aviso_id: UUID, usuario_id: UUID) -> AcknowledgmentAviso | None:
        stmt = select(AcknowledgmentAviso).where(
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.usuario_id == usuario_id,
            AcknowledgmentAviso.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_aviso(self, aviso_id: UUID) -> int:
        stmt = select(func.count(AcknowledgmentAviso.id)).where(
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def list_confirmados_by_aviso(self, aviso_id: UUID) -> list[AcknowledgmentAviso]:
        stmt = select(AcknowledgmentAviso).where(
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.is_deleted == False,
        ).order_by(AcknowledgmentAviso.confirmado_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
