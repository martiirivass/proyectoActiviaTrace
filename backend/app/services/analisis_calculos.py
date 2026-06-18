"""Pure computation functions for analisis module.

These functions have NO I/O dependencies — they receive plain data and return
structured results, making them fully testable without a database.
"""

import csv
import io
from dataclasses import dataclass, field
from uuid import UUID


# ===== Dataclasses for input/output of pure functions =====


@dataclass
class CalificacionData:
    """A single calificacion record (no DB dependency)."""
    entrada_padron_id: UUID
    materia_id: UUID
    actividad: str
    nota_numerica: float | None = None
    nota_textual: str | None = None
    aprobado: bool = False


@dataclass
class AlumnoData:
    """Alumno info from EntradaPadron."""
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    email: str | None = None
    comision: str | None = None
    regional: str | None = None


@dataclass
class UmbralData:
    """Umbral config for a materia."""
    umbral_pct: int = 60
    valores_aprobatorios: list[str] = field(default_factory=list)


@dataclass
class AtrasadoResult:
    """Result item for atrasados endpoint."""
    alumno_id: str
    alumno_nombre: str
    alumno_apellido: str
    email: str
    actividad: str
    nota: float | None = None
    causa: str = "actividad_faltante"  # "actividad_faltante" | "nota_bajo_umbral"


@dataclass
class RankingItem:
    """Ranking item."""
    alumno_id: str
    alumno_nombre: str
    alumno_apellido: str
    email: str
    comision: str | None
    aprobadas: int
    total: int
    porcentaje: float


@dataclass
class ActividadReporte:
    """Per-activity metrics in reporte rapido."""
    nombre: str
    alumnos_con_nota: int
    promedio: float | None
    aprobados: int
    desaprobados: int


@dataclass
class ReporteRapidoResult:
    """Consolidated metrics for reporte rapido."""
    total_alumnos: int
    total_actividades: int
    promedio_general: float | None
    total_aprobados: int
    total_desaprobados: int
    porcentaje_aprobacion: float | None
    actividades: list[ActividadReporte] = field(default_factory=list)


@dataclass
class NotaFinalItem:
    """Nota final per alumno."""
    alumno_id: str
    alumno_nombre: str
    alumno_apellido: str
    email: str
    comision: str | None
    actividades_consideradas: int
    nota_final: float | None
    actividades_detalle: list[dict] = field(default_factory=list)


@dataclass
class TpsSinCorregirItem:
    """TP sin corregir item."""
    alumno_nombre: str
    actividad: str
    fecha_finalizacion: str | None = None


# ===== 1.2 compute_atrasados =====


def compute_atrasados(
    calificaciones: list[CalificacionData],
    alumnos: list[AlumnoData],
    umbral: UmbralData,
    actividades_esperadas: list[str],
    busqueda: str | None = None,
) -> list[AtrasadoResult]:
    """Computar alumnos atrasados según RN-06.

    Un alumno está atrasado si:
    - Tiene actividades faltantes (sin registro de calificación)
    - Su nota registrada es inferior al umbral

    Args:
        calificaciones: Lista de calificaciones de la materia.
        alumnos: Lista de alumnos en el padrón de la materia.
        umbral: Configuración de umbral (umbral_pct, valores_aprobatorios).
        actividades_esperadas: Lista de nombres de actividades esperadas.
        busqueda: Filtro opcional por nombre/apellido (case-insensitive).

    Returns:
        Lista de AtrasadoResult.
    """
    # Build alumno lookup
    alumno_map = {str(a.entrada_padron_id): a for a in alumnos}

    # Group calificaciones by alumno
    calif_por_alumno: dict[str, dict[str, CalificacionData]] = {}
    for c in calificaciones:
        key = str(c.entrada_padron_id)
        if key not in calif_por_alumno:
            calif_por_alumno[key] = {}
        calif_por_alumno[key][c.actividad] = c

    resultados: list[AtrasadoResult] = []

    for alumno in alumnos:
        alumno_key = str(alumno.entrada_padron_id)
        calif_alumno = calif_por_alumno.get(alumno_key, {})

        for actividad in actividades_esperadas:
            cal = calif_alumno.get(actividad)

            if cal is None:
                # Actividad faltante
                resultados.append(AtrasadoResult(
                    alumno_id=str(alumno.entrada_padron_id),
                    alumno_nombre=alumno.nombre,
                    alumno_apellido=alumno.apellidos,
                    email=alumno.email,
                    actividad=actividad,
                    nota=None,
                    causa="actividad_faltante",
                ))
            elif not cal.aprobado:
                # Nota bajo umbral
                resultados.append(AtrasadoResult(
                    alumno_id=str(alumno.entrada_padron_id),
                    alumno_nombre=alumno.nombre,
                    alumno_apellido=alumno.apellidos,
                    email=alumno.email,
                    actividad=actividad,
                    nota=cal.nota_numerica,
                    causa="nota_bajo_umbral",
                ))

    # Apply search filter if specified
    if busqueda:
        busqueda_lower = busqueda.lower()
        resultados = [
            r for r in resultados
            if busqueda_lower in r.alumno_nombre.lower()
        ]

    return resultados


