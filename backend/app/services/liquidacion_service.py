from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import LIQUIDACION_CALCULAR, LIQUIDACION_CERRAR
from app.models.asignacion import Asignacion
from app.models.liquidacion import Liquidacion
from app.models.materia import Materia
from app.models.user import User
from app.repositories.grilla_salarial_repository import (
    SalarioBaseRepository,
    SalarioPlusRepository,
)
from app.repositories.liquidacion_repository import LiquidacionRepository
from app.schemas.liquidaciones import (
    KPIResponse,
    LiquidacionCalcularRequest,
    LiquidacionCalcularResponse,
    LiquidacionListResponse,
    LiquidacionResponse,
)
from app.services.audit_service import AuditService


class LiquidacionService:
    def __init__(self, session: AsyncSession, tenant_id: UUID, actor_id: UUID):
        self.liquidacion_repo = LiquidacionRepository(session, tenant_id)
        self.base_repo = SalarioBaseRepository(session, tenant_id)
        self.plus_repo = SalarioPlusRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.audit = AuditService(session)

    # ── Cálculo puro (decoupled per ADR-007) ──────────────────────────────

    async def _calcular_liquidacion_docente(
        self,
        usuario_id: UUID,
        rol: str,
        periodo: str,
        cohorte_id: UUID,
    ) -> dict:
        """
        Pure calculation function.

        Decoupled so the formula can be replaced when FINANZAS confirms
        PA-23/ADR-007.

        Current formula: Base(rol) + Σ(Plus(grupo, rol) × N_comisiones)
        """
        anio, mes = periodo.split("-")
        fecha_vigencia = date(int(anio), int(mes), 1)

        # 1. Find SalarioBase vigente
        base = await self.base_repo.find_vigente_base_by_rol(rol, fecha_vigencia)
        if not base:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"No hay SalarioBase vigente para rol {rol} en {periodo}",
            )

        # 2. Find active asignaciones for this user in the cohorte
        stmt = select(Asignacion).where(
            Asignacion.usuario_id == usuario_id,
            Asignacion.cohorte_id == cohorte_id,
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        asignaciones = result.scalars().all()

        if not asignaciones:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"El usuario no tiene asignaciones activas en la cohorte {cohorte_id}",
            )

        # 3. Get grupo_plus for each materia — group by grupo for N×Plus
        materia_grupo_count: dict[str, int] = {}
        comisiones_detalle: list[dict] = []

        for asig in asignaciones:
            materia = await self.session.get(Materia, asig.materia_id)
            grupo = materia.grupo_plus if (materia and materia.grupo_plus) else None

            if grupo:
                materia_grupo_count[grupo] = materia_grupo_count.get(grupo, 0) + 1

            comisiones_detalle.append({
                "materia_id": str(asig.materia_id),
                "grupo_plus": grupo,
            })

        # 4. Calculate Plus: Σ(Plus(grupo, rol) × N_comisiones)
        monto_plus_total = Decimal("0.00")
        for grupo, count in materia_grupo_count.items():
            plus = await self.plus_repo.find_vigente_plus_by_grupo_rol(
                grupo, rol, fecha_vigencia,
            )
            if plus:
                monto_plus_total += plus.monto * count
            # No plus found → contributes 0 (does not block)

        monto_base = base.monto
        total = monto_base + monto_plus_total

        # 5. Check if user is facturante
        user = await self.session.get(User, usuario_id)
        excluido_por_factura = user.facturador if user else False

        es_nexo = (rol == "NEXO")

        return {
            "monto_base": monto_base,
            "monto_plus": monto_plus_total,
            "total": total,
            "es_nexo": es_nexo,
            "excluido_por_factura": excluido_por_factura,
            "comisiones": {
                "items": comisiones_detalle,
                "grupos": materia_grupo_count,
            },
            "rol": rol,
        }

    # ── Calcular ───────────────────────────────────────────────────────────

    async def calcular(
        self,
        data: LiquidacionCalcularRequest,
    ) -> LiquidacionCalcularResponse:
        """Execute calculation for a cohorte+periodo. Atomic + idempotent."""
        cohorte_id = data.cohorte_id
        periodo = data.periodo

        # 1. Get all active users in the cohorte, grouped by (usuario_id, rol)
        stmt = select(
            Asignacion.usuario_id,
            Asignacion.rol,
        ).where(
            Asignacion.cohorte_id == cohorte_id,
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.is_deleted == False,
        ).distinct()
        result = await self.session.execute(stmt)
        rows = result.all()

        # Group by usuario_id to detect multiple roles per user
        user_roles: dict[UUID, set[str]] = defaultdict(set)
        for row in rows:
            user_roles[row.usuario_id].add(row.rol)

        if not user_roles:
            return LiquidacionCalcularResponse(creadas=0, items=[])

        # 2. Check if any liquidacion already exists for this cohorte+periodo
        #    If any is Cerrada → reject (cannot recalculate closed period)
        existing_all = await self.liquidacion_repo.find_by_cohorte_periodo(
            cohorte_id, periodo,
        )
        existing_by_user: dict[UUID, Liquidacion] = {}
        for liq in existing_all:
            existing_by_user[liq.usuario_id] = liq
            if liq.estado == "Cerrada":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Ya existen liquidaciones cerradas para la cohorte {cohorte_id} "
                        f"en período {periodo}. No se puede recalcular."
                    ),
                )

        # 3. Validate ALL users have SalarioBase before any creation
        anio, mes = periodo.split("-")
        fecha_vigencia = date(int(anio), int(mes), 1)
        for usuario_id, roles in user_roles.items():
            for rol in roles:
                base = await self.base_repo.find_vigente_base_by_rol(rol, fecha_vigencia)
                if not base:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=(
                            f"No hay SalarioBase vigente para rol {rol} en período {periodo}. "
                            "La operación se canceló — no se generó ninguna liquidación."
                        ),
                    )

        # 4. Calculate and create/update for each (usuario, rol)
        liquidaciones_creadas: list[LiquidacionResponse] = []
        creadas_count = 0

        for usuario_id, roles in user_roles.items():
            for rol in roles:
                calculo = await self._calcular_liquidacion_docente(
                    usuario_id=usuario_id,
                    rol=rol,
                    periodo=periodo,
                    cohorte_id=cohorte_id,
                )

                existing = existing_by_user.get(usuario_id)

                if existing:
                    # Update existing (Abierta) liquidacion
                    existing.monto_base = calculo["monto_base"]
                    existing.monto_plus = calculo["monto_plus"]
                    existing.total = calculo["total"]
                    existing.comisiones = calculo["comisiones"]
                    existing.es_nexo = calculo["es_nexo"]
                    existing.excluido_por_factura = calculo["excluido_por_factura"]
                    await self.session.flush()
                    await self.session.refresh(existing)
                    liquidaciones_creadas.append(
                        LiquidacionResponse.model_validate(existing),
                    )
                    creadas_count += 1
                else:
                    # Create new liquidacion
                    nueva = Liquidacion(
                        tenant_id=self.tenant_id,
                        cohorte_id=cohorte_id,
                        periodo=periodo,
                        usuario_id=usuario_id,
                        rol=rol,
                        comisiones=calculo["comisiones"],
                        monto_base=calculo["monto_base"],
                        monto_plus=calculo["monto_plus"],
                        total=calculo["total"],
                        es_nexo=calculo["es_nexo"],
                        excluido_por_factura=calculo["excluido_por_factura"],
                        estado="Abierta",
                    )
                    self.session.add(nueva)
                    await self.session.flush()
                    await self.session.refresh(nueva)
                    liquidaciones_creadas.append(
                        LiquidacionResponse.model_validate(nueva),
                    )
                    creadas_count += 1

        # 5. Audit
        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=LIQUIDACION_CALCULAR,
            detalle={
                "cohorte_id": str(cohorte_id),
                "periodo": periodo,
                "docentes": len(user_roles),
                "liquidaciones": creadas_count,
            },
        )

        return LiquidacionCalcularResponse(
            creadas=creadas_count,
            items=liquidaciones_creadas,
        )

    # ── Listar ─────────────────────────────────────────────────────────────

    async def listar(
        self,
        cohorte_id: UUID | None = None,
        periodo: str | None = None,
        usuario_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> LiquidacionListResponse:
        filtros = {}
        if cohorte_id is not None:
            filtros["cohorte_id"] = cohorte_id
        if periodo is not None:
            filtros["periodo"] = periodo
        if usuario_id is not None:
            filtros["usuario_id"] = usuario_id

        items, total = await self.liquidacion_repo.list_by_filters(
            filtros=filtros,
            offset=offset,
            limit=limit,
        )

        return LiquidacionListResponse(
            items=[LiquidacionResponse.model_validate(i) for i in items],
            total=total,
            offset=offset,
            limit=limit,
        )

    # ── Obtener ────────────────────────────────────────────────────────────

    async def obtener(self, id: UUID) -> LiquidacionResponse:
        liquidacion = await self.liquidacion_repo.get(id)
        if not liquidacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Liquidación no encontrada",
            )
        return LiquidacionResponse.model_validate(liquidacion)

    # ── Cerrar ─────────────────────────────────────────────────────────────

    async def cerrar(self, id: UUID) -> LiquidacionResponse:
        liquidacion = await self.liquidacion_repo.get(id)
        if not liquidacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Liquidación no encontrada",
            )

        if liquidacion.estado == "Cerrada":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La liquidación ya está cerrada",
            )

        liquidacion.estado = "Cerrada"
        await self.session.flush()
        await self.session.refresh(liquidacion)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=LIQUIDACION_CERRAR,
            detalle={
                "liquidacion_id": str(id),
                "cohorte_id": str(liquidacion.cohorte_id),
                "periodo": liquidacion.periodo,
                "usuario_id": str(liquidacion.usuario_id),
            },
        )

        return LiquidacionResponse.model_validate(liquidacion)

    # ── Exportar ───────────────────────────────────────────────────────────

    async def exportar(
        self,
        cohorte_id: UUID | None = None,
        periodo: str | None = None,
    ) -> list[LiquidacionResponse]:
        filtros = {}
        if cohorte_id is not None:
            filtros["cohorte_id"] = cohorte_id
        if periodo is not None:
            filtros["periodo"] = periodo

        items, _ = await self.liquidacion_repo.list_by_filters(
            filtros=filtros,
            offset=0,
            limit=None,
        )

        return [LiquidacionResponse.model_validate(i) for i in items]

    # ── Historial ──────────────────────────────────────────────────────────

    async def historial(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        """List LIQUIDACION_CALCULAR audit events, sorted by created_at desc."""
        logs = await self.audit.get_log(
            tenant_id=self.tenant_id,
            accion=LIQUIDACION_CALCULAR,
            offset=offset,
            limit=limit,
        )
        return [
            {
                "id": str(log.id),
                "actor_id": str(log.actor_id),
                "accion": log.accion,
                "detalle": log.detalle,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    # ── KPIs ───────────────────────────────────────────────────────────────

    async def kpis(
        self,
        periodo: str,
        cohorte_id: UUID | None = None,
    ) -> KPIResponse:
        agg = await self.liquidacion_repo.kpi_aggregation(
            periodo=periodo,
            cohorte_id=cohorte_id,
        )

        return KPIResponse(
            periodo=periodo,
            cohorte_id=cohorte_id,
            total_facturantes_count=agg["total_facturantes_count"],
            total_facturantes_sum=agg["total_facturantes_sum"],
            total_no_facturantes_count=agg["total_no_facturantes_count"],
            total_no_facturantes_sum=agg["total_no_facturantes_sum"],
        )
