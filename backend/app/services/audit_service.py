from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.materia import Materia
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.schemas.audit import (
    AccionesPorDiaItem,
    DashboardResponse,
    ComunicacionesPorDocenteItem,
    InteraccionesPorDocenteMateriaItem,
    UltimasAccionesItem,
)
from app.services.permission_service import PermissionService


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AuditLogRepository(session)

    async def log(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        accion: str,
        detalle: dict | None = None,
        impersonado_id: UUID | None = None,
        materia_id: UUID | None = None,
        filas_afectadas: int = 0,
        ip: str | None = None,
        user_agent: str | None = None,
    ):
        return await self.repo.create(
            tenant_id=tenant_id,
            actor_id=actor_id,
            accion=accion,
            detalle=detalle,
            impersonado_id=impersonado_id,
            materia_id=materia_id,
            filas_afectadas=filas_afectadas,
            ip=ip,
            user_agent=user_agent,
        )

    async def get_log(
        self,
        *,
        tenant_id: UUID,
        accion: str | None = None,
        actor_id: UUID | None = None,
        materia_id: UUID | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
        current_user=None,
    ):
        resolved_materia_ids = await self._resolve_materias(current_user)

        if materia_id is not None:
            if resolved_materia_ids and materia_id not in resolved_materia_ids:
                return []
        elif resolved_materia_ids:
            return await self.repo.find(
                tenant_id=tenant_id,
                accion=accion,
                actor_id=actor_id,
                materia_ids=resolved_materia_ids,
                desde=desde,
                hasta=hasta,
                offset=offset,
                limit=limit,
            )

        return await self.repo.find(
            tenant_id=tenant_id,
            accion=accion,
            actor_id=actor_id,
            materia_id=materia_id,
            desde=desde,
            hasta=hasta,
            offset=offset,
            limit=limit,
        )

    async def _resolve_materias(self, current_user) -> list[UUID]:
        if current_user is None:
            return []
        permission_svc = PermissionService(self.session)
        scope = await permission_svc.get_effective_scope("auditoria:ver", current_user.id)
        if scope is None or scope == "global":
            return []
        stmt = (
            select(Asignacion.materia_id)
            .where(
                Asignacion.usuario_id == current_user.id,
                Asignacion.is_deleted == False,
                Asignacion.materia_id.isnot(None),
            )
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_dashboard(
        self,
        *,
        tenant_id: UUID,
        current_user,
        materia_id: UUID | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        limit: int = 200,
    ) -> DashboardResponse:
        resolved_materia_ids = await self._resolve_materias(current_user)

        filter_materia_ids = None
        if materia_id is not None:
            if resolved_materia_ids and materia_id not in resolved_materia_ids:
                return DashboardResponse(
                    acciones_por_dia=[],
                    comunicaciones_por_docente=[],
                    interacciones_por_docente_materia=[],
                    ultimas_acciones=[],
                    total=0,
                )
            filter_materia_ids = [materia_id]
        elif resolved_materia_ids:
            filter_materia_ids = resolved_materia_ids

        actions_by_day = await self.repo.count_actions_by_day(
            tenant_id=tenant_id,
            materia_ids=filter_materia_ids,
            desde=desde,
            hasta=hasta,
        )

        comms_by_docente = await self.repo.count_comms_by_docente(
            tenant_id=tenant_id,
            materia_ids=filter_materia_ids,
            desde=desde,
            hasta=hasta,
        )

        interactions = await self.repo.count_interactions_by_docente_materia(
            tenant_id=tenant_id,
            materia_ids=filter_materia_ids,
            desde=desde,
            hasta=hasta,
        )

        recent = await self.repo.find_recent(
            tenant_id=tenant_id,
            materia_ids=filter_materia_ids,
            desde=desde,
            hasta=hasta,
            limit=limit,
        )

        # Resolve user names
        all_user_ids = set()
        for r in comms_by_docente:
            all_user_ids.add(r["docente_id"])
        for r2 in interactions:
            all_user_ids.add(r2["actor_id"])

        user_names = {}
        if all_user_ids:
            user_stmt = select(User.id, User.nombre, User.apellido).where(User.id.in_(all_user_ids))
            user_result = await self.session.execute(user_stmt)
            for row in user_result.all():
                user_names[row.id] = f"{row.nombre} {row.apellido}"

        # Resolve materia names
        all_materia_ids = set()
        for r2 in interactions:
            all_materia_ids.add(r2["materia_id"])

        materia_names = {}
        if all_materia_ids:
            mat_stmt = select(Materia.id, Materia.nombre).where(Materia.id.in_(all_materia_ids))
            mat_result = await self.session.execute(mat_stmt)
            for row in mat_result.all():
                materia_names[row.id] = row.nombre

        # Build comunicaciones_por_docente (pivot estado -> named fields)
        comms_agg = {}
        for r in comms_by_docente:
            did = r["docente_id"]
            if did not in comms_agg:
                comms_agg[did] = {
                    "docente_id": did,
                    "docente_nombre": user_names.get(did, "Unknown"),
                    "pendiente": 0,
                    "enviando": 0,
                    "enviado": 0,
                    "error": 0,
                    "cancelado": 0,
                }
            estado_str = str(r["estado"]).lower()
            if estado_str in comms_agg[did]:
                comms_agg[did][estado_str] = r["total"]

        # Build interacciones_por_docente_materia
        interaction_groups = defaultdict(lambda: defaultdict(int))
        for r2 in interactions:
            key = (r2["actor_id"], r2["materia_id"])
            interaction_groups[key][r2["accion"]] = r2["total"]

        interacciones_list = []
        for (uid, mid), acciones in sorted(interaction_groups.items()):
            total = sum(acciones.values())
            interacciones_list.append(
                InteraccionesPorDocenteMateriaItem(
                    docente_id=uid,
                    docente_nombre=user_names.get(uid, "Unknown"),
                    materia_id=mid,
                    materia_nombre=materia_names.get(mid, "Unknown"),
                    total_acciones=total,
                    acciones=dict(acciones),
                )
            )

        return DashboardResponse(
            acciones_por_dia=[
                AccionesPorDiaItem(fecha=r["fecha"], total=r["total"])
                for r in actions_by_day
            ],
            comunicaciones_por_docente=[
                ComunicacionesPorDocenteItem(**v)
                for v in comms_agg.values()
            ],
            interacciones_por_docente_materia=interacciones_list,
            ultimas_acciones=[
                UltimasAccionesItem(
                    id=e.id,
                    fecha_hora=e.fecha_hora,
                    actor_id=e.actor_id,
                    materia_id=e.materia_id,
                    accion=e.accion,
                    filas_afectadas=e.filas_afectadas,
                    ip=e.ip,
                    user_agent=e.user_agent,
                )
                for e in recent
            ],
            total=len(recent),
        )
