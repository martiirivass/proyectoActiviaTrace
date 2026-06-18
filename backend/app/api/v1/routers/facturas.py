from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.permissions import FACTURAS_GESTIONAR
from app.schemas.auth import CurrentUser
from app.schemas.liquidaciones import (
    FacturaCreate,
    FacturaListResponse,
    FacturaResponse,
)
from app.services.factura_service import FacturaService

router = APIRouter(prefix="/api/v1/facturas", tags=["Facturas"])


@router.get("/", response_model=FacturaListResponse)
async def listar_facturas(
    periodo: str | None = Query(None),
    usuario_id: UUID | None = Query(None),
    estado: str | None = Query(None),
    materia_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(FACTURAS_GESTIONAR)),
    db: AsyncSession = Depends(get_db),
):
    """Listar facturas con filtros opcionales por período, usuario, estado y comisión."""
    svc = FacturaService(db, current_user.tenant_id, current_user.id)
    return await svc.listar(
        periodo=periodo,
        usuario_id=usuario_id,
        estado=estado,
        materia_id=materia_id,
        offset=offset,
        limit=limit,
    )


@router.post("/", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED)
async def crear_factura(
    data: FacturaCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(FACTURAS_GESTIONAR)),
    db: AsyncSession = Depends(get_db),
):
    """Cargar una nueva factura (estado inicial: Pendiente)."""
    svc = FacturaService(db, current_user.tenant_id, current_user.id)
    return await svc.crear(data)


@router.get("/{factura_id}", response_model=FacturaResponse)
async def obtener_factura(
    factura_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(FACTURAS_GESTIONAR)),
    db: AsyncSession = Depends(get_db),
):
    """Obtener detalle de una factura por ID."""
    svc = FacturaService(db, current_user.tenant_id, current_user.id)
    return await svc.obtener(factura_id)


@router.post("/{factura_id}/abonar", response_model=FacturaResponse)
async def abonar_factura(
    factura_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(FACTURAS_GESTIONAR)),
    db: AsyncSession = Depends(get_db),
):
    """Marcar una factura como abonada (cambia estado a Abonada)."""
    svc = FacturaService(db, current_user.tenant_id, current_user.id)
    return await svc.abonar(factura_id)


@router.delete("/{factura_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_factura(
    factura_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(FACTURAS_GESTIONAR)),
    db: AsyncSession = Depends(get_db),
):
    """Eliminar (soft delete) una factura."""
    svc = FacturaService(db, current_user.tenant_id, current_user.id)
    await svc.eliminar(factura_id)
