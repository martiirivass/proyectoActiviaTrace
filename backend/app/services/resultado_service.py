from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import RESULTADO_REGISTRAR
from app.models.resultado_evaluacion import EstadoResultado
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.repositories.resultado_repository import ResultadoRepository
from app.schemas.evaluaciones import (
    MetricasResponse,
    ResultadoCreate,
    ResultadoListItem,
    ResultadoListResponse,
    ResultadoResponse,
    ResultadoUpdate,
)
from app.services.audit_service import AuditService


class ResultadoService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.resultado_repo = ResultadoRepository(session, tenant_id)
        self.eval_repo = EvaluacionRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.audit = AuditService(session)

    async def registrar_resultado(
        self,
        data: ResultadoCreate,
        actor_id: UUID,
    ) -> ResultadoResponse:
        ev = await self.eval_repo.get(data.evaluacion_id)
        if not ev:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )

        existing = await self.resultado_repo.get_by_alumno_y_evaluacion(
            data.evaluacion_id, data.alumno_id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un resultado para este alumno en esta evaluación",
            )

        resultado = await self.resultado_repo.create(
            evaluacion_id=data.evaluacion_id,
            alumno_id=data.alumno_id,
            nota_final=data.nota_final,
            estado=EstadoResultado.BORRADOR,
        )

        return ResultadoResponse.model_validate(resultado)

    async def actualizar_resultado(
        self,
        resultado_id: UUID,
        data: ResultadoUpdate,
        actor_id: UUID,
    ) -> ResultadoResponse:
        resultado = await self.resultado_repo.get(resultado_id)
        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resultado no encontrado",
            )

        if data.estado:
            nuevo_estado = EstadoResultado(data.estado)
            current_estado = resultado.estado

            if current_estado == EstadoResultado.DEFINITIVO and nuevo_estado == EstadoResultado.BORRADOR:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="No se puede volver de Definitivo a Borrador",
                )

            resultado.estado = nuevo_estado

        if data.nota_final is not None:
            resultado.nota_final = data.nota_final

        await self.session.flush()

        if data.estado == "Definitivo":
            await self.audit.log(
                tenant_id=self.tenant_id,
                actor_id=actor_id,
                accion=RESULTADO_REGISTRAR,
                detalle={
                    "resultado_id": str(resultado_id),
                    "nota_final": resultado.nota_final,
                },
            )

        await self.session.refresh(resultado)
        return ResultadoResponse.model_validate(resultado)

    async def listar_resultados(
        self,
        evaluacion_id: UUID | None = None,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ResultadoListResponse:
        items, total = await self.resultado_repo.list_with_filters(
            evaluacion_id=evaluacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            estado=estado,
            offset=offset,
            limit=limit,
        )

        result_items = []
        for item in items:
            r = item["resultado"]
            result_items.append(ResultadoListItem(
                id=r.id,
                evaluacion_id=r.evaluacion_id,
                alumno_id=r.alumno_id,
                nota_final=r.nota_final,
                estado=r.estado.value if hasattr(r.estado, "value") else str(r.estado),
                alumno_nombre=item.get("alumno_nombre", ""),
                alumno_apellido=item.get("alumno_apellido", ""),
                evaluacion_instancia=item.get("evaluacion_instancia", ""),
                materia_nombre=item.get("materia_nombre", ""),
            ))

        return ResultadoListResponse(items=result_items, total=total)

    async def obtener_metricas(self) -> MetricasResponse:
        metrics = await self.resultado_repo.get_metricas()
        return MetricasResponse(**metrics)
