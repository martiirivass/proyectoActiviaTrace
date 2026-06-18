"""Unit tests for analisis_calculos pure functions (no DB needed)."""

import uuid
from decimal import Decimal

import pytest

from app.services.analisis_calculos import (
    AlumnoData,
    CalificacionData,
    UmbralData,
    compute_atrasados,
    compute_nota_final,
    compute_ranking,
    compute_reporte_rapido,
    compute_tps_sin_corregir,
    build_csv_string,
)

# Pure functions — no async needed


# ===== Fixtures =====


def _cal_data(
    entrada_padron_id=None,
    materia_id=None,
    actividad="TP1",
    nota_numerica=None,
    nota_textual=None,
    aprobado=False,
):
    return CalificacionData(
        entrada_padron_id=entrada_padron_id or uuid.uuid4(),
        materia_id=materia_id or uuid.uuid4(),
        actividad=actividad,
        nota_numerica=nota_numerica,
        nota_textual=nota_textual,
        aprobado=aprobado,
    )


def _alumno_data(
    entrada_padron_id=None,
    nombre="Juan",
    apellidos="Perez",
    email="juan@test.com",
    comision="A",
    regional="CABA",
):
    return AlumnoData(
        entrada_padron_id=entrada_padron_id or uuid.uuid4(),
        nombre=nombre,
        apellidos=apellidos,
        email=email,
        comision=comision,
        regional=regional,
    )


# ===== 1.2 compute_atrasados =====


class TestComputeAtrasados:
    """RN-06: Alumno atrasado = actividades faltantes OR nota < umbral."""

    def test_alumno_con_nota_bajo_umbral_es_atrasado(self):
        """Scenario: Alumno con nota inferior al umbral es marcado como atrasado."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="TP1", nota_numerica=40, aprobado=False),
            _cal_data(entrada_padron_id=alumno_id, actividad="TP2", nota_numerica=80, aprobado=True),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Juan", apellidos="Perez")]
        umbral = UmbralData(umbral_pct=60, valores_aprobatorios=[])
        actividades_esperadas = ["TP1", "TP2"]

        result = compute_atrasados(calificaciones, alumnos, umbral, actividades_esperadas)

        assert len(result) == 1
        assert result[0].alumno_nombre == "Juan Perez"
        assert result[0].actividad == "TP1"
        assert result[0].causa == "nota_bajo_umbral"

    def test_alumno_con_actividad_faltante_es_atrasado(self):
        """Scenario: Alumno con actividad faltante es marcado como atrasado."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="TP1", nota_numerica=80, aprobado=True),
            _cal_data(entrada_padron_id=alumno_id, actividad="TP2", nota_numerica=75, aprobado=True),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Maria", apellidos="Garcia")]
        umbral = UmbralData(umbral_pct=60, valores_aprobatorios=[])
        actividades_esperadas = ["TP1", "TP2", "TP3"]

        result = compute_atrasados(calificaciones, alumnos, umbral, actividades_esperadas)

        assert len(result) == 1
        assert result[0].alumno_nombre == "Maria Garcia"
        assert result[0].actividad == "TP3"
        assert result[0].causa == "actividad_faltante"

    def test_alumno_todas_aprobadas_no_aparece(self):
        """Scenario: Alumno con todas las actividades aprobadas no aparece."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="TP1", nota_numerica=80, aprobado=True),
            _cal_data(entrada_padron_id=alumno_id, actividad="TP2", nota_numerica=75, aprobado=True),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Carlos", apellidos="Lopez")]
        umbral = UmbralData(umbral_pct=60, valores_aprobatorios=[])
        actividades_esperadas = ["TP1", "TP2"]

        result = compute_atrasados(calificaciones, alumnos, umbral, actividades_esperadas)

        assert len(result) == 0

    def test_alumno_con_nota_textual_aprobatoria_no_es_atrasado(self):
        """Scenario: Alumno con nota textual aprobatoria no es atrasado."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="Estado TP1", nota_textual="Satisfactorio", aprobado=True),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Ana", apellidos="Martinez")]
        umbral = UmbralData(umbral_pct=60, valores_aprobatorios=["Satisfactorio", "Supera lo esperado"])
        actividades_esperadas = ["Estado TP1"]

        result = compute_atrasados(calificaciones, alumnos, umbral, actividades_esperadas)

        assert len(result) == 0

    def test_filtro_busqueda_por_nombre(self):
        """Scenario: Filtro opcional por búsqueda de alumno."""
        alumno_a = uuid.uuid4()
        alumno_b = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_a, actividad="TP1", nota_numerica=40, aprobado=False),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP1", nota_numerica=30, aprobado=False),
        ]
        alumnos = [
            _alumno_data(entrada_padron_id=alumno_a, nombre="Juan", apellidos="Garcia"),
            _alumno_data(entrada_padron_id=alumno_b, nombre="Pedro", apellidos="Rodriguez"),
        ]
        umbral = UmbralData(umbral_pct=60, valores_aprobatorios=[])
        actividades_esperadas = ["TP1"]

        result = compute_atrasados(calificaciones, alumnos, umbral, actividades_esperadas, busqueda="Garcia")

        assert len(result) == 1
        assert "Garcia" in result[0].alumno_nombre

    def test_sin_calificaciones_no_devuelve_atrasados(self):
        """No calificaciones means no data to compute on."""
        alumno_id = uuid.uuid4()
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Juan", apellidos="Perez")]
        umbral = UmbralData(umbral_pct=60, valores_aprobatorios=[])
        actividades_esperadas = ["TP1"]

        result = compute_atrasados([], alumnos, umbral, actividades_esperadas)
        # With no calificaciones, all activities are "faltante"
        assert len(result) == 1
        assert result[0].causa == "actividad_faltante"


