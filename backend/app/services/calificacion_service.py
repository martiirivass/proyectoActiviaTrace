import io
import os
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.umbral_materia_repository import UmbralMateriaRepository
from app.schemas.calificaciones import (
    ActividadDetectadaItem,
    CalificacionConfirmResponse,
    CalificacionPreviewResponse,
    UmbralMateriaResponse,
)
from app.services.audit_service import AuditService

VALORES_APROBATORIOS_DEFAULT = ["Satisfactorio", "Supera lo esperado"]
COLUMNAS_METADATO = {"nombre", "apellidos", "apellido", "email", "usuario", "username"}


class CalificacionService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = CalificacionRepository(session, tenant_id)
        self.umbral_repo = UmbralMateriaRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.audit = AuditService(session)

    async def preview_import(self, file: UploadFile) -> CalificacionPreviewResponse:
        ext = os.path.splitext(file.filename or "")[1].lower()

        if ext not in (".xlsx", ".csv"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Formato no soportado. Use archivos .xlsx o .csv",
            )

        try:
            content = await file.read()
            if ext == ".xlsx":
                actividades, alumnos_count, total_filas = self._parse_xlsx(content)
            else:
                actividades, alumnos_count, total_filas = self._parse_csv(content)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Error al parsear el archivo",
            )

        return CalificacionPreviewResponse(
            actividades=actividades,
            alumnos_count=alumnos_count,
            total_filas=total_filas,
        )

    def _parse_xlsx(self, content: bytes) -> tuple[list[ActividadDetectadaItem], int, int]:
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active
        if ws is None:
            raise HTTPException(status_code=422, detail="El archivo xlsx no contiene hojas")

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise HTTPException(status_code=422, detail="El archivo está vacío")

        headers = [str(h).strip() if h else "" for h in rows[0]]
        return self._detect_actividades(headers, rows[1:])

    def _parse_csv(self, content: bytes) -> tuple[list[ActividadDetectadaItem], int, int]:
        import csv

        text = content.decode("utf-8-sig")
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(text[:2048]).delimiter if text.strip() else ","
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)

        if not rows:
            raise HTTPException(status_code=422, detail="El archivo está vacío")

        cleaned = [[cell.strip() for cell in row] for row in rows]
        headers = cleaned[0]
        return self._detect_actividades(headers, cleaned[1:])

    def _detect_actividades(
        self, headers: list[str], data_rows: list[list]
    ) -> tuple[list[ActividadDetectadaItem], int, int]:
        actividades: list[ActividadDetectadaItem] = []
        total_filas = 0

        non_empty_rows = []
        for row in data_rows:
            if any(str(v).strip() for v in row if v is not None):
                non_empty_rows.append(row)

        total_filas = len(non_empty_rows)

        for i, header in enumerate(headers):
            h_lower = header.strip().lower()
            if h_lower in COLUMNAS_METADATO:
                continue

            # Check if this column has data
            has_data = any(
                i < len(row) and row[i] is not None and str(row[i]).strip()
                for row in non_empty_rows
            )
            if not has_data:
                continue

            if header.strip().endswith("(Real)"):
                actividades.append(ActividadDetectadaItem(nombre=header.strip(), tipo="numerica"))
            elif h_lower not in COLUMNAS_METADATO:
                actividades.append(ActividadDetectadaItem(nombre=header.strip(), tipo="textual"))

        unique_alumnos = len(non_empty_rows)
        return actividades, unique_alumnos, total_filas

    async def confirm_import(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        actividades_seleccionadas: list[str],
        entries: list[dict],
        actor_id: UUID,
    ) -> CalificacionConfirmResponse:
        """Import calificaciones for selected activities.

        entries format: list of dicts with keys like {nombre, apellidos, email, <actividad_name>: value, ...}
        """
        umbral = await self.umbral_repo.get_by_asignacion(actor_id)
        umbral_pct = umbral.umbral_pct if umbral else 60
        valores_aprob = umbral.valores_aprobatorios if umbral and umbral.valores_aprobatorios else VALORES_APROBATORIOS_DEFAULT

        now = datetime.now(timezone.utc)
        calificaciones_data = []

        from app.repositories.padron_repository import PadronRepository
        from app.models.entrada_padron import EntradaPadron
        from sqlalchemy import select

        padron_repo = PadronRepository(self.session, self.tenant_id)

        # Get current version for this materia+cohorte
        version = await padron_repo.get_active_version(materia_id, cohorte_id)
        if not version:
            raise HTTPException(status_code=400, detail="No hay versión activa de padrón para esta materia y cohorte")

        # Build a lookup of email -> entrada_padron.id
        stmt = (
            select(EntradaPadron)
            .where(
                EntradaPadron.version_id == version.id,
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        entradas = {e.email: e.id for e in result.scalars().all() if e.email}

        for entry in entries:
            email = entry.get("email", "").strip().lower() if entry.get("email") else None
            entrada_id = entradas.get(email) if email else None
            if not entrada_id:
                continue

            for actividad in actividades_seleccionadas:
                raw_val = entry.get(actividad)
                if raw_val is None or str(raw_val).strip() == "":
                    continue

                nota_numerica = None
                nota_textual = None

                # Try to parse as number
                try:
                    nota_numerica = float(raw_val)
                except (ValueError, TypeError):
                    nota_textual = str(raw_val).strip()

                # Derive aprobado
                aprobado = self._derivar_aprobado(
                    nota_numerica=nota_numerica,
                    nota_textual=nota_textual,
                    umbral_pct=umbral_pct,
                    valores_aprobatorios=valores_aprob,
                )

                calificaciones_data.append({
                    "entrada_padron_id": entrada_id,
                    "materia_id": materia_id,
                    "actividad": actividad,
                    "nota_numerica": nota_numerica,
                    "nota_textual": nota_textual,
                    "aprobado": aprobado,
                    "origen": "Importado",
                    "importado_at": now,
                })

        created = await self.repo.bulk_create_calificaciones(calificaciones_data)

        # Audit log
        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion="CALIFICACIONES_IMPORTAR",
            materia_id=materia_id,
            detalle={
                "materia_id": str(materia_id),
                "cohorte_id": str(cohorte_id),
                "actividades_seleccionadas": actividades_seleccionadas,
                "filas_afectadas": len(created),
            },
            filas_afectadas=len(created),
        )

        return CalificacionConfirmResponse(
            registros_creados=len(created),
            materia_id=materia_id,
            cohorte_id=cohorte_id,
        )

    def _derivar_aprobado(
        self,
        nota_numerica: float | None,
        nota_textual: str | None,
        umbral_pct: int = 60,
        valores_aprobatorios: list[str] | None = None,
    ) -> bool:
        """Derive if a calificacion is approved based on rules.

        - If nota_numerica is set: >= umbral_pct → aprobado
        - If only nota_textual is set: in valores_aprobatorios → aprobado
        - Neither set: False
        """
        if nota_numerica is not None:
            return nota_numerica >= umbral_pct

        if nota_textual is not None:
            vals = [v.lower() for v in (valores_aprobatorios or VALORES_APROBATORIOS_DEFAULT)]
            return nota_textual.strip().lower() in vals

        return False

    async def get_umbral(self, asignacion_id: UUID) -> UmbralMateriaResponse | dict:
        umbral = await self.umbral_repo.get_by_asignacion(asignacion_id)
        if umbral:
            return UmbralMateriaResponse(
                id=umbral.id,
                asignacion_id=umbral.asignacion_id,
                materia_id=umbral.materia_id,
                umbral_pct=umbral.umbral_pct,
                valores_aprobatorios=umbral.valores_aprobatorios,
            )
        return {
            "umbral_pct": 60,
            "valores_aprobatorios": VALORES_APROBATORIOS_DEFAULT,
        }

    async def configurar_umbral(
        self,
        asignacion_id: UUID,
        materia_id: UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str],
        actor_id: UUID,
    ) -> UmbralMateriaResponse:
        umbral = await self.umbral_repo.upsert(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios or None,
        )

        # Audit
        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion="CALIFICACIONES_IMPORTAR",
            materia_id=materia_id,
            detalle={
                "accion": "configurar_umbral",
                "asignacion_id": str(asignacion_id),
                "umbral_pct": umbral_pct,
            },
        )

        return UmbralMateriaResponse(
            id=umbral.id,
            asignacion_id=umbral.asignacion_id,
            materia_id=umbral.materia_id,
            umbral_pct=umbral.umbral_pct,
            valores_aprobatorios=umbral.valores_aprobatorios,
        )

    async def recalcular_aprobados(self, asignacion_id: UUID) -> dict:
        umbral = await self.umbral_repo.get_by_asignacion(asignacion_id)
        umbral_pct = umbral.umbral_pct if umbral else 60
        valores_aprob = umbral.valores_aprobatorios if umbral and umbral.valores_aprobatorios else VALORES_APROBATORIOS_DEFAULT

        count = await self.repo.recalcular_aprobados(
            asignacion_id=asignacion_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprob,
        )

        return {
            "registros_actualizados": count,
            "asignacion_id": str(asignacion_id),
        }
