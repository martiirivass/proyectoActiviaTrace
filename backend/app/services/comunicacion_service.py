from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunicacion import EstadoComunicacion
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.repositories.lote_comunicacion_repository import LoteComunicacionRepository
from app.schemas.comunicaciones import (
    AprobarLoteResponse,
    ComunicacionDetalle,
    ComunicacionIndividualResponse,
    ComunicacionItem,
    ComunicacionListResponse,
    ComunicacionMasivaResponse,
    ComunicacionPreviewResponse,
    DistribucionEstados,
    LoteDetalle,
    LotePendienteItem,
    RechazarLoteResponse,
)
from app.services.audit_service import AuditService
from app.core.audit_codes import COMUNICACION_ENVIAR


class ComunicacionService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = ComunicacionRepository(session, tenant_id)
        self.lote_repo = LoteComunicacionRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.audit = AuditService(session)

    async def preview(
        self,
        asunto: str,
        cuerpo: str,
        materia_id: UUID,
        destinatarios: list[str],
    ) -> ComunicacionPreviewResponse:
        return ComunicacionPreviewResponse(
            asunto=asunto,
            cuerpo_renderizado=cuerpo,
            cantidad_destinatarios=len(destinatarios),
        )

    async def enviar_individual(
        self,
        asunto: str,
        cuerpo: str,
        materia_id: UUID,
        destinatario_email: str,
        actor_id: UUID,
    ) -> ComunicacionIndividualResponse:
        comunicacion = await self.repo.create_comunicacion(
            enviado_por=actor_id,
            materia_id=materia_id,
            destinatario=destinatario_email,
            asunto=asunto,
            cuerpo=cuerpo,
            estado=EstadoComunicacion.PENDIENTE,
        )

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=COMUNICACION_ENVIAR,
            materia_id=materia_id,
            detalle={
                "tipo": "individual",
                "comunicacion_id": str(comunicacion.id),
                "materia_id": str(materia_id),
                "cantidad_destinatarios": 1,
            },
            filas_afectadas=1,
        )

        return ComunicacionIndividualResponse(
            id=comunicacion.id,
            estado=comunicacion.estado.value,
        )

    async def enviar_masivo(
        self,
        asunto: str,
        cuerpo: str,
        materia_id: UUID,
        destinatarios: list[str],
        actor_id: UUID,
    ) -> ComunicacionMasivaResponse:
        # Deduplicar destinatarios
        emails_unicos = list(set(destinatarios))

        # Crear lote
        lote = await self.lote_repo.create_lote(
            materia_id=materia_id,
            enviado_por=actor_id,
            total_mensajes=len(emails_unicos),
        )

        # Crear comunicaciones
        entries = [
            {
                "lote_id": lote.id,
                "enviado_por": actor_id,
                "materia_id": materia_id,
                "destinatario": email,
                "asunto": asunto,
                "cuerpo": cuerpo,
                "estado": EstadoComunicacion.PENDIENTE,
            }
            for email in emails_unicos
        ]
        await self.repo.bulk_create_comunicaciones(entries)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=COMUNICACION_ENVIAR,
            materia_id=materia_id,
            detalle={
                "tipo": "masivo",
                "lote_id": str(lote.id),
                "materia_id": str(materia_id),
                "cantidad_destinatarios": len(emails_unicos),
            },
            filas_afectadas=len(emails_unicos),
        )

        return ComunicacionMasivaResponse(
            lote_id=lote.id,
            total_mensajes=len(emails_unicos),
            estado_lote=lote.estado.value,
        )

    async def listar_lotes_pendientes(self) -> list[LotePendienteItem]:
        lotes = await self.lote_repo.list_pendientes()
        return [
            LotePendienteItem(
                id=l.id,
                materia_id=l.materia_id,
                enviado_por=l.enviado_por,
                total_mensajes=l.total_mensajes,
                created_at=l.created_at,
            )
            for l in lotes
        ]

    async def aprobar_lote(
        self,
        lote_id: UUID,
        aprobado_por: UUID,
    ) -> AprobarLoteResponse:
        lote = await self.lote_repo.get_by_id(lote_id)
        if lote is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
        if lote.estado.value != "Pendiente":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El lote ya está en estado {lote.estado.value}",
            )

        lote = await self.lote_repo.aprobar(lote_id, aprobado_por)
        if lote is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se pudo aprobar el lote")

        # Contar mensajes liberados (Pendientes en el lote)
        comunicaciones = await self.repo.list_by_lote(lote_id)
        pendientes = [c for c in comunicaciones if c.estado == EstadoComunicacion.PENDIENTE]

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=aprobado_por,
            accion=COMUNICACION_ENVIAR,
            materia_id=lote.materia_id,
            detalle={
                "tipo": "aprobacion_lote",
                "lote_id": str(lote_id),
                "materia_id": str(lote.materia_id),
                "total_mensajes": lote.total_mensajes,
            },
            filas_afectadas=lote.total_mensajes,
        )

        return AprobarLoteResponse(
            lote_id=lote.id,
            estado=lote.estado.value,
            mensajes_liberados=len(pendientes),
        )

    async def rechazar_lote(self, lote_id: UUID, actor_id: UUID) -> RechazarLoteResponse:
        lote = await self.lote_repo.get_by_id(lote_id)
        if lote is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
        if lote.estado.value != "Pendiente":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El lote ya está en estado {lote.estado.value}",
            )

        lote = await self.lote_repo.rechazar(lote_id)
        if lote is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se pudo rechazar el lote")

        # Cancelar mensajes Pendientes del lote
        mensajes_cancelados = await self.repo.cancelar_por_lote(lote_id)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=COMUNICACION_ENVIAR,
            materia_id=lote.materia_id,
            detalle={
                "tipo": "rechazo_lote",
                "lote_id": str(lote_id),
                "materia_id": str(lote.materia_id),
                "total_mensajes": lote.total_mensajes,
            },
            filas_afectadas=mensajes_cancelados,
        )

        return RechazarLoteResponse(
            lote_id=lote.id,
            estado=lote.estado.value,
            mensajes_cancelados=mensajes_cancelados,
        )

    async def obtener_detalle_lote(self, lote_id: UUID) -> LoteDetalle:
        lote = await self.lote_repo.get_by_id(lote_id)
        if lote is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

        comunicaciones = await self.repo.list_by_lote(lote_id)
        distribucion = await self._calcular_distribucion(comunicaciones)

        return LoteDetalle(
            id=lote.id,
            materia_id=lote.materia_id,
            total_mensajes=lote.total_mensajes,
            estado=lote.estado.value,
            aprobado_por=lote.aprobado_por,
            aprobado_en=lote.aprobado_en,
            distribucion_estados=distribucion,
        )

    async def listar_por_materia(
        self,
        materia_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> ComunicacionListResponse:
        comunicaciones = await self.repo.list_by_materia(materia_id, offset, limit)
        total = await self.repo.count_by_materia(materia_id)

        items = [
            ComunicacionItem(
                id=c.id,
                destinatario=self._enmascarar_email(c.destinatario),
                asunto=c.asunto,
                estado=c.estado.value,
                created_at=c.created_at,
                enviado_at=c.enviado_at,
                error_msg=c.error_msg,
            )
            for c in comunicaciones
        ]

        return ComunicacionListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    async def obtener_distribucion(self, materia_id: UUID) -> DistribucionEstados:
        counts = await self.repo.count_by_estado(materia_id)
        return DistribucionEstados(
            pendiente=counts.get("Pendiente", 0),
            enviando=counts.get("Enviando", 0),
            enviado=counts.get("Enviado", 0),
            error=counts.get("Error", 0),
            cancelado=counts.get("Cancelado", 0),
        )

    async def obtener_comunicacion(self, comunicacion_id: UUID) -> ComunicacionDetalle:
        comunicacion = await self.repo.get(comunicacion_id)
        if comunicacion is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunicación no encontrada")

        return ComunicacionDetalle(
            id=comunicacion.id,
            destinatario=self._enmascarar_email(comunicacion.destinatario),
            asunto=comunicacion.asunto,
            cuerpo=comunicacion.cuerpo,
            estado=comunicacion.estado.value,
            materia_id=comunicacion.materia_id,
            created_at=comunicacion.created_at,
            enviado_at=comunicacion.enviado_at,
            error_msg=comunicacion.error_msg,
        )

    async def _calcular_distribucion(
        self,
        comunicaciones: list,
    ) -> DistribucionEstados:
        counts = {"Pendiente": 0, "Enviando": 0, "Enviado": 0, "Error": 0, "Cancelado": 0}
        for c in comunicaciones:
            estado = c.estado.value if hasattr(c.estado, "value") else c.estado
            if estado in counts:
                counts[estado] += 1
        return DistribucionEstados(
            pendiente=counts["Pendiente"],
            enviando=counts["Enviando"],
            enviado=counts["Enviado"],
            error=counts["Error"],
            cancelado=counts["Cancelado"],
        )

    @staticmethod
    def _enmascarar_email(email: str) -> str:
        """Enmascarar email mostrando solo primeros 4 chars del local-part."""
        if "@" not in email:
            return email
        local, dominio = email.split("@", 1)
        if len(local) <= 4:
            prefix = local[:1]
        else:
            prefix = local[:4]
        return f"{prefix}***@{dominio}"
