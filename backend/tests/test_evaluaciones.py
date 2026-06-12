"""Tests for Evaluaciones / Coloquios module.

Strict TDD: RED -> GREEN -> REFACTOR.
Full stack: Router -> Service -> Repository -> DB.
"""

import uuid
from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.core.security import PasswordService, create_access_token
from app.models import (
    Asignacion,
    Carrera,
    Cohorte,
    Materia,
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
    UserTenant,
)
from app.models.evaluacion import (
    DiaConvocatoria,
    Evaluacion,
    EvaluacionAlumnoConvocado,
    TipoEvaluacion,
)
from app.models.reserva_evaluacion import EstadoReserva, ReservaEvaluacion
from app.models.resultado_evaluacion import EstadoResultado, ResultadoEvaluacion

pytestmark = pytest.mark.asyncio


# ===== Helpers =====


async def _setup_tenant_with_user(db_session, role_name="COORDINADOR"):
    """Setup tenant with user having coloquios:gestionar permission."""
    code = f"EV{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Eval Test {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"eval-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Eval",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name=role_name, tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    from sqlalchemy import select
    stmt = select(Permission).where(Permission.name == "coloquios:gestionar")
    result = await db_session.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        perm = Permission(name="coloquios:gestionar", module="coloquios", action="gestionar")
        db_session.add(perm)
        await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
    db_session.add(rp)
    await db_session.flush()

    return user, tenant, role


async def _setup_alumno(db_session, tenant, role_alumno=None):
    """Setup an ALUMNO user in the given tenant."""
    if role_alumno is None:
        role_alumno = Role(name="ALUMNO", tenant_id=tenant.id)
        db_session.add(role_alumno)
        await db_session.flush()

        from sqlalchemy import select
        stmt = select(Permission).where(Permission.name == "coloquios:reservar")
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm is None:
            perm = Permission(name="coloquios:reservar", module="coloquios", action="reservar")
            db_session.add(perm)
            await db_session.flush()

        rp = RolePermission(role_id=role_alumno.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
        db_session.add(rp)
        await db_session.flush()

    alumno = User(
        tenant_id=tenant.id,
        email=f"alumno-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Alumno",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(alumno)
    await db_session.flush()

    ut = UserTenant(user_id=alumno.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    ur = UserRole(user_id=alumno.id, tenant_id=tenant.id, role_id=role_alumno.id)
    db_session.add(ur)
    await db_session.flush()

    return alumno, role_alumno


async def _setup_second_tenant(db_session):
    """Setup a second tenant with user for isolation tests."""
    from sqlalchemy import select

    code = f"EV2{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Eval Test B {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"eval-b-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="EvalB",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name="COORDINADOR", tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    stmt = select(Permission).where(Permission.name == "coloquios:gestionar")
    result = await db_session.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        perm = Permission(name="coloquios:gestionar", module="coloquios", action="gestionar")
        db_session.add(perm)
        await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
    db_session.add(rp)
    await db_session.flush()

    return user, tenant, role


async def _create_materia(db_session, tenant_id):
    m = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:6].upper()}",
        nombre="Materia Eval Test",
    )
    db_session.add(m)
    await db_session.flush()
    return m


async def _create_carrera(db_session, tenant_id):
    c = Carrera(
        tenant_id=tenant_id,
        codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
        nombre="Carrera Test",
    )
    db_session.add(c)
    await db_session.flush()
    return c


async def _create_cohorte(db_session, tenant_id, carrera_id):
    coh = Cohorte(
        tenant_id=tenant_id,
        carrera_id=carrera_id,
        nombre=f"COH-{uuid.uuid4().hex[:6].upper()}",
        anio=2026,
    )
    db_session.add(coh)
    await db_session.flush()
    return coh


def _make_token(user, tenant, roles=None):
    return create_access_token(user.id, tenant.id, roles or ["COORDINADOR"])


# ===== 8.1 Fixtures de setup =====


class TestSetup:
    """8.1: Fixtures work correctly"""

    async def test_setup_creates_tenant_and_user(self, client, db_session):
        user, tenant, role = await _setup_tenant_with_user(db_session)
        assert user.id is not None
        assert tenant.id is not None


