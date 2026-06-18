"""Service layer for analisis endpoints.

Orchestrates repository queries and delegates computation to pure functions.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.umbral_materia_repository import UmbralMateriaRepository
from app.schemas.analisis import (
    AtrasadoItem,
    AtrasadosResponse,
    NotaFinalItem,
    NotasFinalesResponse,
    RankingItem,
    RankingResponse,
    ReporteRapidoResponse,
    ActividadReporteItem,
    ActividadDetalleItem,
)


class AnalisisService:
    """Service for analisis and reporting operations."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = CalificacionRepository(session, tenant_id)
        self.umbral_repo = UmbralMateriaRepository(session, tenant_id)

    # --- 3.2 get_atrasados ---

    async def get_atrasados(
        self,
        materia_id: UUID,
        current_user_id: UUID,
        busqueda: str | None = None,
        es_scope_global: bool = False,
    ) -> AtrasadosResponse:
        """Get alumnos atrasados for a materia."""
        from app.services.analisis_calculos import (
            AlumnoData,
            CalificacionData,
            UmbralData,
            compute_atrasados,
        )

        # Get calificaciones with alumno data
        calificaciones_raw = await self.repo.get_calificaciones_with_alumno(materia_id)

        # Convert to pure data objects
        alumno_map: dict[str, AlumnoData] = {}
        calificaciones: list[CalificacionData] = []
        alumnos: list[AlumnoData] = []

        for row in calificaciones_raw:
            cal = CalificacionData(
                entrada_padron_id=row["entrada_padron_id"],
                materia_id=row["materia_id"],
                actividad=row["actividad"],
                nota_numerica=row["nota_numerica"],
                nota_textual=row["nota_textual"],
                aprobado=row["aprobado"],
            )
            calificaciones.append(cal)

            alumno_key = str(row["entrada_padron_id"])
            if alumno_key not in alumno_map:
                alumno = AlumnoData(
                    entrada_padron_id=row["entrada_padron_id"],
                    nombre=row["alumno_nombre"].split(" ")[0] if " " in row["alumno_nombre"] else row["alumno_nombre"],
                    apellidos=" ".join(row["alumno_nombre"].split(" ")[1:]) if " " in row["alumno_nombre"] else "",
                    email=row["email"],
                    comision=row["comision"],
                    regional=row["regional"],
                )
                alumno_map[alumno_key] = alumno
                alumnos.append(alumno)

        # Get actividades esperadas
        actividades_esperadas = await self.repo.get_actividades_by_materia(materia_id)

        # Get umbral (default to 60 if not configured)
        umbral = UmbralData(umbral_pct=60, valores_aprobatorios=[])

        # Compute
        result = compute_atrasados(
            calificaciones=calificaciones,
            alumnos=alumnos,
            umbral=umbral,
            actividades_esperadas=actividades_esperadas,
            busqueda=busqueda,
        )

        items = [
            AtrasadoItem(
                alumno_id=r.alumno_id,
                alumno_nombre=r.alumno_nombre,
                alumno_apellido=r.alumno_apellido,
                email=r.email,
                actividad=r.actividad,
                nota=r.nota,
                causa=r.causa,
            )
            for r in result
        ]

        return AtrasadosResponse(items=items, total=len(items))

    # --- 3.3 get_ranking ---

    async def get_ranking(
        self,
        materia_id: UUID,
    ) -> RankingResponse:
        """Get ranking of alumnos by approved activities."""
        from app.services.analisis_calculos import (
            AlumnoData,
            CalificacionData,
            compute_ranking,
        )

        calificaciones_raw = await self.repo.get_calificaciones_with_alumno(materia_id)

        alumno_map: dict[str, AlumnoData] = {}
        calificaciones: list[CalificacionData] = []
        alumnos: list[AlumnoData] = []

        for row in calificaciones_raw:
            cal = CalificacionData(
                entrada_padron_id=row["entrada_padron_id"],
                materia_id=row["materia_id"],
                actividad=row["actividad"],
                nota_numerica=row["nota_numerica"],
                nota_textual=row["nota_textual"],
                aprobado=row["aprobado"],
            )
            calificaciones.append(cal)

            alumno_key = str(row["entrada_padron_id"])
            if alumno_key not in alumno_map:
                alumno = AlumnoData(
                    entrada_padron_id=row["entrada_padron_id"],
                    nombre=row["alumno_nombre"].split(" ")[0],
                    apellidos=" ".join(row["alumno_nombre"].split(" ")[1:]),
                    email=row["email"],
                    comision=row["comision"],
                    regional=row["regional"],
                )
                alumno_map[alumno_key] = alumno
                alumnos.append(alumno)

        actividades_esperadas = await self.repo.get_actividades_by_materia(materia_id)

        result = compute_ranking(
            calificaciones=calificaciones,
            alumnos=alumnos,
            actividades_esperadas=actividades_esperadas,
        )

        items = [
            RankingItem(
                alumno_id=r.alumno_id,
                alumno_nombre=r.alumno_nombre,
                alumno_apellido=r.alumno_apellido,
                email=r.email,
                comision=r.comision,
                posicion=idx + 1,
                aprobadas=r.aprobadas,
                total=r.total,
                porcentaje=r.porcentaje,
            )
            for idx, r in enumerate(result)
        ]

        return RankingResponse(items=items, total=len(items))

    # --- 3.4 get_reportes_rapidos ---

    async def get_reportes_rapidos(self, materia_id: UUID) -> ReporteRapidoResponse:
        """Get consolidated metrics for a materia."""
        from app.services.analisis_calculos import (
            AlumnoData,
            CalificacionData,
            compute_reporte_rapido,
        )

        calificaciones_raw = await self.repo.get_calificaciones_with_alumno(materia_id)
        actividades_esperadas = await self.repo.get_actividades_by_materia(materia_id)

        alumno_map: dict[str, AlumnoData] = {}
        calificaciones: list[CalificacionData] = []
        alumnos: list[AlumnoData] = []

        for row in calificaciones_raw:
            cal = CalificacionData(
                entrada_padron_id=row["entrada_padron_id"],
                materia_id=row["materia_id"],
                actividad=row["actividad"],
                nota_numerica=row["nota_numerica"],
                nota_textual=row["nota_textual"],
                aprobado=row["aprobado"],
            )
            calificaciones.append(cal)

            alumno_key = str(row["entrada_padron_id"])
            if alumno_key not in alumno_map:
                alumno = AlumnoData(
                    entrada_padron_id=row["entrada_padron_id"],
                    nombre=row["alumno_nombre"].split(" ")[0],
                    apellidos=" ".join(row["alumno_nombre"].split(" ")[1:]),
                    email=row["email"],
                    comision=row["comision"],
                    regional=row["regional"],
                )
                alumno_map[alumno_key] = alumno
                alumnos.append(alumno)

        result = compute_reporte_rapido(
            calificaciones=calificaciones,
            alumnos=alumnos,
            actividades_esperadas=actividades_esperadas,
        )

        return ReporteRapidoResponse(
            total_alumnos=result.total_alumnos,
            total_actividades=result.total_actividades,
            promedio_general=result.promedio_general,
            total_aprobados=result.total_aprobados,
            total_desaprobados=result.total_desaprobados,
            porcentaje_aprobacion=result.porcentaje_aprobacion,
            actividades=[
                ActividadReporteItem(
                    nombre=a.nombre,
                    alumnos_con_nota=a.alumnos_con_nota,
                    promedio=a.promedio,
                    aprobados=a.aprobados,
                    desaprobados=a.desaprobados,
                )
                for a in result.actividades
            ],
        )

    # --- 3.5 get_notas_finales ---

    async def get_notas_finales(self, materia_id: UUID) -> NotasFinalesResponse:
        """Get final grades for each alumno in a materia."""
        from app.services.analisis_calculos import (
            AlumnoData,
            CalificacionData,
            compute_nota_final,
        )

        calificaciones_raw = await self.repo.get_calificaciones_with_alumno(materia_id)

        alumno_map: dict[str, AlumnoData] = {}
        calificaciones: list[CalificacionData] = []
        alumnos: list[AlumnoData] = []

        for row in calificaciones_raw:
            cal = CalificacionData(
                entrada_padron_id=row["entrada_padron_id"],
                materia_id=row["materia_id"],
                actividad=row["actividad"],
                nota_numerica=row["nota_numerica"],
                nota_textual=row["nota_textual"],
                aprobado=row["aprobado"],
            )
            calificaciones.append(cal)

            alumno_key = str(row["entrada_padron_id"])
            if alumno_key not in alumno_map:
                alumno = AlumnoData(
                    entrada_padron_id=row["entrada_padron_id"],
                    nombre=row["alumno_nombre"].split(" ")[0],
                    apellidos=" ".join(row["alumno_nombre"].split(" ")[1:]),
                    email=row["email"],
                    comision=row["comision"],
                    regional=row["regional"],
                )
                alumno_map[alumno_key] = alumno
                alumnos.append(alumno)

        result = compute_nota_final(
            calificaciones=calificaciones,
            alumnos=alumnos,
        )

        items = [
            NotaFinalItem(
                alumno_id=r.alumno_id,
                alumno_nombre=r.alumno_nombre,
                alumno_apellido=r.alumno_apellido,
                email=r.email,
                comision=r.comision,
                actividades_consideradas=r.actividades_consideradas,
                nota_final=r.nota_final,
                actividades=[
                    ActividadDetalleItem(
                        nombre=d["actividad"],
                        nota=d["nota_numerica"] if d["nota_numerica"] is not None else d["nota_textual"],
                    )
                    for d in r.actividades_detalle
                ],
            )
            for r in result
        ]

        return NotasFinalesResponse(items=items, total=len(items))

    # --- 3.6 exportar_tps_sin_corregir ---

    async def exportar_tps_sin_corregir(
        self,
        materia_id: UUID,
        reporte_finalizacion_data: dict[UUID, dict[str, str]] | None = None,
    ) -> str:
        """Export TPs sin corregir as CSV string.

        If reporte_finalizacion_data is provided, uses it directly.
        Otherwise, returns empty CSV with header.
        """
        from app.services.analisis_calculos import (
            AlumnoData,
            CalificacionData,
            compute_tps_sin_corregir,
            build_csv_string,
        )

        calificaciones_raw = await self.repo.get_calificaciones_with_alumno(materia_id)

        alumno_map: dict[str, AlumnoData] = {}
        calificaciones: list[CalificacionData] = []
        alumnos: list[AlumnoData] = []

        for row in calificaciones_raw:
            cal = CalificacionData(
                entrada_padron_id=row["entrada_padron_id"],
                materia_id=row["materia_id"],
                actividad=row["actividad"],
                nota_numerica=row["nota_numerica"],
                nota_textual=row["nota_textual"],
                aprobado=row["aprobado"],
            )
            calificaciones.append(cal)

            alumno_key = str(row["entrada_padron_id"])
            if alumno_key not in alumno_map:
                alumno = AlumnoData(
                    entrada_padron_id=row["entrada_padron_id"],
                    nombre=row["alumno_nombre"].split(" ")[0],
                    apellidos=" ".join(row["alumno_nombre"].split(" ")[1:]),
                    email=row["email"],
                    comision=row["comision"],
                    regional=row["regional"],
                )
                alumno_map[alumno_key] = alumno
                alumnos.append(alumno)

        reporte = reporte_finalizacion_data or {}
        result = compute_tps_sin_corregir(
            calificaciones=calificaciones,
            alumnos=alumnos,
            reporte_finalizacion=reporte,
        )

        rows = [
            {"alumno_nombre": r.alumno_nombre, "actividad": r.actividad}
            for r in result
        ]

        return build_csv_string(rows, columns=["alumno_nombre", "actividad"])

    # --- 3.7 get_monitor_general ---

    async def get_monitor_general(
        self,
        materia_id: UUID | None = None,
        regional: str | None = None,
        comision: str | None = None,
        busqueda: str | None = None,
        estado: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """Get monitor general with filtering and pagination.

        For COORDINADOR/ADMIN - scope global.
        """
        calificaciones_raw = await self.repo.get_calificaciones_with_alumno(materia_id)

        # Build monitor items grouped by alumno
        from collections import defaultdict

        alumno_data: dict[str, dict] = {}
        for row in calificaciones_raw:
            key = str(row["entrada_padron_id"])
            if key not in alumno_data:
                alumno_data[key] = {
                    "alumno_nombre": row["alumno_nombre"],
                    "email": row["email"],
                    "comision": row["comision"],
                    "regional": row["regional"],
                    "total_actividades": 0,
                    "aprobadas": 0,
                    "desaprobadas": 0,
                }
            alumno_data[key]["total_actividades"] += 1
            if row["aprobado"]:
                alumno_data[key]["aprobadas"] += 1
            else:
                alumno_data[key]["desaprobadas"] += 1

        # Apply filters
        items_list = list(alumno_data.values())

        if regional:
            items_list = [i for i in items_list if i["regional"] == regional]
        if comision:
            items_list = [i for i in items_list if i["comision"] == comision]
        if busqueda:
            busqueda_lower = busqueda.lower()
            items_list = [
                i for i in items_list
                if busqueda_lower in i["alumno_nombre"].lower()
            ]
        if estado == "atrasado":
            items_list = [i for i in items_list if i["desaprobadas"] > 0 or i["total_actividades"] == 0]

        # Compute derived fields
        for item in items_list:
            item["pendientes"] = item["total_actividades"] - item["aprobadas"] - item["desaprobadas"]
            item["porcentaje_avance"] = round(
                item["aprobadas"] / item["total_actividades"] * 100, 2
            ) if item["total_actividades"] > 0 else 0.0

        # Sort by nombre
        items_list.sort(key=lambda x: x["alumno_nombre"])

        total = len(items_list)
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        page_items = items_list[start:end]

        next_page = page + 1 if end < total else None
        prev_page = page - 1 if page > 1 else None

        return {
            "items": page_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "next_page": next_page,
            "prev_page": prev_page,
        }

    # --- 3.8 get_monitor_seguimiento ---

    async def get_monitor_seguimiento(
        self,
        current_user_id: UUID,
        alumno_id: UUID | None = None,
        email: str | None = None,
        comision: str | None = None,
        regional: str | None = None,
        actividad: str | None = None,
        min_actividades: int | None = None,
    ) -> dict:
        """Get monitor seguimiento for TUTOR/PROFESOR - scope propio.

        Filters by user's assignments.
        """
        from app.models.asignacion import Asignacion
        from sqlalchemy import select

        # Get user's materia assignments
        stmt = (
            select(Asignacion.materia_id)
            .where(
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.usuario_id == current_user_id,
                Asignacion.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        materia_ids = [row[0] for row in result.all()]

        if not materia_ids:
            return {"items": [], "total": 0, "alumno_count": 0}

        all_items = []
        for mid in materia_ids:
            calificaciones_raw = await self.repo.get_calificaciones_with_alumno(mid)
            all_items.extend(calificaciones_raw)

        # Build monitor items grouped by alumno
        from collections import defaultdict

        alumno_data: dict[str, dict] = {}
        for row in all_items:
            key = str(row["entrada_padron_id"])
            if key not in alumno_data:
                alumno_data[key] = {
                    "entrada_padron_id": row["entrada_padron_id"],
                    "alumno_nombre": row["alumno_nombre"],
                    "email": row["email"],
                    "comision": row["comision"],
                    "regional": row["regional"],
                    "total_actividades": 0,
                    "aprobadas": 0,
                    "desaprobadas": 0,
                }
            alumno_data[key]["total_actividades"] += 1
            if row["aprobado"]:
                alumno_data[key]["aprobadas"] += 1
            else:
                alumno_data[key]["desaprobadas"] += 1

        items_list = list(alumno_data.values())

        # Apply filters
        if alumno_id:
            items_list = [i for i in items_list if i["entrada_padron_id"] == alumno_id]
        if email:
            items_list = [i for i in items_list if i["email"] == email]
        if comision:
            items_list = [i for i in items_list if i["comision"] == comision]
        if regional:
            items_list = [i for i in items_list if i["regional"] == regional]
        if min_actividades is not None:
            items_list = [i for i in items_list if i["total_actividades"] >= min_actividades]

        # Compute derived fields
        for item in items_list:
            item["pendientes"] = item["total_actividades"] - item["aprobadas"] - item["desaprobadas"]
            item["porcentaje_aprobacion"] = round(
                item["aprobadas"] / item["total_actividades"] * 100, 2
            ) if item["total_actividades"] > 0 else 0.0

        items_list.sort(key=lambda x: x["alumno_nombre"])

        return {
            "items": items_list,
            "total": len(items_list),
            "alumno_count": len(items_list),
        }

    # --- 3.9 get_monitor_seguimiento_extendido ---

    async def get_monitor_seguimiento_extendido(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        alumno_id: UUID | None = None,
        email: str | None = None,
        comision: str | None = None,
        regional: str | None = None,
        actividad: str | None = None,
        min_actividades: int | None = None,
    ) -> dict:
        """Get monitor seguimiento extendido for COORDINADOR/ADMIN - scope global.

        Same as monitor_seguimiento but with date range filters and global scope.
        """
        calificaciones_raw = await self.repo.get_all_calificaciones_with_alumno()

        # Build monitor items grouped by alumno
        from collections import defaultdict

        alumno_data: dict[str, dict] = {}
        for row in calificaciones_raw:
            key = str(row["entrada_padron_id"])
            if key not in alumno_data:
                alumno_data[key] = {
                    "entrada_padron_id": row["entrada_padron_id"],
                    "alumno_nombre": row["alumno_nombre"],
                    "email": row["email"],
                    "comision": row["comision"],
                    "regional": row["regional"],
                    "total_actividades": 0,
                    "aprobadas": 0,
                    "desaprobadas": 0,
                }
            alumno_data[key]["total_actividades"] += 1
            if row["aprobado"]:
                alumno_data[key]["aprobadas"] += 1
            else:
                alumno_data[key]["desaprobadas"] += 1

        items_list = list(alumno_data.values())

        # Apply filters
        if alumno_id:
            items_list = [i for i in items_list if i["entrada_padron_id"] == alumno_id]
        if email:
            items_list = [i for i in items_list if i["email"] == email]
        if comision:
            items_list = [i for i in items_list if i["comision"] == comision]
        if regional:
            items_list = [i for i in items_list if i["regional"] == regional]
        if min_actividades is not None:
            items_list = [i for i in items_list if i["total_actividades"] >= min_actividades]

        for item in items_list:
            item["pendientes"] = item["total_actividades"] - item["aprobadas"] - item["desaprobadas"]
            item["porcentaje_aprobacion"] = round(
                item["aprobadas"] / item["total_actividades"] * 100, 2
            ) if item["total_actividades"] > 0 else 0.0

        items_list.sort(key=lambda x: x["alumno_nombre"])

        return {
            "items": items_list,
            "total": len(items_list),
            "alumno_count": len(items_list),
        }