# ===== 1.3 compute_ranking =====


def compute_ranking(
    calificaciones: list[CalificacionData],
    alumnos: list[AlumnoData],
    actividades_esperadas: list[str],
) -> list[RankingItem]:
    """Generar ranking descendente por actividades aprobadas (RN-09).

    Args:
        calificaciones: Lista de calificaciones.
        alumnos: Lista de alumnos.
        actividades_esperadas: Lista de nombres de actividades.

    Returns:
        Ranking ordenado descendente por aprobadas.
    """
    alumno_map = {str(a.entrada_padron_id): a for a in alumnos}

    # Count aprobadas per alumno
    aprobadas_por_alumno: dict[str, int] = {}
    for c in calificaciones:
        key = str(c.entrada_padron_id)
        if key not in aprobadas_por_alumno:
            aprobadas_por_alumno[key] = 0
        if c.aprobado:
            aprobadas_por_alumno[key] += 1

    # Build ranking items, excluding those with 0
    ranking: list[RankingItem] = []
    total_actividades = len(actividades_esperadas)

    for alumno_key, count in aprobadas_por_alumno.items():
        if count < 1:
            continue  # RN-09: exclude 0 aprobadas
        alumno = alumno_map.get(alumno_key)
        if alumno is None:
            continue
        pct = (count / total_actividades * 100) if total_actividades > 0 else 0.0
        ranking.append(RankingItem(
            alumno_id=str(alumno.entrada_padron_id),
            alumno_nombre=alumno.nombre,
            alumno_apellido=alumno.apellidos,
            email=alumno.email,
            comision=alumno.comision,
            aprobadas=count,
            total=total_actividades,
            porcentaje=round(pct, 2),
        ))

    # Sort descending by aprobadas, then alphabetical by name
    ranking.sort(key=lambda x: (-x.aprobadas, x.alumno_nombre))
    return ranking


# ===== 1.4 compute_reporte_rapido =====


def compute_reporte_rapido(
    calificaciones: list[CalificacionData],
    alumnos: list[AlumnoData],
    actividades_esperadas: list[str],
) -> ReporteRapidoResult:
    """Generar métricas consolidadas por materia.

    Args:
        calificaciones: Lista de calificaciones.
        alumnos: Lista de alumnos.
        actividades_esperadas: Lista de nombres de actividades.

    Returns:
        ReporteRapidoResult con métricas consolidadas.
    """
    if not calificaciones or not actividades_esperadas:
        return ReporteRapidoResult(
            total_alumnos=len(alumnos),
            total_actividades=0,
            promedio_general=None,
            total_aprobados=0,
            total_desaprobados=0,
            porcentaje_aprobacion=None,
            actividades=[],
        )

    # Per-activity metrics
    actividad_metrics: dict[str, dict] = {}
    for act in actividades_esperadas:
        actividad_metrics[act] = {
            "alumnos_con_nota": 0,
            "suma_notas": 0.0,
            "aprobados": 0,
            "desaprobados": 0,
        }

    alumnos_unicos = {str(c.entrada_padron_id) for c in calificaciones}

    for c in calificaciones:
        if c.actividad not in actividad_metrics:
            continue
        am = actividad_metrics[c.actividad]
        if c.nota_numerica is not None:
            am["alumnos_con_nota"] += 1
            am["suma_notas"] += c.nota_numerica
        if c.aprobado:
            am["aprobados"] += 1
        else:
            am["desaprobados"] += 1

    # Build actividad reports
    actividades_reporte: list[ActividadReporte] = []
    for act in actividades_esperadas:
        am = actividad_metrics[act]
        if am["alumnos_con_nota"] > 0:
            prom = round(am["suma_notas"] / am["alumnos_con_nota"], 2)
        else:
            prom = None
        actividades_reporte.append(ActividadReporte(
            nombre=act,
            alumnos_con_nota=am["alumnos_con_nota"],
            promedio=prom,
            aprobados=am["aprobados"],
            desaprobados=am["desaprobados"],
        ))

    # General metrics
    notas_numericas = [c.nota_numerica for c in calificaciones if c.nota_numerica is not None]
    promedio_general = round(sum(notas_numericas) / len(notas_numericas), 2) if notas_numericas else None

    total_alumnos_unique = len(alumnos_unicos)
    total_aprobados = sum(1 for c in calificaciones if c.aprobado)
    calificaciones_con_decision = sum(1 for c in calificaciones if c.aprobado is not None)

    # Count unique alumnos that have at least one aprobado
    alumnos_con_aprobado = set()
    for c in calificaciones:
        if c.aprobado:
            alumnos_con_aprobado.add(str(c.entrada_padron_id))

    # Count unique alumnos that have no aprobados (but have calificaciones)
    alumnos_sin_aprobado = alumnos_unicos - alumnos_con_aprobado

    porcentaje_aprobacion = round(
        len(alumnos_con_aprobado) / len(alumnos_unicos) * 100, 2
    ) if alumnos_unicos else None

    return ReporteRapidoResult(
        total_alumnos=total_alumnos_unique,
        total_actividades=len(actividades_esperadas),
        promedio_general=promedio_general,
        total_aprobados=len(alumnos_con_aprobado),
        total_desaprobados=len(alumnos_sin_aprobado),
        porcentaje_aprobacion=porcentaje_aprobacion,
        actividades=actividades_reporte,
    )