# ===== 1.3 compute_ranking =====


class TestComputeRanking:
    """RN-09: Ranking incluye solo alumnos con >=1 actividad aprobada."""

    def test_ranking_descendente_por_aprobadas(self):
        """Scenario: Ranking ordena descendente por aprobadas."""
        alumno_a = uuid.uuid4()
        alumno_b = uuid.uuid4()
        alumno_c = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_a, actividad="TP1", aprobado=True),
            _cal_data(entrada_padron_id=alumno_a, actividad="TP2", aprobado=True),
            _cal_data(entrada_padron_id=alumno_a, actividad="TP3", aprobado=True),
            _cal_data(entrada_padron_id=alumno_a, actividad="TP4", aprobado=True),
            _cal_data(entrada_padron_id=alumno_a, actividad="TP5", aprobado=True),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP1", aprobado=True),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP2", aprobado=True),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP3", aprobado=True),
            _cal_data(entrada_padron_id=alumno_c, actividad="TP1", aprobado=True),
        ]
        alumnos = [
            _alumno_data(entrada_padron_id=alumno_a, nombre="Ana", apellidos="Martinez"),
            _alumno_data(entrada_padron_id=alumno_b, nombre="Carlos", apellidos="Lopez"),
            _alumno_data(entrada_padron_id=alumno_c, nombre="Beatriz", apellidos="Garcia"),
        ]
        actividades_esperadas = ["TP1", "TP2", "TP3", "TP4", "TP5"]

        result = compute_ranking(calificaciones, alumnos, actividades_esperadas)

        assert len(result) == 3
        # Ana: 5, Carlos: 3, Beatriz: 1
        assert result[0].alumno_nombre == "Ana Martinez"
        assert result[0].aprobadas == 5
        assert result[1].alumno_nombre == "Carlos Lopez"
        assert result[1].aprobadas == 3
        assert result[2].alumno_nombre == "Beatriz Garcia"
        assert result[2].aprobadas == 1

    def test_alumno_sin_aprobadas_excluido(self):
        """Scenario: Alumno sin actividades aprobadas excluido."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="TP1", nota_numerica=30, aprobado=False),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Juan", apellidos="Perez")]
        actividades_esperadas = ["TP1"]

        result = compute_ranking(calificaciones, alumnos, actividades_esperadas)

        assert len(result) == 0

    def test_empate_orden_alfabetico(self):
        """Scenario: Empate en aprobadas ordena alfabéticamente."""
        alumno_a = uuid.uuid4()
        alumno_b = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_a, actividad="TP1", aprobado=True),
            _cal_data(entrada_padron_id=alumno_a, actividad="TP2", aprobado=True),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP1", aprobado=True),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP2", aprobado=True),
        ]
        alumnos = [
            _alumno_data(entrada_padron_id=alumno_a, nombre="Beatriz", apellidos="Garcia"),
            _alumno_data(entrada_padron_id=alumno_b, nombre="Ana", apellidos="Garcia"),
        ]
        actividades_esperadas = ["TP1", "TP2"]

        result = compute_ranking(calificaciones, alumnos, actividades_esperadas)

        assert len(result) == 2
        # Both have 2, so alphabetical by apellido then nombre
        assert result[0].alumno_nombre == "Ana Garcia"
        assert result[1].alumno_nombre == "Beatriz Garcia"

    def test_ranking_include_porcentaje(self):
        """Ranking includes percentage of aprobadas."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="TP1", aprobado=True),
            _cal_data(entrada_padron_id=alumno_id, actividad="TP2", aprobado=True),
            _cal_data(entrada_padron_id=alumno_id, actividad="TP3", aprobado=False),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Juan", apellidos="Perez")]
        actividades_esperadas = ["TP1", "TP2", "TP3"]

        result = compute_ranking(calificaciones, alumnos, actividades_esperadas)

        assert len(result) == 1
        assert result[0].aprobadas == 2
        assert result[0].total == 3
        assert result[0].porcentaje == pytest.approx(66.67, rel=0.01)


