from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.evaluaciones import (
    AlumnoConvocadoResponse,
    ConvocadosUpdateRequest,
    EvaluacionCreate,
    EvaluacionDetailResponse,
    EvaluacionListResponse,
    EvaluacionResponse,
    EvaluacionUpdate,
    MetricasResponse,
    ReservaAgendaResponse,
    ReservaCreate,
    ReservaResponse,
    ResultadoCreate,
    ResultadoListResponse,
    ResultadoResponse,
    ResultadoUpdate,
)
from app.services.evaluacion_service import EvaluacionService
from app.services.reserva_service import ReservaService
from app.services.resultado_service import ResultadoService

router = APIRouter(prefix="/api/v1/evaluaciones", tags=["Evaluaciones / Coloquios"])


# ===== Static routes MUST come before parameterized /{id} routes =====


# --- Métricas ---

@router.get("/metricas", response_model=MetricasResponse)
async def obtener_metricas(
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ResultadoService(db, current_user.tenant_id)
    return await svc.obtener_metricas()


# --- Reservas (static) ---

@router.post("/reservas", status_code=201, response_model=ReservaResponse)
async def reservar_turno(
    data: ReservaCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:reservar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ReservaService(db, current_user.tenant_id)
    return await svc.reservar_turno(
        evaluacion_id=data.evaluacion_id,
        dia_convocatoria_id=data.dia_convocatoria_id,
        alumno_id=current_user.id,
        actor_id=current_user.id,
    )


@router.post("/reservas/{id}/cancelar")
async def cancelar_reserva(
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:reservar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ReservaService(db, current_user.tenant_id)
    return await svc.cancelar_reserva(
        reserva_id=id,
        alumno_id=current_user.id,
        actor_id=current_user.id,
    )


@router.get("/reservas", response_model=ReservaAgendaResponse)
async def listar_agenda(
    evaluacion_id: UUID | None = Query(None),
    materia_id: UUID | None = Query(None),
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    estado: str | None = Query(None),
    alumno_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ReservaService(db, current_user.tenant_id)
    return await svc.listar_agenda(
        evaluacion_id=evaluacion_id,
        materia_id=materia_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        estado=estado,
        alumno_id=alumno_id,
        offset=offset,
        limit=limit,
    )


@router.get("/reservas/mis-reservas", response_model=ReservaAgendaResponse)
async def mis_reservas(
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:reservar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ReservaService(db, current_user.tenant_id)
    return await svc.mis_reservas(alumno_id=current_user.id)


# --- Resultados (static) ---

@router.post("/resultados", status_code=201, response_model=ResultadoResponse)
async def registrar_resultado(
    data: ResultadoCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ResultadoService(db, current_user.tenant_id)
    return await svc.registrar_resultado(data=data, actor_id=current_user.id)


@router.patch("/resultados/{id}", response_model=ResultadoResponse)
async def actualizar_resultado(
    data: ResultadoUpdate,
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ResultadoService(db, current_user.tenant_id)
    return await svc.actualizar_resultado(
        resultado_id=id,
        data=data,
        actor_id=current_user.id,
    )


@router.get("/resultados", response_model=ResultadoListResponse)
async def listar_resultados(
    evaluacion_id: UUID | None = Query(None),
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    estado: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ResultadoService(db, current_user.tenant_id)
    return await svc.listar_resultados(
        evaluacion_id=evaluacion_id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        estado=estado,
        offset=offset,
        limit=limit,
    )


# ===== Convocatorias (root + parameterized /{id}) =====

@router.post("/", status_code=201, response_model=EvaluacionResponse)
async def crear_convocatoria(
    data: EvaluacionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = EvaluacionService(db, current_user.tenant_id)
    return await svc.crear_convocatoria(data=data, actor_id=current_user.id)


@router.get("/", response_model=EvaluacionListResponse)
async def listar_convocatorias(
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    activa: bool | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = EvaluacionService(db, current_user.tenant_id)
    return await svc.listar_convocatorias(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        activa=activa,
        offset=offset,
        limit=limit,
    )


@router.get("/{id}", response_model=EvaluacionDetailResponse)
async def obtener_detalle_convocatoria(
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = EvaluacionService(db, current_user.tenant_id)
    return await svc.obtener_detalle(evaluacion_id=id)


@router.patch("/{id}", response_model=EvaluacionResponse)
async def editar_convocatoria(
    data: EvaluacionUpdate,
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = EvaluacionService(db, current_user.tenant_id)
    return await svc.editar_convocatoria(evaluacion_id=id, data=data, actor_id=current_user.id)


@router.post("/{id}/cerrar")
async def cerrar_convocatoria(
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    if "ADMIN" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo ADMIN puede cerrar convocatorias",
        )
    svc = EvaluacionService(db, current_user.tenant_id)
    return await svc.cerrar_convocatoria(evaluacion_id=id, actor_id=current_user.id)


@router.post("/{id}/convocados")
async def importar_convocados(
    data: ConvocadosUpdateRequest,
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = EvaluacionService(db, current_user.tenant_id)
    return await svc.importar_convocados(
        evaluacion_id=id,
        alumno_ids=data.alumno_ids,
        actor_id=current_user.id,
    )


@router.get("/{id}/convocados", response_model=list[AlumnoConvocadoResponse])
async def listar_convocados(
    id: UUID = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = EvaluacionService(db, current_user.tenant_id)
    return await svc.listar_convocados(evaluacion_id=id)
