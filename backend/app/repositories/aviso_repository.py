from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.aviso import Aviso, AlcanceAviso
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.models.user_tenant import UserTenant
from app.repositories.base import TenantScopedRepository


class AvisoRepository(TenantScopedRepository[Aviso]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Aviso, session, tenant_id)

    def _base_active_query(self) -> Select:
        now = datetime.now(timezone.utc)
        return (
            select(Aviso)
            .where(
                Aviso.tenant_id == self.tenant_id,
                Aviso.is_deleted == False,
                Aviso.activo == True,
                Aviso.inicio_en <= now,
                Aviso.fin_en >= now,
            )
        )

    def _build_alcance_filters(
        self,
        rol: str,
        cohorte_ids: list[UUID],
        materia_ids: list[UUID],
    ) -> list:
        """Build SQLAlchemy filter conditions for alcance visibility."""
        filters = []

        # Global: always visible (but still subject to rol_destino filter)
        filters.append(Aviso.alcance == AlcanceAviso.Global)

        # PorRol: match user's rol
        if rol:
            filters.append(
                (Aviso.alcance == AlcanceAviso.PorRol)
                & ((Aviso.rol_destino == rol) | (Aviso.rol_destino.is_(None)))
            )
        else:
            filters.append(
                (Aviso.alcance == AlcanceAviso.PorRol)
                & (Aviso.rol_destino.is_(None))
            )

        # PorMateria: user has asignacion in that materia
        if materia_ids:
            filters.append(
                (Aviso.alcance == AlcanceAviso.PorMateria)
                & Aviso.materia_id.in_(materia_ids)
            )

        # PorCohorte: user belongs to that cohorte
        if cohorte_ids:
            filters.append(
                (Aviso.alcance == AlcanceAviso.PorCohorte)
                & Aviso.cohorte_id.in_(cohorte_ids)
            )

        return filters

    async def list_activos_for_user(
        self,
        usuario_id: UUID,
        rol: str,
        cohorte_ids: list[UUID],
        materia_ids: list[UUID],
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Aviso], int]:
        """List active avisos visible for a specific user.

        Returns (items, total_count).
        Filters by tenant + active + vigencia + alcance visibility.
        """
        base = self._base_active_query()
        alcance_filters = self._build_alcance_filters(rol, cohorte_ids, materia_ids)
        base = base.where(or_(*alcance_filters))

        # rol_destino filter for non-PorRol alcances: if set, must match user's rol
        base = base.where(
            (Aviso.rol_destino.is_(None)) | (Aviso.rol_destino == rol)
        )

        # Count total
        count_q = select(func.count()).select_from(base.subquery())
        count_result = await self.session.execute(count_q)
        total = count_result.scalar() or 0

        # Get items with ordering
        data_q = (
            base
            .order_by(Aviso.orden.asc(), Aviso.inicio_en.desc())
            .offset(offset)
            .limit(limit)
        )
        data_result = await self.session.execute(data_q)
        items = list(data_result.scalars().all())
        return items, total

    async def get_by_id_if_visible(
        self,
        aviso_id: UUID,
        usuario_id: UUID,
        rol: str,
        cohorte_ids: list[UUID],
        materia_ids: list[UUID],
    ) -> Aviso | None:
        """Get aviso by id if it is visible for the user."""
        base = self._base_active_query().where(Aviso.id == aviso_id)
        alcance_filters = self._build_alcance_filters(rol, cohorte_ids, materia_ids)
        base = base.where(or_(*alcance_filters))

        # rol_destino filter for non-PorRol alcances
        base = base.where(
            (Aviso.rol_destino.is_(None)) | (Aviso.rol_destino == rol)
        )

        result = await self.session.execute(base)
        return result.scalar_one_or_none()

    async def count_usuarios_alcanzados(self, aviso: Aviso) -> int:
        """Count potential users that should see this aviso based on its alcance."""
        if aviso.alcance == AlcanceAviso.Global:
            stmt = (
                select(func.count(User.id))
                .join(UserTenant, UserTenant.user_id == User.id)
                .where(
                    UserTenant.tenant_id == self.tenant_id,
                    UserTenant.is_active == True,
                    User.is_deleted == False,
                )
            )
        elif aviso.alcance == AlcanceAviso.PorMateria and aviso.materia_id:
            stmt = (
                select(func.count(Asignacion.usuario_id.distinct()))
                .where(
                    Asignacion.tenant_id == self.tenant_id,
                    Asignacion.materia_id == aviso.materia_id,
                    Asignacion.is_deleted == False,
                )
            )
        elif aviso.alcance == AlcanceAviso.PorCohorte and aviso.cohorte_id:
            stmt = (
                select(func.count(Asignacion.usuario_id.distinct()))
                .where(
                    Asignacion.tenant_id == self.tenant_id,
                    Asignacion.cohorte_id == aviso.cohorte_id,
                    Asignacion.is_deleted == False,
                )
            )
        elif aviso.alcance == AlcanceAviso.PorRol and aviso.rol_destino:
            stmt = (
                select(func.count(UserRole.user_id.distinct()))
                .join(Role, UserRole.role_id == Role.id)
                .where(
                    Role.tenant_id == self.tenant_id,
                    Role.name == aviso.rol_destino,
                    Role.is_deleted == False,
                )
            )
        else:
            return 0

        result = await self.session.execute(stmt)
        return result.scalar() or 0