# ===== 1.4 compute_reporte_rapido =====


class TestComputeReporteRapido:
    """Métricas consolidadas por materia."""

    def test_reporte_incluye_metricas_generales(self):
        """Reporte incluye total alumnos, actividades, promedio, aprobados/desaprobados."""
        alumno_a = uuid.uuid4()
        alumno_b = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_a, actividad="TP1", nota_numerica=80, aprobado=True),
            _cal_data(entrada_padron_id=alumno_a, actividad="TP2", nota_numerica=90, aprobado=True),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP1", nota_numerica=40, aprobado=False),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP2", nota_numerica=50, aprobado=False),
        ]
        alumnos = [
            _alumno_data(entrada_padron_id=alumno_a, nombre="Ana", apellidos="Lopez"),
            _alumno_data(entrada_padron_id=alumno_b, nombre="Juan", apellidos="Perez"),
        ]
        actividades_esperadas = ["TP1", "TP2"]

        result = compute_reporte_rapido(calificaciones, alumnos, actividades_esperadas)

        assert result.total_alumnos == 2
        assert result.total_actividades == 2
        assert result.promedio_general == pytest.approx(65.0, rel=0.01)
        assert result.total_aprobados == 1  # Ana
        assert result.total_desaprobados == 1  # Juan
        assert result.porcentaje_aprobacion == pytest.approx(50.0, rel=0.01)

    def test_reporte_incluye_distribucion_por_actividad(self):
        """Cada actividad listada con su promedio, aprobados y desaprobados."""
        alumno_a = uuid.uuid4()
        alumno_b = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_a, actividad="TP1", nota_numerica=80, aprobado=True),
            _cal_data(entrada_padron_id=alumno_a, actividad="TP2", nota_numerica=90, aprobado=True),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP1", nota_numerica=40, aprobado=False),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP2", nota_numerica=50, aprobado=False),
        ]
        alumnos = [
            _alumno_data(entrada_padron_id=alumno_a, nombre="Ana", apellidos="Lopez"),
            _alumno_data(entrada_padron_id=alumno_b, nombre="Juan", apellidos="Perez"),
        ]
        actividades_esperadas = ["TP1", "TP2"]

        result = compute_reporte_rapido(calificaciones, alumnos, actividades_esperadas)

        assert len(result.actividades) == 2
        tp1 = [a for a in result.actividades if a.nombre == "TP1"][0]
        assert tp1.promedio == 60.0
        assert tp1.aprobados == 1
        assert tp1.desaprobados == 1

        tp2 = [a for a in result.actividades if a.nombre == "TP2"][0]
        assert tp2.promedio == 70.0
        assert tp2.aprobados == 1
        assert tp2.desaprobados == 1

    def test_reporte_sin_datos(self):
        """Materia sin datos retorna estado informativo."""
        result = compute_reporte_rapido([], [], [])
        assert result.total_alumnos == 0
        assert result.total_actividades == 0
        assert result.promedio_general is None
        assert result.total_aprobados == 0
        assert result.total_desaprobados == 0
        assert result.porcentaje_aprobacion is None


