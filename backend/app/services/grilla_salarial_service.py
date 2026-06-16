from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import (
    SALARIO_BASE_CREAR,
    SALARIO_BASE_ELIMINAR,
    SALARIO_BASE_MODIFICAR,
    SALARIO_PLUS_CREAR,
    SALARIO_PLUS_ELIMINAR,
    SALARIO_PLUS_MODIFICAR,
)
from app.repositories.grilla_salarial_repository import (
    SalarioBaseRepository,
    SalarioPlusRepository,
)
from app.schemas.liquidaciones import (
    SalarioBaseCreate,
    SalarioBaseResponse,
    SalarioBaseUpdate,
    SalarioPlusCreate,
    SalarioPlusResponse,
    SalarioPlusUpdate,
)
from app.services.audit_service import AuditService


class GrillaSalarialService:
    def __init__(self, session: AsyncSession, tenant_id: UUID, actor_id: UUID):
        self.base_repo = SalarioBaseRepository(session, tenant_id)
        self.plus_repo = SalarioPlusRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.audit = AuditService(session)

    # ── SalarioBase ────────────────────────────────────────────────────────

    async def listar_base(
        self,
        rol: str | None = None,
        vigente: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[SalarioBaseResponse]:
        filters = {}
        if rol is not None:
            filters["rol"] = rol

        if vigente:
            from datetime import date
            today = date.today()
            if rol:
                base = await self.base_repo.find_vigente_base_by_rol(rol, today)
                items = [base] if base else []
            else:
                # No specific rol → list all and filter vigentes in-memory
                all_items = await self.base_repo.list_base(offset=offset, limit=limit, **filters)
                items = [
                    b for b in all_items
                    if b.desde <= today and (b.hasta is None or b.hasta >= today)
                ]
        else:
            items = await self.base_repo.list_base(offset=offset, limit=limit, **filters)

        return [SalarioBaseResponse.model_validate(b) for b in items]

    async def obtener_base(self, id: UUID) -> SalarioBaseResponse:
        base = await self.base_repo.get_base(id)
        if not base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salario base no encontrado",
            )
        return SalarioBaseResponse.model_validate(base)

    async def crear_base(self, data: SalarioBaseCreate) -> SalarioBaseResponse:
        # Check unique constraint: same (rol, desde) for this tenant
        existing = await self.base_repo.list_base(rol=data.rol, desde=data.desde)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un SalarioBase para rol {data.rol} con fecha desde {data.desde}",
            )

        base = await self.base_repo.create_base(
            rol=data.rol,
            monto=data.monto,
            desde=data.desde,
            hasta=data.hasta,
        )

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=SALARIO_BASE_CREAR,
            detalle={
                "salario_base_id": str(base.id),
                "rol": data.rol,
                "monto": str(data.monto),
                "desde": str(data.desde),
            },
        )

        return SalarioBaseResponse.model_validate(base)

    async def editar_base(self, id: UUID, data: SalarioBaseUpdate) -> SalarioBaseResponse:
        base = await self.base_repo.get_base(id)
        if not base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salario base no encontrado",
            )

        update_kwargs = {
            k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None
        }
        if not update_kwargs:
            return SalarioBaseResponse.model_validate(base)

        updated = await self.base_repo.update_base(id, **update_kwargs)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=SALARIO_BASE_MODIFICAR,
            detalle={
                "salario_base_id": str(id),
                "campos_actualizados": list(update_kwargs.keys()),
            },
        )

        return SalarioBaseResponse.model_validate(updated)

    async def eliminar_base(self, id: UUID) -> None:
        base = await self.base_repo.get_base(id)
        if not base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salario base no encontrado",
            )

        await self.base_repo.soft_delete_base(id)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=SALARIO_BASE_ELIMINAR,
            detalle={"salario_base_id": str(id)},
        )

    # ── SalarioPlus ────────────────────────────────────────────────────────

    async def listar_plus(
        self,
        grupo: str | None = None,
        rol: str | None = None,
        vigente: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[SalarioPlusResponse]:
        filters = {}
        if grupo is not None:
            filters["grupo"] = grupo
        if rol is not None:
            filters["rol"] = rol

        if vigente:
            from datetime import date
            today = date.today()
            if rol:
                items = await self.plus_repo.list_vigentes_plus_by_rol(rol, today)
            else:
                all_items = await self.plus_repo.list_plus(offset=offset, limit=limit, **filters)
                items = [
                    p for p in all_items
                    if p.desde <= today and (p.hasta is None or p.hasta >= today)
                ]
        else:
            items = await self.plus_repo.list_plus(offset=offset, limit=limit, **filters)

        return [SalarioPlusResponse.model_validate(p) for p in items]

    async def obtener_plus(self, id: UUID) -> SalarioPlusResponse:
        plus = await self.plus_repo.get_plus(id)
        if not plus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salario plus no encontrado",
            )
        return SalarioPlusResponse.model_validate(plus)

    async def crear_plus(self, data: SalarioPlusCreate) -> SalarioPlusResponse:
        # Check unique constraint: same (grupo, rol, desde) for this tenant
        existing = await self.plus_repo.list_plus(grupo=data.grupo, rol=data.rol, desde=data.desde)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un SalarioPlus para grupo {data.grupo}, rol {data.rol} con fecha desde {data.desde}",
            )

        plus = await self.plus_repo.create_plus(
            grupo=data.grupo,
            rol=data.rol,
            descripcion=data.descripcion,
            monto=data.monto,
            desde=data.desde,
            hasta=data.hasta,
        )

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=SALARIO_PLUS_CREAR,
            detalle={
                "salario_plus_id": str(plus.id),
                "grupo": data.grupo,
                "rol": data.rol,
                "monto": str(data.monto),
            },
        )

        return SalarioPlusResponse.model_validate(plus)

    async def editar_plus(self, id: UUID, data: SalarioPlusUpdate) -> SalarioPlusResponse:
        plus = await self.plus_repo.get_plus(id)
        if not plus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salario plus no encontrado",
            )

        update_kwargs = {
            k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None
        }
        if not update_kwargs:
            return SalarioPlusResponse.model_validate(plus)

        updated = await self.plus_repo.update_plus(id, **update_kwargs)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=SALARIO_PLUS_MODIFICAR,
            detalle={
                "salario_plus_id": str(id),
                "campos_actualizados": list(update_kwargs.keys()),
            },
        )

        return SalarioPlusResponse.model_validate(updated)

    async def eliminar_plus(self, id: UUID) -> None:
        plus = await self.plus_repo.get_plus(id)
        if not plus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salario plus no encontrado",
            )

        await self.plus_repo.soft_delete_plus(id)

        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            accion=SALARIO_PLUS_ELIMINAR,
            detalle={"salario_plus_id": str(id)},
        )
