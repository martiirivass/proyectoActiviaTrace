"""Integration tests for CalificacionRepository analisis methods."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.core.database import Base
from app.models.calificacion import Calificacion, OrigenCalificacion

pytestmark = pytest.mark.asyncio


async def _ensure_table(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _setup_tenant_with_user(db_session, tenant=None):
    from app.core.security import PasswordService
    from app.models import Tenant, User, UserTenant

    if tenant is None:
        code = f"REP{uuid.uuid4().hex[:6].upper()}"
        tenant = Tenant(name=f"Repo Test {code}", code=code)
        db_session.add(tenant)
        await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"repo-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Repo",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    return user, tenant


async def _create_materia(db_session, tenant_id):
    from app.models.materia import Materia

    m = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:6].upper()}",
        nombre="Materia Analisis",
    )
    db_session.add(m)
    await db_session.flush()
    return m


async def _create_entrada_padron(db_session, tenant_id, version_id, nombre="Juan", apellidos="Perez", email=None, comision="A", regional="CABA"):
    from app.models.entrada_padron import EntradaPadron

    if email is None:
        email = f"{nombre.lower()}.{apellidos.lower()}@test.com"

    e = EntradaPadron(
        version_id=version_id,
        tenant_id=tenant_id,
        nombre=nombre,
        apellidos=apellidos,
        email=email,
        comision=comision,
        regional=regional,
    )
    db_session.add(e)
    await db_session.flush()
    return e


async def _create_version_padron(db_session, tenant_id, materia_id, cohorte_id, user_id):
    from app.models.version_padron import VersionPadron

    v = VersionPadron(
        tenant_id=tenant_id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        cargado_por=user_id,
        activa=True,
    )
    db_session.add(v)
    await db_session.flush()
    return v


async def _create_cohorte(db_session, tenant_id):
    from app.models.cohorte import Cohorte
    from app.models.carrera import Carrera

    c = Carrera(
        tenant_id=tenant_id,
        codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
        nombre="Carrera Test",
    )
    db_session.add(c)
    await db_session.flush()

    coh = Cohorte(
        tenant_id=tenant_id,
        carrera_id=c.id,
        nombre=f"COH-{uuid.uuid4().hex[:6].upper()}",
        anio=2026,
    )
    db_session.add(coh)
    await db_session.flush()
    return coh


async def _create_entrada_simple(db_session, tenant_id, materia_id, cohorte_id, user_id, nombre="Juan", apellidos="Perez"):
    """Create a simple entrada_padron with all needed parents."""
    version = await _create_version_padron(db_session, tenant_id, materia_id, cohorte_id, user_id)
    return await _create_entrada_padron(db_session, tenant_id, version.id, nombre, apellidos)


# ===== 2.1 get_actividades_by_materia =====


class TestGetActividadesByMateria:
    async def test_retorna_actividades_distint_por_materia(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        entrada = await _create_entrada_simple(db_session, tenant.id, materia.id, cohorte.id, user.id)

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)

        # Create calificaciones with various actividades
        for actividad in ["TP1", "TP2", "TP1"]:
            cal = Calificacion(
                tenant_id=tenant.id,
                entrada_padron_id=entrada.id,
                materia_id=materia.id,
                actividad=actividad,
                nota_numerica=80, aprobado=True,
                origen=OrigenCalificacion.IMPORTADO,
            )
            db_session.add(cal)
        await db_session.flush()

        result = await repo.get_actividades_by_materia(materia.id)

        assert sorted(result) == ["TP1", "TP2"]

    async def test_otra_materia_no_contamina(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia_a = await _create_materia(db_session, tenant.id)
        materia_b = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        entrada = await _create_entrada_simple(db_session, tenant.id, materia_a.id, cohorte.id, user.id)

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)

        cal = Calificacion(
            tenant_id=tenant.id,
            entrada_padron_id=entrada.id,
            materia_id=materia_a.id,
            actividad="TP-A",
            nota_numerica=80, aprobado=True,
            origen=OrigenCalificacion.IMPORTADO,
        )
        db_session.add(cal)
        await db_session.flush()

        result_a = await repo.get_actividades_by_materia(materia_a.id)
        result_b = await repo.get_actividades_by_materia(materia_b.id)

        assert result_a == ["TP-A"]
        assert result_b == []

    async def test_sin_calificaciones_retorna_vacio(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)
        result = await repo.get_actividades_by_materia(materia.id)
        assert result == []


# ===== 2.2 get_calificaciones_with_alumno =====


class TestGetCalificacionesWithAlumno:
    async def test_retorna_calificaciones_con_datos_alumno(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        version = await _create_version_padron(db_session, tenant.id, materia.id, cohorte.id, user.id)
        entrada = await _create_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez", comision="A", regional="CABA")

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)

        cal = Calificacion(
            tenant_id=tenant.id,
            entrada_padron_id=entrada.id,
            materia_id=materia.id,
            actividad="TP1",
            nota_numerica=80, aprobado=True,
            origen=OrigenCalificacion.IMPORTADO,
        )
        db_session.add(cal)
        await db_session.flush()

        result = await repo.get_calificaciones_with_alumno(materia.id)

        assert len(result) == 1
        assert result[0]["alumno_nombre"] == "Juan Perez"
        assert result[0]["email"] == entrada.email
        assert result[0]["comision"] == "A"
        assert result[0]["regional"] == "CABA"
        assert result[0]["actividad"] == "TP1"
        assert result[0]["nota_numerica"] == 80

    async def test_sin_calificaciones_retorna_vacio(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)
        result = await repo.get_calificaciones_with_alumno(materia.id)
        assert result == []


# ===== 2.3 get_aggregated_by_materia =====


class TestGetAggregatedByMateria:
    async def test_retorna_metricas_agregadas(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        entrada = await _create_entrada_simple(db_session, tenant.id, materia.id, cohorte.id, user.id)

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)

        cal1 = Calificacion(
            tenant_id=tenant.id,
            entrada_padron_id=entrada.id,
            materia_id=materia.id,
            actividad="TP1",
            nota_numerica=80, aprobado=True,
            origen=OrigenCalificacion.IMPORTADO,
        )
        db_session.add(cal1)
        cal2 = Calificacion(
            tenant_id=tenant.id,
            entrada_padron_id=entrada.id,
            materia_id=materia.id,
            actividad="TP2",
            nota_numerica=60, aprobado=True,
            origen=OrigenCalificacion.IMPORTADO,
        )
        db_session.add(cal2)
        await db_session.flush()

        result = await repo.get_aggregated_by_materia(materia.id)

        assert result["count"] == 2
        assert result["avg"] == pytest.approx(70.0, rel=0.01)
        assert result["min"] == 60.0
        assert result["max"] == 80.0

    async def test_sin_notas_numericas_retorna_none(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        entrada = await _create_entrada_simple(db_session, tenant.id, materia.id, cohorte.id, user.id)

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)

        cal = Calificacion(
            tenant_id=tenant.id,
            entrada_padron_id=entrada.id,
            materia_id=materia.id,
            actividad="Estado TP1",
            nota_textual="Satisfactorio", aprobado=True,
            origen=OrigenCalificacion.IMPORTADO,
        )
        db_session.add(cal)
        await db_session.flush()

        result = await repo.get_aggregated_by_materia(materia.id)

        assert result["count"] == 1
        assert result["avg"] is None
        assert result["min"] is None
        assert result["max"] is None

    async def test_sin_calificaciones(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)
        result = await repo.get_aggregated_by_materia(materia.id)

        assert result["count"] == 0
        assert result["avg"] is None
        assert result["min"] is None
        assert result["max"] is None


# ===== 2.4 count_aprobados_desaprobados =====


class TestCountAprobadosDesaprobados:
    async def test_cuenta_aprobados_y_desaprobados(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        entrada = await _create_entrada_simple(db_session, tenant.id, materia.id, cohorte.id, user.id)

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)

        for i in range(3):
            cal = Calificacion(
                tenant_id=tenant.id,
                entrada_padron_id=entrada.id,
                materia_id=materia.id,
                actividad=f"TP{i+1}",
                nota_numerica=80, aprobado=True,
                origen=OrigenCalificacion.IMPORTADO,
            )
            db_session.add(cal)
        for i in range(2):
            cal = Calificacion(
                tenant_id=tenant.id,
                entrada_padron_id=entrada.id,
                materia_id=materia.id,
                actividad=f"TP{i+4}",
                nota_numerica=40, aprobado=False,
                origen=OrigenCalificacion.IMPORTADO,
            )
            db_session.add(cal)
        await db_session.flush()

        aprobados, desaprobados = await repo.count_aprobados_desaprobados(materia.id)

        assert aprobados == 3
        assert desaprobados == 2

    async def test_sin_calificaciones(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)
        aprobados, desaprobados = await repo.count_aprobados_desaprobados(materia.id)

        assert aprobados == 0
        assert desaprobados == 0


# ===== 2.5 get_alumnos_en_padron =====


class TestGetAlumnosEnPadron:
    async def test_retorna_alumnos_del_padron_para_materia(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        version = await _create_version_padron(db_session, tenant.id, materia.id, cohorte.id, user.id)
        entrada1 = await _create_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez")
        entrada2 = await _create_entrada_padron(db_session, tenant.id, version.id, "Maria", "Garcia")

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)
        result = await repo.get_alumnos_en_padron(materia.id)

        assert len(result) == 2
        nombres = {e.nombre for e in result}
        assert "Juan" in nombres
        assert "Maria" in nombres

    async def test_retorna_vacio_si_no_hay_version_activa(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.repositories.calificacion_repository import CalificacionRepository

        repo = CalificacionRepository(db_session, tenant.id)
        result = await repo.get_alumnos_en_padron(materia.id)

        assert result == []