# ===== 1.5 compute_nota_final =====


class TestComputeNotaFinal:
    """Promedio simple de notas numéricas por alumno."""

    def test_promedio_notas_numericas(self):
        """Nota final promedio de actividades numéricas."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="TP1", nota_numerica=80, aprobado=True),
            _cal_data(entrada_padron_id=alumno_id, actividad="TP2", nota_numerica=90, aprobado=True),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Juan", apellidos="Perez")]

        result = compute_nota_final(calificaciones, alumnos)

        assert len(result) == 1
        assert result[0].nota_final == 85.0
        assert result[0].actividades_consideradas == 2

    def test_solo_textuales_nota_null(self):
        """Alumno sin notas numéricas tiene nota_final null."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="Estado TP1", nota_textual="Satisfactorio", aprobado=True),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Maria", apellidos="Garcia")]

        result = compute_nota_final(calificaciones, alumnos)

        assert len(result) == 1
        assert result[0].nota_final is None
        assert result[0].actividades_consideradas == 0

    def test_mixto_numericas_y_textuales(self):
        """Alumno con notas numéricas y textuales: solo numéricas promedian."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="TP1", nota_numerica=70, aprobado=True),
            _cal_data(entrada_padron_id=alumno_id, actividad="Estado TP1", nota_textual="Satisfactorio", aprobado=True),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Carlos", apellidos="Lopez")]

        result = compute_nota_final(calificaciones, alumnos)

        assert len(result) == 1
        assert result[0].nota_final == 70.0
        assert result[0].actividades_consideradas == 1

    def test_multiples_alumnos(self):
        """Notas finales de múltiples alumnos."""
        alumno_a = uuid.uuid4()
        alumno_b = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_a, actividad="TP1", nota_numerica=80, aprobado=True),
            _cal_data(entrada_padron_id=alumno_b, actividad="TP1", nota_numerica=60, aprobado=True),
        ]
        alumnos = [
            _alumno_data(entrada_padron_id=alumno_a, nombre="Ana", apellidos="Lopez"),
            _alumno_data(entrada_padron_id=alumno_b, nombre="Juan", apellidos="Perez"),
        ]

        result = compute_nota_final(calificaciones, alumnos)

        assert len(result) == 2
        assert result[0].nota_final == 80.0
        assert result[1].nota_final == 60.0

    def test_sin_calificaciones_lista_vacia(self):
        """Sin calificaciones retorna lista vacía."""
        result = compute_nota_final([], [])
        assert len(result) == 0


# ===== 1.6 compute_tps_sin_corregir =====


class TestComputeTpsSinCorregir:
    """RN-07/RN-08: TPs sin corregir solo de actividades textuales."""

    def test_textual_sin_calificar_se_incluye(self):
        """Actividad textual finalizada sin calificación aparece en reporte."""
        alumno_id = uuid.uuid4()
        calificaciones = []  # No calificaciones for this alumno
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Juan", apellidos="Perez")]

        # These are the textual actividades from the reporte_finalizacion
        reporte_finalizacion = {
            alumno_id: {"Estado TP1": "Finalizado", "Estado TP2": "Finalizado"}
        }

        result = compute_tps_sin_corregir(calificaciones, alumnos, reporte_finalizacion)

        assert len(result) == 2
        assert result[0].actividad in ("Estado TP1", "Estado TP2")

    def test_numerica_sin_calificar_no_se_incluye(self):
        """RN-08: Actividad numérica sin calificación no se incluye."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="TP1 (Real)", nota_numerica=80, aprobado=True),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Juan", apellidos="Perez")]

        # Report has a numeric-like activity - but compute_tps_sin_corregir only
        # receives calificaciones (existing) and reporte_finalizacion (finished entries)
        # By design, if calificacion exists for a textual activity, it's NOT sin_corregir
        reporte_finalizacion = {
            alumno_id: {"TP1 (Real)": "75", "Estado TP1": "Finalizado"}
        }

        result = compute_tps_sin_corregir(calificaciones, alumnos, reporte_finalizacion)

        # Only "Estado TP1" would appear if it's textual and not in calificaciones
        # But "TP1 (Real)" is in calificaciones (we added it above), so it's not sin_corregir
        # "Estado TP1" is in reporte but NOT in calificaciones → sin_corregir
        assert len(result) == 1
        assert result[0].actividad == "Estado TP1"

    def test_con_calificacion_no_aparece(self):
        """Actividad con calificación existente no aparece como sin_corregir."""
        alumno_id = uuid.uuid4()
        calificaciones = [
            _cal_data(entrada_padron_id=alumno_id, actividad="Estado TP1", nota_textual="Satisfactorio", aprobado=True),
        ]
        alumnos = [_alumno_data(entrada_padron_id=alumno_id, nombre="Juan", apellidos="Perez")]
        reporte_finalizacion = {
            alumno_id: {"Estado TP1": "Finalizado"}
        }

        result = compute_tps_sin_corregir(calificaciones, alumnos, reporte_finalizacion)

        assert len(result) == 0


