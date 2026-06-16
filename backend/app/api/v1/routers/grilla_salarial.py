from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.permissions import (
    GRILLA_SALARIAL_CREAR,
    GRILLA_SALARIAL_EDITAR,
    GRILLA_SALARIAL_ELIMINAR,
    GRILLA_SALARIAL_VER,
)
from app.schemas.auth import CurrentUser
from app.schemas.liquidaciones import (
    SalarioBaseCreate,
    SalarioBaseResponse,
    SalarioBaseUpdate,
    SalarioPlusCreate,
    SalarioPlusResponse,
    SalarioPlusUpdate,
)
from app.services.grilla_salarial_service import GrillaSalarialService

router = APIRouter(prefix="/api/v1/grilla-salarial", tags=["Grilla Salarial"])


# ── SalarioBase ──────────────────────────────────────────────────────────────


@router.get("/base", response_model=list[SalarioBaseResponse])
async def listar_base(
    rol: str | None = Query(None),
    vigente: bool | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(GRILLA_SALARIAL_VER)),
    db: AsyncSession = Depends(get_db),
):
    """Listar salarios base con filtros opcionales por rol y vigencia."""
    svc = GrillaSalarialService(db, current_user.tenant_id, current_user.id)
    return await svc.listar_base(rol=rol, vigente=vigente, offset=offset, limit=limit)


@router.post("/base", response_model=SalarioBaseResponse, status_code=status.HTTP_201_CREATED)
async def crear_base(
    data: SalarioBaseCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(GRILLA_SALARIAL_CREAR)),
    db: AsyncSession = Depends(get_db),
):
    """Crear un nuevo salario base para un rol."""
    svc = GrillaSalarialService(db, current_user.tenant_id, current_user.id)
    return await svc.crear_base(data)


@router.get("/base/{base_id}", response_model=SalarioBaseResponse)
async def obtener_base(
    base_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(GRILLA_SALARIAL_VER)),
    db: AsyncSession = Depends(get_db),
):
    """Obtener detalle de un salario base por ID."""
    svc = GrillaSalarialService(db, current_user.tenant_id, current_user.id)
    return await svc.obtener_base(base_id)


@router.put("/base/{base_id}", response_model=SalarioBaseResponse)
async def editar_base(
    base_id: UUID,
    data: SalarioBaseUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(GRILLA_SALARIAL_EDITAR)),
    db: AsyncSession = Depends(get_db),
):
    """Editar monto o fecha de fin de un salario base."""
    svc = GrillaSalarialService(db, current_user.tenant_id, current_user.id)
    return await svc.editar_base(base_id, data)


@router.delete("/base/{base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_base(
    base_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(GRILLA_SALARIAL_ELIMINAR)),
    db: AsyncSession = Depends(get_db),
):
    """Eliminar (soft delete) un salario base."""
    svc = GrillaSalarialService(db, current_user.tenant_id, current_user.id)
    await svc.eliminar_base(base_id)


# ── SalarioPlus ──────────────────────────────────────────────────────────────


@router.get("/plus", response_model=list[SalarioPlusResponse])
async def listar_plus(
    grupo: str | None = Query(None),
    rol: str | None = Query(None),
    vigente: bool | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(GRILLA_SALARIAL_VER)),
    db: AsyncSession = Depends(get_db),
):
    """Listar plus salariales con filtros opcionales por grupo, rol y vigencia."""
    svc = GrillaSalarialService(db, current_user.tenant_id, current_user.id)
    return await svc.listar_plus(grupo=grupo, rol=rol, vigente=vigente, offset=offset, limit=limit)


@router.post("/plus", response_model=SalarioPlusResponse, status_code=status.HTTP_201_CREATED)
async def crear_plus(
    data: SalarioPlusCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(GRILLA_SALARIAL_CREAR)),
    db: AsyncSession = Depends(get_db),
):
    """Crear un nuevo plus salarial para un grupo y rol."""
    svc = GrillaSalarialService(db, current_user.tenant_id, current_user.id)
    return await svc.crear_plus(data)


@router.get("/plus/{plus_id}", response_model=SalarioPlusResponse)
async def obtener_plus(
    plus_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(GRILLA_SALARIAL_VER)),
    db: AsyncSession = Depends(get_db),
):
    """Obtener detalle de un plus salarial por ID."""
    svc = GrillaSalarialService(db, current_user.tenant_id, current_user.id)
    return await svc.obtener_plus(plus_id)


@router.put("/plus/{plus_id}", response_model=SalarioPlusResponse)
async def editar_plus(
    plus_id: UUID,
    data: SalarioPlusUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(GRILLA_SALARIAL_EDITAR)),
    db: AsyncSession = Depends(get_db),
):
    """Editar monto, descripción o fecha de fin de un plus salarial."""
    svc = GrillaSalarialService(db, current_user.tenant_id, current_user.id)
    return await svc.editar_plus(plus_id, data)


@router.delete("/plus/{plus_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_plus(
    plus_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission(GRILLA_SALARIAL_ELIMINAR)),
    db: AsyncSession = Depends(get_db),
):
    """Eliminar (soft delete) un plus salarial."""
    svc = GrillaSalarialService(db, current_user.tenant_id, current_user.id)
    await svc.eliminar_plus(plus_id)
