import re
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fecha_academica import FechaAcademica, TipoFecha
from app.repositories.fecha_academica_repository import FechaAcademicaRepository
from app.services.audit_service import AuditService

PERIODO_REGEX = re.compile(r"^\d{4}-[12]$")


class FechaAcademicaService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = FechaAcademicaRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.audit = AuditService(session)

    async def create(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        tipo: TipoFecha | str,
        numero: int,
        periodo: str,
        fecha: date,
        titulo: str,
        actor_id: UUID | None = None,
    ) -> FechaAcademica:
        tipo_enum = self._validate_tipo(tipo)
        self._validate_numero(numero)
        self._validate_periodo(periodo)

        existing = await self.repo.find_by_unique(materia_id, cohorte_id, tipo_enum, numero, periodo)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una fecha académica con esa combinación materia, cohorte, tipo, número y periodo",
            )

        obj = await self.repo.create(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            tipo=tipo_enum,
            numero=numero,
            periodo=periodo,
            fecha=fecha,
            titulo=titulo,
        )
        if actor_id:
            await self.audit.log(
                tenant_id=self.tenant_id,
                actor_id=actor_id,
                accion="FECHA_CREAR",
                materia_id=materia_id,
                detalle={
                    "fecha_id": str(obj.id),
                    "tipo": str(tipo_enum.value),
                    "numero": numero,
                    "periodo": periodo,
                },
            )
        return obj

    async def get(self, id: UUID) -> FechaAcademica:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fecha académica no encontrada")
        return obj

    async def list(
        self,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        tipo: TipoFecha | str | None = None,
        periodo: str | None = None,
    ) -> list[FechaAcademica]:
        tipo_enum = None
        if tipo is not None:
            tipo_enum = self._validate_tipo(tipo)
        return await self.repo.list(materia_id=materia_id, cohorte_id=cohorte_id, tipo=tipo_enum, periodo=periodo)

    async def update(
        self,
        id: UUID,
        tipo: TipoFecha | str | None = None,
        numero: int | None = None,
        periodo: str | None = None,
        fecha: date | None = None,
        titulo: str | None = None,
        actor_id: UUID | None = None,
    ) -> FechaAcademica:
        kwargs = {}
        if tipo is not None:
            kwargs["tipo"] = self._validate_tipo(tipo)
        if numero is not None:
            self._validate_numero(numero)
            kwargs["numero"] = numero
        if periodo is not None:
            self._validate_periodo(periodo)
            kwargs["periodo"] = periodo
        if fecha is not None:
            kwargs["fecha"] = fecha
        if titulo is not None:
            kwargs["titulo"] = titulo

        obj = await self.repo.update(id, **kwargs)
        if actor_id:
            detalle = {"fecha_id": str(id)}
            detalle.update(kwargs)
            # Fecha is a date object; convert to ISO string for JSON serialization
            if "fecha" in detalle:
                detalle["fecha"] = detalle["fecha"].isoformat()
            await self.audit.log(
                tenant_id=self.tenant_id,
                actor_id=actor_id,
                accion="FECHA_EDITAR",
                materia_id=obj.materia_id,
                detalle=detalle,
            )
        return obj

    async def delete(self, id: UUID, actor_id: UUID | None = None) -> None:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fecha académica no encontrada")
        await self.repo.soft_delete(id)
        if actor_id:
            await self.audit.log(
                tenant_id=self.tenant_id,
                actor_id=actor_id,
                accion="FECHA_ELIMINAR",
                materia_id=obj.materia_id,
                detalle={"fecha_id": str(id)},
            )

    async def exportar_lms(
        self,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        periodo: str | None = None,
    ) -> str:
        if materia_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="materia_id es requerido para exportar",
            )

        fechas = await self.repo.list(materia_id=materia_id, cohorte_id=cohorte_id, periodo=periodo)

        if not fechas:
            return "No hay fechas académicas registradas para los filtros seleccionados."

        lines = ["<h3>Calendario Académico</h3>", "<ul>"]
        for f in fechas:
            lines.append(
                f"  <li><strong>{f.tipo.value} {f.numero}</strong> — {f.titulo} "
                f"({f.fecha.isoformat()})</li>"
            )
        lines.append("</ul>")
        return "\n".join(lines)

    def _validate_tipo(self, tipo: TipoFecha | str) -> TipoFecha:
        if isinstance(tipo, TipoFecha):
            return tipo
        try:
            return TipoFecha(tipo)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Tipo inválido: {tipo}. Valores válidos: {[e.value for e in TipoFecha]}",
            )

    def _validate_numero(self, numero: int) -> None:
        if numero <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="numero debe ser un entero positivo",
            )

    def _validate_periodo(self, periodo: str) -> None:
        if not PERIODO_REGEX.match(periodo):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail='periodo debe tener formato AAAA-S (ej: "2026-1", "2026-2")',
            )
