import io
import os
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.padron_repository import PadronRepository
from app.schemas.calificaciones import (
    EntradaSinCorregirItem,
    ReporteFinalizacionResponse,
)


class ReporteFinalizacionService:
    COLUMNAS_FINALIZACION = {"finalizado", "entregado", "completado", "finished", "submitted"}

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = CalificacionRepository(session, tenant_id)
        self.padron_repo = PadronRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id

    async def procesar_reporte(
        self, file: UploadFile, materia_id: UUID
    ) -> ReporteFinalizacionResponse:
        ext = os.path.splitext(file.filename or "")[1].lower()

        if ext not in (".xlsx", ".csv"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Formato no soportado. Use archivos .xlsx o .csv",
            )

        try:
            content = await file.read()
            if ext == ".xlsx":
                actividades_textuales, entries = self._parse_xlsx(content)
            else:
                actividades_textuales, entries = self._parse_csv(content)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Error al parsear el archivo",
            )

        # Get entrada_padron IDs for this materia
        # First get active version
        from app.models.entrada_padron import EntradaPadron
        from app.models.version_padron import VersionPadron
        from sqlalchemy import select

        version_stmt = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.activa == True,
                VersionPadron.is_deleted == False,
            )
        )
        result = await self.session.execute(version_stmt)
        version = result.scalar_one_or_none()

        if not version:
            raise HTTPException(status_code=400, detail="No hay versión activa de padrón para esta materia")

        # Get entrada ids
        entrada_stmt = (
            select(EntradaPadron.id, EntradaPadron.email)
            .where(
                EntradaPadron.version_id == version.id,
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.is_deleted == False,
            )
        )
        entrada_result = await self.session.execute(entrada_stmt)
        entrada_map = {e.email: e.id for e in entrada_result.all() if e.email}

        entrada_ids = list(entrada_map.values())

        # Find sin calificar
        sin_calificar_data = await self.repo.find_sin_calificar(
            materia_id=materia_id,
            entrada_padron_ids=entrada_ids,
            actividades_textuales=actividades_textuales,
        )

        sin_corregir = [
            EntradaSinCorregirItem(
                alumno_nombre=item["alumno_nombre"],
                actividad=item["actividad"],
            )
            for item in sin_calificar_data
        ]

        return ReporteFinalizacionResponse(
            sin_corregir=sin_corregir,
            total=len(sin_corregir),
        )

    def _parse_xlsx(self, content: bytes) -> tuple[list[str], list[dict]]:
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active
        if ws is None:
            raise HTTPException(status_code=422, detail="El archivo xlsx no contiene hojas")

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise HTTPException(status_code=422, detail="El archivo está vacío")

        headers = [str(h).strip() if h else "" for h in rows[0]]
        return self._procesar_headers_y_filas(headers, rows[1:])

    def _parse_csv(self, content: bytes) -> tuple[list[str], list[dict]]:
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
        return self._procesar_headers_y_filas(headers, cleaned[1:])

    def _procesar_headers_y_filas(
        self, headers: list[str], data_rows: list[list]
    ) -> tuple[list[str], list[dict]]:
        """Process report headers and detect finalization columns vs metadata columns."""
        actividades_textuales: list[str] = []
        entries: list[dict] = []

        non_empty_rows = []
        for row in data_rows:
            if any(str(v).strip() for v in row if v is not None):
                non_empty_rows.append(row)

        # Detect activity columns (non-metadata columns that are NOT finalization status columns)
        # Finalization status columns are those whose header indicates status (finalizado/entregado etc)
        act_indices: dict[str, int] = {}
        status_indices: dict[str, int] = {}

        for i, header in enumerate(headers):
            h_lower = header.strip().lower()
            if h_lower in {"nombre", "apellidos", "apellido", "email", "usuario", "username"}:
                continue

            if h_lower in self.COLUMNAS_FINALIZACION:
                status_indices[h_lower] = i
                continue

            # Check if column has textual activity data (not numeric)
            has_data = any(
                i < len(row) and row[i] is not None and str(row[i]).strip()
                for row in non_empty_rows
            )
            if not has_data:
                continue

            # Only textual activities (RN-08: numeric activities don't count)
            # We detect textual by checking if values are non-numeric
            all_textual = True
            for row in non_empty_rows:
                if i < len(row) and row[i] is not None:
                    val = str(row[i]).strip()
                    if val:
                        try:
                            float(val)
                            all_textual = False
                            break
                        except ValueError:
                            pass

            if all_textual:
                # This is a textual activity column
                actividades_textuales.append(header.strip())
                act_indices[header.strip()] = i

        # Build entries
        for row in non_empty_rows:
            entry = {}
            for h, idx in act_indices.items():
                if idx < len(row):
                    entry[h] = str(row[idx]).strip() if row[idx] is not None else None
            if any(v for v in entry.values()):
                entries.append(entry)

        return actividades_textuales, entries
