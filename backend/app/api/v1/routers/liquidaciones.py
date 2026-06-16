from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.permissions import (
    LIQUIDACIONES_CALCULAR,
    LIQUIDACIONES_CERRAR,
    LIQUIDACIONES_EXPORTAR,
    LIQUIDACIONES_HISTORIAL,
    LIQUIDACIONES_VER,
)
from app.schemas.auth import CurrentUser
from app.schemas.liquidaciones import (
    LiquidacionCalcularRequest,
    LiquidacionCalcularResponse,
    LiquidacionListResponse,
    LiquidacionResponse,
)
from app.services.liquidacion_service import LiquidacionService

router = APIRouter(prefix="/api/v1/liquidaciones", tags=["Liquidaciones"])


@router.get("/", response_model=LiquidacionListResponse)
async def listar_liquidaciones(
    cohorte_id: UUID | None = Query(None),
    periodo: str | None = Query(None),
    usuario_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(LIQUIDACIONES_VER)),
    db: AsyncSession = Depends(get_db),
):
    """Listar liquidaciones con filtros opcionales por cohorte, periodo y usuario."""
    svc = LiquidacionService(db, current_user.tenant_id, current_user.id)
    return await svc.listar(
        cohorte_id=cohorte_id,
        periodo=periodo,
        usuario_id=usuario_id,
        offset=offset,
        limit=limit,
    )


@router.post("/calcular", response_model=LiquidacionCalcularResponse, status_code=status.HTTP_201_CREATED)
async def calcular_liquidacion(
    data: LiquidacionCalcularRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(LIQUIDACIONES_CALCULAR)),
    db: AsyncSession = Depends(get_db),
):
    """Ejecutar cálculo de liquidaciones para una cohorte y período."""
    svc = LiquidacionService(db, current_user.tenant_id, current_user.id)
    return await svc.calcular(data)


@router.get("/{liquidacion_id}", response_model=LiquidacionResponse)
async def obtener_liquidacion(
    liquidacion_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(LIQUIDACIONES_VER)),
    db: AsyncSession = Depends(get_db),
):
    """Obtener detalle de una liquidación por ID."""
    svc = LiquidacionService(db, current_user.tenant_id, current_user.id)
    return await svc.obtener(liquidacion_id)


@router.post("/{liquidacion_id}/cerrar", response_model=LiquidacionResponse)
async def cerrar_liquidacion(
    liquidacion_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(LIQUIDACIONES_CERRAR)),
    db: AsyncSession = Depends(get_db),
):
    """Cerrar una liquidación (la hace irreversible)."""
    svc = LiquidacionService(db, current_user.tenant_id, current_user.id)
    return await svc.cerrar(liquidacion_id)


@router.get("/exportar", response_model=list[LiquidacionResponse])
async def exportar_liquidaciones(
    cohorte_id: UUID | None = Query(None),
    periodo: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(LIQUIDACIONES_EXPORTAR)),
    db: AsyncSession = Depends(get_db),
):
    """Exportar listado completo de liquidaciones sin paginación."""
    svc = LiquidacionService(db, current_user.tenant_id, current_user.id)
    return await svc.exportar(cohorte_id=cohorte_id, periodo=periodo)


@router.get("/historial")
async def historial_liquidaciones(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(LIQUIDACIONES_HISTORIAL)),
    db: AsyncSession = Depends(get_db),
):
    """Historial de ejecuciones de cálculo de liquidaciones (auditoría)."""
    svc = LiquidacionService(db, current_user.tenant_id, current_user.id)
    return await svc.historial(offset=offset, limit=limit)
