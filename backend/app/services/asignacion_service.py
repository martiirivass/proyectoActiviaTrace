from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.dictado import Dictado
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.user import User
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.dictado_repository import DictadoRepository

ROLES_VALIDOS = {"ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"}


def compute_estado_vigencia(asignacion: Asignacion) -> str:
    today = date.today()
    if asignacion.hasta is not None and today > asignacion.hasta:
        return "Vencida"
    return "Vigente"


class AsignacionService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.repo = AsignacionRepository(Asignacion, session, tenant_id)
        self.dictado_repo = DictadoRepository(Dictado, session, tenant_id)

    async def create(self, data) -> Asignacion:
        if data.rol not in ROLES_VALIDOS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Rol inválido: {data.rol}")
        return await self.repo.create(**data.model_dump())

    async def get(self, id: UUID) -> Asignacion:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
        return obj

    async def list(
        self,
        usuario_id: UUID | None = None,
        materia_id: UUID | None = None,
        dictado_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        rol: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Asignacion]:
        return await self.repo.list(
            usuario_id=usuario_id,
            materia_id=materia_id,
            dictado_id=dictado_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            rol=rol,
            offset=offset,
            limit=limit,
        )

    async def update(self, id: UUID, data) -> Asignacion:
        obj = await self.repo.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
        kwargs = data.model_dump(exclude_none=True)
        if "rol" in kwargs and kwargs["rol"] not in ROLES_VALIDOS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Rol inválido: {kwargs['rol']}")
        return await self.repo.update(id, **kwargs)

    async def delete(self, id: UUID) -> None:
        await self.repo.soft_delete(id)

    @staticmethod
    def is_vigente(asignacion: Asignacion) -> bool:
        return compute_estado_vigencia(asignacion) == "Vigente"

    # --- Equipos operations ---

    async def mis_equipos(
        self,
        usuario_id: UUID,
        estado: str | None = None,
        rol: str | None = None,
    ) -> list[Asignacion]:
        asignaciones = await self.repo.list(usuario_id=usuario_id, rol=rol)
        if estado:
            asignaciones = [a for a in asignaciones if compute_estado_vigencia(a) == estado]
        return asignaciones

    async def asignar_masivo(
        self,
        dictado_id: UUID,
        rol: str,
        desde: date,
        hasta: date | None,
        usuario_ids: list[UUID],
    ) -> list[Asignacion]:
        if rol not in ROLES_VALIDOS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Rol inválido: {rol}")

        # Validate dictado exists
        dictado = await self.dictado_repo.get(dictado_id)
        if dictado is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dictado no encontrado")

        # Check for duplicates
        seen = set()
        for uid in usuario_ids:
            if uid in seen:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Usuario duplicado: {uid}",
                )
            seen.add(uid)

        # Validate all users exist
        for uid in usuario_ids:
            stmt = select(User).where(User.id == uid, User.tenant_id == self.repo.tenant_id)
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Usuario no encontrado: {uid}",
                )

        asignaciones_data = [
            {
                "usuario_id": uid,
                "rol": rol,
                "dictado_id": dictado_id,
                "materia_id": dictado.materia_id,
                "carrera_id": dictado.carrera_id,
                "cohorte_id": dictado.cohorte_id,
                "desde": desde,
                "hasta": hasta,
            }
            for uid in usuario_ids
        ]

        return await self.repo.bulk_create(asignaciones_data)

    async def clonar_equipo(
        self,
        dictado_origen_id: UUID,
        dictado_destino_id: UUID,
        force: bool = False,
    ) -> list[Asignacion]:
        origen = await self.dictado_repo.get(dictado_origen_id)
        if origen is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dictado origen no encontrado")

        destino = await self.dictado_repo.get(dictado_destino_id)
        if destino is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dictado destino no encontrado")

        if not force:
            existing_count = await self.repo.count_by_dictado(dictado_destino_id)
            if existing_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El dictado destino ya tiene asignaciones. Usá force=true para clonar de todas formas.",
                )

        asignaciones_origen = await self.repo.list_by_dictado(dictado_origen_id)
        if not asignaciones_origen:
            return []

        asignaciones_data = [
            {
                "usuario_id": a.usuario_id,
                "rol": a.rol,
                "dictado_id": dictado_destino_id,
                "materia_id": destino.materia_id,
                "carrera_id": destino.carrera_id,
                "cohorte_id": destino.cohorte_id,
                "responsable_id": a.responsable_id,
                "desde": destino.created_at.date() if hasattr(destino.created_at, 'date') else date.today(),
                "hasta": None,
            }
            for a in asignaciones_origen
        ]

        return await self.repo.bulk_create(asignaciones_data)

    async def modificar_vigencia_general(
        self,
        dictado_id: UUID,
        desde: date,
        hasta: date | None,
    ) -> int:
        if hasta is not None and desde > hasta:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La fecha 'desde' no puede ser posterior a 'hasta'",
            )

        count = await self.repo.update_vigencia(dictado_id, desde, hasta)
        return count

    async def exportar_equipo(self, dictado_id: UUID) -> list[dict]:
        asignaciones = await self.repo.list_by_dictado(dictado_id)
        rows = []
        for a in asignaciones:
            rows.append({
                "docente_id": str(a.usuario_id),
                "rol": a.rol,
                "materia_id": str(a.materia_id) if a.materia_id else "",
                "carrera_id": str(a.carrera_id) if a.carrera_id else "",
                "cohorte_id": str(a.cohorte_id) if a.cohorte_id else "",
                "desde": str(a.desde),
                "hasta": str(a.hasta) if a.hasta else "",
                "estado_vigencia": compute_estado_vigencia(a),
            })
        return rows

    async def get_dictado_info(self, dictado_id: UUID) -> dict | None:
        """Load dictado with materia/carrera/cohorte names for enriched response."""
        stmt = (
            select(Dictado, Materia, Carrera, Cohorte)
            .join(Materia, Dictado.materia_id == Materia.id)
            .join(Carrera, Dictado.carrera_id == Carrera.id)
            .join(Cohorte, Dictado.cohorte_id == Cohorte.id)
            .where(Dictado.id == dictado_id, Dictado.tenant_id == self.repo.tenant_id)
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        d, m, c, co = row
        return {
            "id": str(d.id),
            "nombre": d.nombre,
            "materia_nombre": m.nombre,
            "carrera_nombre": c.nombre,
            "cohorte_nombre": co.nombre,
        }