# ===== 1.5 compute_nota_final =====


def compute_nota_final(
    calificaciones: list[CalificacionData],
    alumnos: list[AlumnoData],
) -> list[NotaFinalItem]:
    """Calcular nota final como promedio de notas numéricas por alumno.

    Args:
        calificaciones: Lista de calificaciones.
        alumnos: Lista de alumnos.

    Returns:
        Lista de NotaFinalItem.
    """
    alumno_map = {str(a.entrada_padron_id): a for a in alumnos}

    # Group by alumno
    notas_por_alumno: dict[str, dict] = {}
    for c in calificaciones:
        key = str(c.entrada_padron_id)
        if key not in notas_por_alumno:
            notas_por_alumno[key] = {"numericas": [], "detalle": []}
        notas_por_alumno[key]["detalle"].append({
            "actividad": c.actividad,
            "nota_numerica": c.nota_numerica,
            "nota_textual": c.nota_textual,
        })
        if c.nota_numerica is not None:
            notas_por_alumno[key]["numericas"].append(c.nota_numerica)

    resultados: list[NotaFinalItem] = []
    for alumno_key, data in notas_por_alumno.items():
        alumno = alumno_map.get(alumno_key)
        if alumno is None:
            continue

        numericas = data["numericas"]
        if numericas:
            nota_final = round(sum(numericas) / len(numericas), 2)
        else:
            nota_final = None

        resultados.append(NotaFinalItem(
            alumno_id=str(alumno.entrada_padron_id),
            alumno_nombre=alumno.nombre,
            alumno_apellido=alumno.apellidos,
            email=alumno.email,
            comision=alumno.comision,
            actividades_consideradas=len(numericas),
            nota_final=nota_final,
            actividades_detalle=data["detalle"],
        ))

    # Sort alphabetically
    resultados.sort(key=lambda x: x.alumno_nombre)
    return resultados


# ===== 1.6 compute_tps_sin_corregir =====


def compute_tps_sin_corregir(
    calificaciones: list[CalificacionData],
    alumnos: list[AlumnoData],
    reporte_finalizacion: dict[UUID, dict[str, str]],
) -> list[TpsSinCorregirItem]:
    """Computar TPs sin corregir.

    Cruza el reporte de finalización (actividades que el alumno finalizó)
    contra las calificaciones existentes. Si una actividad textual está
    en el reporte pero no tiene calificación, se marca como sin corregir.

    RN-07: Incluye solo actividades textuales.
    RN-08: Actividades numéricas sin calificación NO se incluyen (no entregado).

    Args:
        calificaciones: Lista de calificaciones existentes.
        alumnos: Lista de alumnos.
        reporte_finalizacion: Dict de {entrada_padron_id: {actividad: estado}}.

    Returns:
        Lista de TpsSinCorregirItem.
    """
    alumno_map = {str(a.entrada_padron_id): a for a in alumnos}

    # Build set of (alumno_key, actividad) that have calificaciones
    calificaciones_existentes: set[tuple[str, str]] = set()
    for c in calificaciones:
        calificaciones_existentes.add((str(c.entrada_padron_id), c.actividad))

    resultados: list[TpsSinCorregirItem] = []

    for entrada_id, actividades in reporte_finalizacion.items():
        entrada_key = str(entrada_id) if not isinstance(entrada_id, str) else entrada_id
        alumno = alumno_map.get(entrada_key)
        if alumno is None:
            continue

        for actividad, _estado in actividades.items():
            # Only include if NOT in calificaciones existentes
            if (entrada_key, actividad) not in calificaciones_existentes:
                resultados.append(TpsSinCorregirItem(
                    alumno_nombre=f"{alumno.nombre} {alumno.apellidos}",
                    actividad=actividad,
                    fecha_finalizacion=None,
                ))

    return resultados


# ===== 1.7 CSV builder =====


def build_csv_string(rows: list[dict], columns: list[str]) -> str:
    """Build CSV string from list of dicts with anti-CSV-injection escaping.

    Args:
        rows: Lista de diccionarios con datos.
        columns: Nombres de columnas en orden.

    Returns:
        String CSV.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(columns)

    # Write data rows
    for row in rows:
        values = []
        for col in columns:
            val = row.get(col, "")
            if val is None:
                val = ""
            val_str = str(val)
            # Anti-CSV-injection: escape values starting with dangerous chars
            if val_str and val_str[0] in ("=", "+", "-", "@"):
                val_str = "\t" + val_str
            values.append(val_str)
        writer.writerow(values)

    return output.getvalue()