class TestCrearConvocatoria:
    """8.2-8.3: Crear convocatoria"""

    async def test_crear_convocatoria_con_3_dias(self, client, db_session):
        """8.2: Crear convocatoria con 3 días y verificar persistencia"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

        resp = await client.post(
            "/api/v1/evaluaciones/",
            json={
                "materia_id": str(materia.id),
                "cohorte_id": str(cohorte.id),
                "tipo": "Coloquio",
                "instancia": "Coloquio Final",
                "dias": [
                    {"fecha": "2026-07-01", "cupo_maximo": 10},
                    {"fecha": "2026-07-02", "cupo_maximo": 10},
                    {"fecha": "2026-07-03", "cupo_maximo": 10},
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["instancia"] == "Coloquio Final"
        assert data["activa"] == True
        assert data["tipo"] == "Coloquio"

        # Verify persistence
        from sqlalchemy import select
        stmt = select(Evaluacion).where(Evaluacion.id == uuid.UUID(data["id"]))
        result = await db_session.execute(stmt)
        ev = result.scalar_one()
        assert ev.instancia == "Coloquio Final"

        dias_stmt = select(DiaConvocatoria).where(
            DiaConvocatoria.evaluacion_id == ev.id,
            DiaConvocatoria.is_deleted == False,
        )
        dias_result = await db_session.execute(dias_stmt)
        dias = list(dias_result.scalars().all())
        assert len(dias) == 3

    async def test_crear_convocatoria_sin_dias_422(self, client, db_session):
        """8.3: Crear convocatoria sin días -> 422"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

        resp = await client.post(
            "/api/v1/evaluaciones/",
            json={
                "materia_id": str(materia.id),
                "cohorte_id": str(cohorte.id),
                "tipo": "Coloquio",
                "instancia": "Coloquio Final",
                "dias": [],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestImportarConvocados:
    """8.4-8.5: Importar padrón"""

    async def test_importar_padron_reemplazo_atomico(self, client, db_session):
        """8.4: Importar padrón -> verificar reemplazo atómico"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

        alumno1, role_alumno = await _setup_alumno(db_session, tenant)
        alumno2, _ = await _setup_alumno(db_session, tenant, role_alumno)
        alumno3, _ = await _setup_alumno(db_session, tenant, role_alumno)

        # Create evaluacion
        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio Final",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        # Import
        resp = await client.post(
            f"/api/v1/evaluaciones/{ev.id}/convocados",
            json={
                "alumno_ids": [str(alumno1.id), str(alumno2.id)],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_convocados"] == 2

        # Reimport with different set
        resp2 = await client.post(
            f"/api/v1/evaluaciones/{ev.id}/convocados",
            json={
                "alumno_ids": [str(alumno2.id), str(alumno3.id)],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["total_convocados"] == 2

        # Verify alumno1 is no longer convocado
        from sqlalchemy import select
        stmt = select(EvaluacionAlumnoConvocado).where(
            EvaluacionAlumnoConvocado.evaluacion_id == ev.id,
            EvaluacionAlumnoConvocado.is_deleted == False,
        )
        result = await db_session.execute(stmt)
        convocados = list(result.scalars().all())
        assert len(convocados) == 2
        alumno_ids = {c.alumno_id for c in convocados}
        assert alumno1.id not in alumno_ids
        assert alumno2.id in alumno_ids
        assert alumno3.id in alumno_ids

    async def test_importar_con_invalido_422(self, client, db_session):
        """8.5: Importar padrón con UUID inválido -> 422"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio Final",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        alumno, _ = await _setup_alumno(db_session, tenant)
        fake_id = uuid.uuid4()

        resp = await client.post(
            f"/api/v1/evaluaciones/{ev.id}/convocados",
            json={
                "alumno_ids": [str(alumno.id), str(fake_id)],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestListarConvocatorias:
    """8.6: Listar convocatorias con métricas"""

    async def test_listar_convocatorias_con_metricas(self, client, db_session):
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio Final",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/evaluaciones/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1


class TestEditarConvocatoria:
    """8.7-8.8: Editar convocatoria"""

    async def test_editar_instancia(self, client, db_session):
        """8.7: Editar convocatoria"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio Original",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        resp = await client.patch(
            f"/api/v1/evaluaciones/{ev.id}",
            json={"instancia": "Coloquio Editado"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["instancia"] == "Coloquio Editado"

    async def test_editar_con_reservas_activas_409(self, client, db_session):
        """8.8: Editar convocatoria con reservas activas -> 409"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, _ = await _setup_alumno(db_session, tenant)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=10,
            cupos_ocupados=1,
        )
        db_session.add(dia)
        await db_session.flush()

        reserva = ReservaEvaluacion(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            dia_convocatoria_id=dia.id,
            alumno_id=alumno.id,
            estado=EstadoReserva.ACTIVA,
        )
        db_session.add(reserva)
        await db_session.flush()

        resp = await client.patch(
            f"/api/v1/evaluaciones/{ev.id}",
            json={"instancia": "Nuevo Nombre"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409


class TestCerrarConvocatoria:
    """8.9: Cerrar convocatoria"""

    async def test_cerrar_convocatoria_cancela_reservas(self, client, db_session):
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant, ["ADMIN"])
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, _ = await _setup_alumno(db_session, tenant)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=10,
        )
        db_session.add(dia)
        await db_session.flush()

        reserva = ReservaEvaluacion(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            dia_convocatoria_id=dia.id,
            alumno_id=alumno.id,
            estado=EstadoReserva.ACTIVA,
        )
        db_session.add(reserva)
        await db_session.flush()

        resp = await client.post(
            f"/api/v1/evaluaciones/{ev.id}/cerrar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reservas_canceladas"] == 1

        await db_session.refresh(reserva)
        assert reserva.estado == EstadoReserva.CANCELADA


class TestReservarTurno:
    """8.10-8.13: Reservar turno"""

    async def test_reservar_con_cupo(self, client, db_session):
        """8.10: Reservar turno con cupo disponible -> verificar decremento"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, role_alumno = await _setup_alumno(db_session, tenant)
        token = _make_token(alumno, tenant, ["ALUMNO"])

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=10,
            cupos_ocupados=0,
        )
        db_session.add(dia)
        await db_session.flush()

        # Convocar alumno
        convocado = EvaluacionAlumnoConvocado(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            alumno_id=alumno.id,
        )
        db_session.add(convocado)
        await db_session.flush()

        resp = await client.post(
            "/api/v1/evaluaciones/reservas",
            json={
                "evaluacion_id": str(ev.id),
                "dia_convocatoria_id": str(dia.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["estado"] == "Activa"

        await db_session.refresh(dia)
        assert dia.cupos_ocupados == 1

    async def test_reservar_sin_cupo_409(self, client, db_session):
        """8.11: Reservar turno sin cupo -> 409"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, role_alumno = await _setup_alumno(db_session, tenant)
        token = _make_token(alumno, tenant, ["ALUMNO"])

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=1,
            cupos_ocupados=1,
        )
        db_session.add(dia)
        await db_session.flush()

        convocado = EvaluacionAlumnoConvocado(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            alumno_id=alumno.id,
        )
        db_session.add(convocado)
        await db_session.flush()

        resp = await client.post(
            "/api/v1/evaluaciones/reservas",
            json={
                "evaluacion_id": str(ev.id),
                "dia_convocatoria_id": str(dia.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    async def test_reservar_duplicada_409(self, client, db_session):
        """8.12: Reserva duplicada -> 409"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, role_alumno = await _setup_alumno(db_session, tenant)
        token = _make_token(alumno, tenant, ["ALUMNO"])

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=10,
            cupos_ocupados=0,
        )
        db_session.add(dia)
        await db_session.flush()

        convocado = EvaluacionAlumnoConvocado(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            alumno_id=alumno.id,
        )
        db_session.add(convocado)
        await db_session.flush()

        # First reservation
        resp1 = await client.post(
            "/api/v1/evaluaciones/reservas",
            json={
                "evaluacion_id": str(ev.id),
                "dia_convocatoria_id": str(dia.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 201

        # Second reservation -> 409
        dia2 = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 2),
            cupo_maximo=10,
            cupos_ocupados=0,
        )
        db_session.add(dia2)
        await db_session.flush()

        resp2 = await client.post(
            "/api/v1/evaluaciones/reservas",
            json={
                "evaluacion_id": str(ev.id),
                "dia_convocatoria_id": str(dia2.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 409

    async def test_alumno_no_convocado_reserva_403(self, client, db_session):
        """8.13: Alumno no convocado intenta reservar -> 403"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, role_alumno = await _setup_alumno(db_session, tenant)
        token = _make_token(alumno, tenant, ["ALUMNO"])

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=10,
            cupos_ocupados=0,
        )
        db_session.add(dia)
        await db_session.flush()

        # NOTE: Not convocado
        resp = await client.post(
            "/api/v1/evaluaciones/reservas",
            json={
                "evaluacion_id": str(ev.id),
                "dia_convocatoria_id": str(dia.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestCancelarReserva:
    """8.14-8.15: Cancelar reserva"""

    async def test_cancelar_reserva_libera_cupo(self, client, db_session):
        """8.14: Cancelar reserva -> verificar liberación de cupo"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, role_alumno = await _setup_alumno(db_session, tenant)
        token = _make_token(alumno, tenant, ["ALUMNO"])

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=10,
            cupos_ocupados=1,
        )
        db_session.add(dia)
        await db_session.flush()

        reserva = ReservaEvaluacion(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            dia_convocatoria_id=dia.id,
            alumno_id=alumno.id,
            estado=EstadoReserva.ACTIVA,
        )
        db_session.add(reserva)
        await db_session.flush()

        resp = await client.post(
            f"/api/v1/evaluaciones/reservas/{reserva.id}/cancelar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        await db_session.refresh(reserva)
        assert reserva.estado == EstadoReserva.CANCELADA

        await db_session.refresh(dia)
        assert dia.cupos_ocupados == 0

    async def test_cancelar_reserva_ajena_403(self, client, db_session):
        """8.15: Cancelar reserva ajena -> 403"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, role_alumno = await _setup_alumno(db_session, tenant)
        alumno2, _ = await _setup_alumno(db_session, tenant, role_alumno)
        token = _make_token(alumno2, tenant, ["ALUMNO"])

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=10,
            cupos_ocupados=1,
        )
        db_session.add(dia)
        await db_session.flush()

        reserva = ReservaEvaluacion(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            dia_convocatoria_id=dia.id,
            alumno_id=alumno.id,
            estado=EstadoReserva.ACTIVA,
        )
        db_session.add(reserva)
        await db_session.flush()

        resp = await client.post(
            f"/api/v1/evaluaciones/reservas/{reserva.id}/cancelar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestAgendaReservas:
    """8.16: Agenda consolidada"""

    async def test_agenda_consolidada(self, client, db_session):
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, role_alumno = await _setup_alumno(db_session, tenant)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=10,
        )
        db_session.add(dia)
        await db_session.flush()

        reserva = ReservaEvaluacion(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            dia_convocatoria_id=dia.id,
            alumno_id=alumno.id,
            estado=EstadoReserva.ACTIVA,
        )
        db_session.add(reserva)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/evaluaciones/reservas",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1


class TestMisReservas:
    """8.17: Alumno consulta mis-reservas"""

    async def test_alumno_consulta_mis_reservas(self, client, db_session):
        user, tenant, role = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, role_alumno = await _setup_alumno(db_session, tenant)
        token = _make_token(alumno, tenant, ["ALUMNO"])

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=10,
        )
        db_session.add(dia)
        await db_session.flush()

        reserva = ReservaEvaluacion(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            dia_convocatoria_id=dia.id,
            alumno_id=alumno.id,
            estado=EstadoReserva.ACTIVA,
        )
        db_session.add(reserva)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/evaluaciones/reservas/mis-reservas",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1


class TestResultados:
    """8.18-8.21: Registro de resultados"""

    async def test_registrar_resultado(self, client, db_session):
        """8.18: Registrar resultado -> verificar creación"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, _ = await _setup_alumno(db_session, tenant)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        resp = await client.post(
            "/api/v1/evaluaciones/resultados",
            json={
                "evaluacion_id": str(ev.id),
                "alumno_id": str(alumno.id),
                "nota_final": "8",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nota_final"] == "8"
        assert data["estado"] == "Borrador"

    async def test_resultado_duplicado_409(self, client, db_session):
        """8.19: Resultado duplicado -> 409"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, _ = await _setup_alumno(db_session, tenant)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        # Create first resultado
        resultado = ResultadoEvaluacion(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            alumno_id=alumno.id,
            nota_final="7",
            estado=EstadoResultado.BORRADOR,
        )
        db_session.add(resultado)
        await db_session.flush()

        # Try to create another
        resp = await client.post(
            "/api/v1/evaluaciones/resultados",
            json={
                "evaluacion_id": str(ev.id),
                "alumno_id": str(alumno.id),
                "nota_final": "8",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    async def test_actualizar_borrador_a_definitivo(self, client, db_session):
        """8.20: Actualizar resultado Borrador -> Definitivo"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, _ = await _setup_alumno(db_session, tenant)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        resultado = ResultadoEvaluacion(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            alumno_id=alumno.id,
            nota_final="7",
            estado=EstadoResultado.BORRADOR,
        )
        db_session.add(resultado)
        await db_session.flush()

        resp = await client.patch(
            f"/api/v1/evaluaciones/resultados/{resultado.id}",
            json={"estado": "Definitivo"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado"] == "Definitivo"

    async def test_rechazar_cambio_definitivo_a_borrador(self, client, db_session):
        """8.21: Rechazar cambio Definitivo -> Borrador"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno, _ = await _setup_alumno(db_session, tenant)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        resultado = ResultadoEvaluacion(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            alumno_id=alumno.id,
            nota_final="7",
            estado=EstadoResultado.DEFINITIVO,
        )
        db_session.add(resultado)
        await db_session.flush()

        resp = await client.patch(
            f"/api/v1/evaluaciones/resultados/{resultado.id}",
            json={"estado": "Borrador"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestMetricas:
    """8.22-8.23: Panel de métricas"""

    async def test_panel_metricas(self, client, db_session):
        """8.22: Panel de métricas"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/evaluaciones/metricas",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_alumnos_cargados" in data
        assert "instancias_activas" in data
        assert "reservas_activas" in data
        assert "notas_registradas" in data

    async def test_alumno_no_accede_metricas_403(self, client, db_session):
        """8.23: ALUMNO no puede acceder a métricas -> 403"""
        user, tenant, role = await _setup_tenant_with_user(db_session)
        alumno, role_alumno = await _setup_alumno(db_session, tenant)
        token = _make_token(alumno, tenant, ["ALUMNO"])

        resp = await client.get(
            "/api/v1/evaluaciones/metricas",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestAislamientoTenant:
    """8.24: Aislamiento tenant"""

    async def test_aislamiento_tenant_datos_no_visibles(self, client, db_session):
        user_a, tenant_a, role_a = await _setup_tenant_with_user(db_session)
        user_b, tenant_b, role_b = await _setup_second_tenant(db_session)
        token_a = _make_token(user_a, tenant_a)

        materia_a = await _create_materia(db_session, tenant_a.id)
        carrera_a = await _create_carrera(db_session, tenant_a.id)
        cohorte_a = await _create_cohorte(db_session, tenant_a.id, carrera_a.id)

        ev = Evaluacion(
            tenant_id=tenant_a.id,
            materia_id=materia_a.id,
            cohorte_id=cohorte_a.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio A",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        # Try to access from tenant B
        token_b = _make_token(user_b, tenant_b)
        resp = await client.get(
            f"/api/v1/evaluaciones/{ev.id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404


class TestConcurrencia:
    """8.25: Concurrencia"""

    async def test_concurrencia_dos_reservas_no_sobrepasan_cupo(self, client, db_session):
        user, tenant, role = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        alumno1, role_alumno = await _setup_alumno(db_session, tenant)
        alumno2, _ = await _setup_alumno(db_session, tenant, role_alumno)

        ev = Evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio",
            activa=True,
        )
        db_session.add(ev)
        await db_session.flush()

        dia = DiaConvocatoria(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            fecha=date(2026, 7, 1),
            cupo_maximo=1,
            cupos_ocupados=0,
        )
        db_session.add(dia)
        await db_session.flush()

        for alumno_id in [alumno1.id, alumno2.id]:
            conv = EvaluacionAlumnoConvocado(
                tenant_id=tenant.id,
                evaluacion_id=ev.id,
                alumno_id=alumno_id,
            )
            db_session.add(conv)
        await db_session.flush()

        token1 = _make_token(alumno1, tenant, ["ALUMNO"])
        resp1 = await client.post(
            "/api/v1/evaluaciones/reservas",
            json={
                "evaluacion_id": str(ev.id),
                "dia_convocatoria_id": str(dia.id),
            },
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert resp1.status_code in (201, 409)

        token2 = _make_token(alumno2, tenant, ["ALUMNO"])
        resp2 = await client.post(
            "/api/v1/evaluaciones/reservas",
            json={
                "evaluacion_id": str(ev.id),
                "dia_convocatoria_id": str(dia.id),
            },
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert resp2.status_code in (201, 409)

        # At most one should have succeeded (cupo_maximo=1)
        successes = sum([
            1 if resp1.status_code == 201 else 0,
            1 if resp2.status_code == 201 else 0,
        ])
        assert successes <= 1

        # Ensure cupo is not exceeded in DB
        await db_session.refresh(dia)
        assert dia.cupos_ocupados <= 1
