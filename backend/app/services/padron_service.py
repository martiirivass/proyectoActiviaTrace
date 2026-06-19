import csv
import io
import os
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.padron_repository import PadronRepository
from app.schemas.padron import (
    EntradaPreviewItem,
    PadronConfirmResponse,
    PadronPreviewResponse,
    VersionPadronListResponse,
    VersionPadronResponse,
)
from app.services.audit_service import AuditService


class PadronService:
    COLUMNAS_REQUERIDAS = {"nombre", "apellidos"}
    COLUMNAS_OPCIONALES = {"email", "comision", "regional"}

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = PadronRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.audit = AuditService(session)

    async def preview_import(self, file: UploadFile) -> PadronPreviewResponse:
        ext = os.path.splitext(file.filename or "")[1].lower()

        if ext not in (".xlsx", ".csv"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Formato no soportado. Use archivos .xlsx o .csv",
            )

        try:
            content = await file.read()
            if ext == ".xlsx":
                entries = self._parse_xlsx(content)
            else:
                entries = self._parse_csv(content)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Error al parsear el archivo",
            )

        return PadronPreviewResponse(entries=entries, total_filas=len(entries))

    def _parse_xlsx(self, content: bytes) -> list[EntradaPreviewItem]:
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active
        if ws is None:
            raise HTTPException(status_code=422, detail="El archivo xlsx no contiene hojas")

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise HTTPException(status_code=422, detail="El archivo está vacío")

        headers = [str(h).strip().lower() if h else "" for h in rows[0]]
        self._validar_columnas(headers)

        col_indices = {h: i for i, h in enumerate(headers)}

        entries = []
        for row in rows[1:]:
            if all(v is None or str(v).strip() == "" for v in row):
                continue
            entries.append(self._build_entry(row, col_indices))

        return entries

    def _parse_csv(self, content: bytes) -> list[EntradaPreviewItem]:
        text = content.decode("utf-8-sig")
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(text[:2048]).delimiter if text.strip() else ","
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)

        if not rows:
            raise HTTPException(status_code=422, detail="El archivo está vacío")

        cleaned = []
        for row in rows:
            cleaned.append([cell.strip() for cell in row])

        headers = [h.lower() for h in cleaned[0]]
        self._validar_columnas(headers)

        col_indices = {h: i for i, h in enumerate(headers)}

        entries = []
        for row in cleaned[1:]:
            if all(c == "" for c in row):
                continue
            entries.append(self._build_entry(row, col_indices))

        return entries

    def _validar_columnas(self, headers: list[str]) -> None:
        header_set = set(headers)
        faltantes = self.COLUMNAS_REQUERIDAS - header_set
        if faltantes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Columnas faltantes: {', '.join(sorted(faltantes))}",
            )

    def _build_entry(
        self, row: list, col_indices: dict[str, int]
    ) -> EntradaPreviewItem:
        def val(col: str) -> str | None:
            idx = col_indices.get(col)
            if idx is None or idx >= len(row):
                return None
            v = row[idx]
            return str(v).strip() if v is not None else None

        return EntradaPreviewItem(
            nombre=val("nombre") or "",
            apellidos=val("apellidos") or "",
            email=val("email"),
            comision=val("comision"),
            regional=val("regional"),
        )

    async def confirm_import(
        self, materia_id: UUID, cohorte_id: UUID, entries: list[dict], actor_id: UUID
    ) -> PadronConfirmResponse:
        version = await self.repo.create_version(materia_id, cohorte_id, actor_id)
        _entries = await self.repo.bulk_create_entries(version.id, entries)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion="PADRON_CARGAR",
            materia_id=materia_id,
            detalle={
                "materia_id": str(materia_id),
                "cohorte_id": str(cohorte_id),
                "version_id": str(version.id),
                "filas_afectadas": len(_entries),
            },
            filas_afectadas=len(_entries),
        )

        return PadronConfirmResponse(
            version_id=version.id,
            activa=version.activa,
            filas_creadas=len(_entries),
        )

    async def list_versions(
        self, materia_id: UUID, cohorte_id: UUID
    ) -> VersionPadronListResponse:
        versions_data = await self.repo.get_versions(materia_id, cohorte_id)
        items = [
            VersionPadronResponse(
                id=v["version"].id,
                materia_id=v["version"].materia_id,
                cohorte_id=v["version"].cohorte_id,
                cargado_por=v["version"].cargado_por,
                cargado_at=v["version"].cargado_at,
                activa=v["version"].activa,
                entrada_count=v["entrada_count"],
                created_at=v["version"].created_at,
            )
            for v in versions_data
        ]
        return VersionPadronListResponse(versiones=items, total=len(items))

    async def vaciar_materia(
        self, materia_id: UUID, actor_id: UUID
    ) -> dict:
        versiones_afectadas = await self.repo.vaciar_materia(materia_id)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion="PADRON_VACIAR",
            materia_id=materia_id,
            detalle={
                "materia_id": str(materia_id),
                "versiones_afectadas": versiones_afectadas,
            },
            filas_afectadas=versiones_afectadas,
        )

        return {
            "materia_id": materia_id,
            "versiones_afectadas": versiones_afectadas,
        }

    async def sync_from_moodle(
        self, materia_id: UUID, cohorte_id: UUID, actor_id: UUID
    ) -> dict:
        from app.integrations.moodle_ws import MoodleWSClient
        from app.core.config import get_settings

        settings = get_settings()
        if not settings.moodle_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integración Moodle no configurada globalmente",
            )

        client = MoodleWSClient(
            base_url=settings.moodle_url,
            token=settings.moodle_token,
            timeout=settings.moodle_timeout,
        )

        try:
            users = await client.get_users_by_cohort(cohorte_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al conectar con Moodle: {str(e)}",
            )

        entries = []
        for user in users:
            entries.append({
                "nombre": user.get("firstname", ""),
                "apellidos": user.get("lastname", ""),
                "email": user.get("email"),
                "comision": None,
                "regional": None,
            })

        return await self.confirm_import(materia_id, cohorte_id, entries, actor_id)
