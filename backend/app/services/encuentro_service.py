from datetime import date, timedelta
from uuid import UUID

from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import EstadoInstancia, InstanciaEncuentro
from app.repositories.encuentro_repository import (
    InstanciaEncuentroRepository,
    SlotEncuentroRepository,
)
from app.schemas.encuentros import (
    EncuentroAdminListResponse,
    EncuentroAdminResponse,
    InstanciaListResponse,
    InstanciaResponse,
    SlotEncuentroCreate,
    SlotEncuentroResponse,
)
from app.services.audit_service import AuditService

DIAS_MAP = {
    "Lunes": 0,
    "Martes": 1,
    "Miércoles": 2,
    "Jueves": 3,
    "Viernes": 4,
    "Sábado": 5,
    "Domingo": 6,
}


class EncuentroService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.slot_repo = SlotEncuentroRepository(session, tenant_id)
        self.instancia_repo = InstanciaEncuentroRepository(session, tenant_id)
        self.session = session
        self.tenant_id = tenant_id
        self.audit = AuditService(session)

    async def crear_slot(
        self,
        data: SlotEncuentroCreate,
        actor_id: UUID,
    ) -> dict:
        """Create a slot (recurrent or unique) and generate its instancias."""
        # Determine mode
        es_unico = data.fecha_unica is not None

        if es_unico:
            # Modo único
            slot_data = data.model_dump(exclude={"dia_semana", "fecha_inicio"})
            slot_data["cant_semanas"] = 0
            slot_data["vig_desde"] = data.fecha_unica
            slot_data["vig_hasta"] = data.fecha_unica
            slot_data["dia_semana"] = None
            slot_data["fecha_inicio"] = None

            slot = await self.slot_repo.create(**slot_data)

            # Generate single instancia
            instancias_data = [{
                "slot_id": slot.id,
                "materia_id": data.materia_id,
                "fecha": data.fecha_unica,
                "hora": data.hora,
                "titulo": data.titulo,
                "estado": EstadoInstancia.PROGRAMADO,
                "meet_url": data.meet_url,
            }]
            instancias = await self.instancia_repo.bulk_create_instancias(instancias_data)
            instancias_creadas = len(instancias)
        else:
            # Modo recurrente
            if data.cant_semanas <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Para modo recurrente, cant_semanas debe ser mayor a 0",
                )
            if not data.dia_semana or not data.fecha_inicio:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Para modo recurrente se requiere dia_semana y fecha_inicio",
                )

            vig_hasta = data.fecha_inicio + timedelta(weeks=data.cant_semanas - 1)
            # Adjust to the correct day of week of the last week
            # Actually vig_hasta just needs to be the last date of the series
            # Let's calculate: fecha_inicio + (cant_semanas - 1) * 7 days
            ultima_fecha = data.fecha_inicio + timedelta(weeks=data.cant_semanas - 1)

            slot_data = data.model_dump()
            slot_data["vig_desde"] = data.fecha_inicio
            slot_data["vig_hasta"] = ultima_fecha
            slot_data["fecha_unica"] = None

            slot = await self.slot_repo.create(**slot_data)

            # Generate N instancias
            instancias_data = []
            for i in range(data.cant_semanas):
                inst_fecha = data.fecha_inicio + timedelta(weeks=i)
                # Verify it matches the specified day of week
                target_dow = DIAS_MAP.get(data.dia_semana, -1)
                if target_dow >= 0 and inst_fecha.weekday() != target_dow:
                    # Adjust to the correct day
                    diff = target_dow - inst_fecha.weekday()
                    inst_fecha += timedelta(days=diff)

                instancias_data.append({
                    "slot_id": slot.id,
                    "materia_id": data.materia_id,
                    "fecha": inst_fecha,
                    "hora": data.hora,
                    "titulo": data.titulo,
                    "estado": EstadoInstancia.PROGRAMADO,
                    "meet_url": data.meet_url,
                })

            instancias = await self.instancia_repo.bulk_create_instancias(instancias_data)
            instancias_creadas = len(instancias)

        # Audit
        await self.audit.log(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion="ENCUENTRO_CREAR",
            materia_id=data.materia_id,
            detalle={
                "slot_id": str(slot.id),
                "modo": "unico" if es_unico else "recurrente",
                "instancias_creadas": instancias_creadas,
                "titulo": data.titulo,
            },
            filas_afectadas=instancias_creadas,
        )

        return {
            "slot_id": slot.id,
            "instancias_creadas": instancias_creadas,
        }

    async def editar_instancia(
        self,
        instancia_id: UUID,
        estado: str | None = None,
        meet_url: str | None = None,
        video_url: str | None = None,
        comentario: str | None = None,
        actor_id: UUID | None = None,
    ) -> InstanciaResponse:
        """Edit an instancia's estado, meet_url, video_url, comentario."""
        instancia = await self.instancia_repo.get(instancia_id)
        if not instancia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instancia no encontrada",
            )

        current_estado = instancia.estado

        if estado:
            nuevo_estado = EstadoInstancia(estado)

            # Validate video_url only when estado=Realizado
            if video_url and nuevo_estado != EstadoInstancia.REALIZADO:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="video_url solo puede establecerse cuando el estado es Realizado",
                )

            # Only validate transition if estado actually changes
            if nuevo_estado != current_estado:
                transiciones_validas = {
                    EstadoInstancia.PROGRAMADO: [EstadoInstancia.REALIZADO, EstadoInstancia.CANCELADO],
                    EstadoInstancia.REALIZADO: [EstadoInstancia.CANCELADO],
                    EstadoInstancia.CANCELADO: [EstadoInstancia.PROGRAMADO],
                }
                permitidos = transiciones_validas.get(current_estado, [])

                if nuevo_estado not in permitidos:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Transición no permitida de {current_estado.value} a {nuevo_estado.value}",
                    )

            instancia.estado = nuevo_estado

        if meet_url is not None:
            instancia.meet_url = meet_url
        if video_url is not None:
            instancia.video_url = video_url
        if comentario is not None:
            instancia.comentario = comentario

        await self.session.flush()
        await self.session.refresh(instancia)

        # Audit
        if actor_id:
            await self.audit.log(
                tenant_id=self.tenant_id,
                actor_id=actor_id,
                accion="ENCUENTRO_EDITAR",
                materia_id=instancia.materia_id,
                detalle={
                    "instancia_id": str(instancia_id),
                    "estado_anterior": current_estado.value if hasattr(current_estado, "value") else str(current_estado),
                    "estado_nuevo": instancia.estado.value if hasattr(instancia.estado, "value") else str(instancia.estado),
                },
            )

        return InstanciaResponse.model_validate(instancia)

    async def listar_instancias_por_slot(self, slot_id: UUID) -> InstanciaListResponse:
        slot = await self.slot_repo.get(slot_id)
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot no encontrado",
            )

        instancias = await self.instancia_repo.list_by_slot(slot_id)
        items = [InstanciaResponse.model_validate(i) for i in instancias]
        return InstanciaListResponse(items=items, total=len(items))

    async def exportar_html(self, materia_id: UUID) -> Response:
        from app.models.instancia_encuentro import InstanciaEncuentro
        from sqlalchemy import select

        stmt = (
            select(InstanciaEncuentro)
            .where(
                InstanciaEncuentro.tenant_id == self.tenant_id,
                InstanciaEncuentro.materia_id == materia_id,
                InstanciaEncuentro.is_deleted == False,
                InstanciaEncuentro.estado.in_([EstadoInstancia.PROGRAMADO, EstadoInstancia.REALIZADO]),
            )
            .order_by(InstanciaEncuentro.fecha.asc())
        )
        result = await self.session.execute(stmt)
        instancias = list(result.scalars().all())

        if not instancias:
            html = "<p>No hay encuentros programados</p>"
        else:
            rows_html = ""
            for inst in instancias:
                meet_link = f'<a href="{inst.meet_url}" target="_blank">Encuentro</a>' if inst.meet_url else "—"
                video_link = f'<a href="{inst.video_url}" target="_blank">Grabación</a>' if inst.video_url else "—"
                rows_html += (
                    f"<tr>"
                    f"<td>{inst.fecha.isoformat()}</td>"
                    f"<td>{inst.hora.strftime('%H:%M')}</td>"
                    f"<td>{inst.titulo}</td>"
                    f"<td>{meet_link}</td>"
                    f"<td>{video_link}</td>"
                    f"</tr>\n"
                )

            html = (
                '<table class="encuentros-table">\n'
                "<thead>\n"
                "<tr><th>Fecha</th><th>Hora</th><th>Título</th><th>Encuentro</th><th>Grabación</th></tr>\n"
                "</thead>\n"
                f"<tbody>\n{rows_html}</tbody>\n"
                "</table>"
            )

        return Response(content=html, media_type="text/html; charset=utf-8")

    async def listar_admin(
        self,
        materia_id: UUID | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        estado: str | None = None,
        asignacion_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> EncuentroAdminListResponse:
        from app.models.asignacion import Asignacion
        from app.models.materia import Materia
        from app.models.slot_encuentro import SlotEncuentro
        from app.models.user import User
        from sqlalchemy import select

        # Base query with joins
        base_where = [
            InstanciaEncuentro.tenant_id == self.tenant_id,
            InstanciaEncuentro.is_deleted == False,
        ]
        if materia_id:
            base_where.append(InstanciaEncuentro.materia_id == materia_id)
        if fecha_desde:
            base_where.append(InstanciaEncuentro.fecha >= fecha_desde)
        if fecha_hasta:
            base_where.append(InstanciaEncuentro.fecha <= fecha_hasta)
        if estado:
            base_where.append(InstanciaEncuentro.estado == estado)

        join_slot = asignacion_id is not None

        # If filtering by asignacion_id, need to join SlotEncuentro
        if join_slot:
            # We use SlotEncuentro as the join table
            # But actually the join path is: InstanciaEncuentro.slot_id -> SlotEncuentro.id -> SlotEncuentro.asignacion_id
            # For instancias without slot (shouldn't happen but guard), use LEFT JOIN
            pass

        # Count
        from sqlalchemy import func as sa_func

        count_stmt = (
            select(sa_func.count(InstanciaEncuentro.id))
            .where(*base_where)
        )
        if join_slot:
            count_stmt = count_stmt.join(
                SlotEncuentro,
                InstanciaEncuentro.slot_id == SlotEncuentro.id,
                isouter=True,
            ).where(SlotEncuentro.asignacion_id == asignacion_id)

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Data query with joins for names
        data_stmt = (
            select(
                InstanciaEncuentro,
                Materia.nombre.label("materia_nombre"),
                User.nombre.label("user_nombre"),
                User.apellido.label("user_apellido"),
            )
            .join(Materia, InstanciaEncuentro.materia_id == Materia.id)
            .join(Asignacion, Materia.id == Asignacion.materia_id, isouter=True)
            .join(User, Asignacion.usuario_id == User.id, isouter=True)
            .where(*base_where)
            .order_by(InstanciaEncuentro.fecha.desc())
            .offset(offset)
            .limit(limit)
        )
        if join_slot:
            data_stmt = data_stmt.join(
                SlotEncuentro,
                InstanciaEncuentro.slot_id == SlotEncuentro.id,
                isouter=True,
            ).where(SlotEncuentro.asignacion_id == asignacion_id)

        data_result = await self.session.execute(data_stmt)
        rows = data_result.all()

        items = []
        for row in rows:
            inst = row[0]
            items.append(EncuentroAdminResponse(
                id=inst.id,
                fecha=inst.fecha,
                hora=inst.hora,
                titulo=inst.titulo,
                estado=inst.estado.value if hasattr(inst.estado, "value") else str(inst.estado),
                meet_url=inst.meet_url,
                video_url=inst.video_url,
                materia_id=inst.materia_id,
                materia_nombre=row.materia_nombre or "",
                docente_nombre=f"{row.user_nombre or ''} {row.user_apellido or ''}",
                slot_id=inst.slot_id,
            ))

        return EncuentroAdminListResponse(items=items, total=total)