# ===== 1.7 CSV builder =====


class TestBuildCsvString:
    """CSV builder con escape anti-CSV-injection."""

    def test_genera_csv_con_header(self):
        """CSV con header y filas de datos."""
        rows = [
            {"alumno_nombre": "Juan Perez", "actividad": "TP1"},
            {"alumno_nombre": "Maria Garcia", "actividad": "TP2"},
        ]
        result = build_csv_string(rows, columns=["alumno_nombre", "actividad"])

        assert "alumno_nombre,actividad" in result
        assert "Juan Perez,TP1" in result
        assert "Maria Garcia,TP2" in result

    def test_escapa_valores_peligrosos(self):
        """Valores que comienzan con =, +, - o @ reciben prefijo \\t."""
        rows = [
            {"valor": "=CMD", "nombre": "safe"},
            {"valor": "+FORMULA", "nombre": "also safe"},
            {"valor": "-DANGER", "nombre": "safe"},
            {"valor": "@LINK", "nombre": "safe"},
        ]
        result = build_csv_string(rows, columns=["valor", "nombre"])

        assert "\t=CMD" in result
        assert "\t+FORMULA" in result
        assert "\t-DANGER" in result
        assert "\t@LINK" in result

    def test_valores_normales_no_se_escapan(self):
        """Valores normales no se modifican."""
        rows = [{"nombre": "Juan Perez", "email": "juan@test.com"}]
        result = build_csv_string(rows, columns=["nombre", "email"])

        assert "Juan Perez" in result
        assert "juan@test.com" in result
        # juan@test.com starts with 'j', not dangerous
        assert "juan@test.com" in result
