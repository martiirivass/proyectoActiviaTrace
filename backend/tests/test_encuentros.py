"""Tests for Encuentros and Guardias modules.

Strict TDD: RED → GREEN → REFACTOR.
These test the full stack: Router → Service → Repository → DB.
"""

import uuid
from datetime import date, datetime, time, timedelta

import pytest
from httpx import AsyncClient

from app.core.security import PasswordService, create_access_token
from app.models import (
    Asignacion,
    Carrera,
    Cohorte,
    Dictado,
    Materia,
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
    UserTenant,
)
from app.models.guardia import DiaGuardia, EstadoGuardia, Guardia
from app.models.instancia_encuentro import EstadoInstancia, InstanciaEncuentro
from app.models.slot_encuentro import DiaSemana, SlotEncuentro

pytestmark = pytest.mark.asyncio


# ===== Helpers =====


async def _setup_tenant_with_user(db_session, role_name="PROFESOR"):
    """Setup tenant with user having encuentros:gestionar permission."""
    code = f"ENC{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Enc Test {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"enc-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Enc",
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
    stmt = select(Permission).where(Permission.name == "encuentros:gestionar")
    result = await db_session.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        perm = Permission(name="encuentros:gestionar", module="encuentros", action="gestionar")
        db_session.add(perm)
        await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
    db_session.add(rp)
    await db_session.flush()

    return user, tenant


async def _setup_second_tenant(db_session):
    """Setup a second tenant with user for isolation tests."""
    from sqlalchemy import select

    code = f"ENC2{uuid.uuid4().hex[:6].upper()}"
    tenant = Tenant(name=f"Enc Test B {code}", code=code)
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"enc-b-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="EncB",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    role = Role(name="PROFESOR", tenant_id=tenant.id)
    db_session.add(role)
    await db_session.flush()

    ur = UserRole(user_id=user.id, tenant_id=tenant.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    stmt = select(Permission).where(Permission.name == "encuentros:gestionar")
    result = await db_session.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        perm = Permission(name="encuentros:gestionar", module="encuentros", action="gestionar")
        db_session.add(perm)
        await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id, tenant_id=tenant.id, scope="global")
    db_session.add(rp)
    await db_session.flush()

    return user, tenant


async def _create_materia(db_session, tenant_id):
    m = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:6].upper()}",
        nombre="Materia Encuentros Test",
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


async def _create_asignacion(db_session, tenant_id, usuario_id, materia_id=None, rol="PROFESOR"):
    a = Asignacion(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        rol=rol,
        materia_id=materia_id,
        desde=date.today(),
        hasta=date.today() + timedelta(days=365),
    )
    db_session.add(a)
    await db_session.flush()
    return a


async def _create_slot_recurrente(db_session, tenant_id, asignacion_id, materia_id):
    slot = SlotEncuentro(
        tenant_id=tenant_id,
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        titulo="Slot Recurrente Test",
        hora=time(18, 0),
        dia_semana=DiaSemana.LUNES,
        fecha_inicio=date(2026, 3, 2),
        cant_semanas=4,
        vig_desde=date(2026, 3, 2),
        vig_hasta=date(2026, 3, 23),
    )
    db_session.add(slot)
    await db_session.flush()
    return slot


async def _create_instancia(db_session, tenant_id, slot_id, materia_id, fecha, estado=EstadoInstancia.PROGRAMADO):
    inst = InstanciaEncuentro(
        tenant_id=tenant_id,
        slot_id=slot_id,
        materia_id=materia_id,
        fecha=fecha,
        hora=time(18, 0),
        titulo="Instancia Test",
        estado=estado,
    )
    db_session.add(inst)
    await db_session.flush()
    return inst


def _make_token(user, tenant, roles=None):
    return create_access_token(user.id, tenant.id, roles or ["PROFESOR"])


# ===== 8.1 Fixtures de setup (implicit in helpers) =====


class TestCrearSlotRecurrente:
    """8.2: Crear slot recurrente con 4 instancias"""

    async def test_crear_slot_recurrente_con_4_instancias(self, client, db_session):
        user, tenant = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)

        resp = await client.post(
            "/api/v1/encuentros/slots",
            json={
                "materia_id": str(materia.id),
                "asignacion_id": str(asignacion.id),
                "titulo": "Clase Semanal",
                "hora": "18:00",
                "dia_semana": "Lunes",
                "fecha_inicio": "2026-03-02",
                "cant_semanas": 4,
                "meet_url": "https://meet.google.com/abc",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "slot_id" in data
        assert data["instancias_creadas"] == 4

        # Verify instancias were created with correct dates
        slot_id = uuid.UUID(data["slot_id"])
        from sqlalchemy import select
        stmt = (
            select(InstanciaEncuentro)
            .where(
                InstanciaEncuentro.slot_id == slot_id,
                InstanciaEncuentro.is_deleted == False,
            )
            .order_by(InstanciaEncuentro.fecha.asc())
        )
        result = await db_session.execute(stmt)
        instancias = list(result.scalars().all())
        assert len(instancias) == 4
        expected_fechas = [
            date(2026, 3, 2),
            date(2026, 3, 9),
            date(2026, 3, 16),
            date(2026, 3, 23),
        ]
        for inst, expected in zip(instancias, expected_fechas):
            assert inst.fecha == expected
            assert inst.estado == EstadoInstancia.PROGRAMADO
            assert inst.meet_url == "https://meet.google.com/abc"


class TestCrearEncuentroUnico:
    """8.3: Crear encuentro único → 1 instancia, cant_semanas=0"""

    async def test_crear_encuentro_unico(self, client, db_session):
        user, tenant = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)

        resp = await client.post(
            "/api/v1/encuentros/slots",
            json={
                "materia_id": str(materia.id),
                "asignacion_id": str(asignacion.id),
                "titulo": "Consulta Pre-Parcial",
                "hora": "10:00",
                "fecha_unica": "2026-04-15",
                "cant_semanas": 0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["instancias_creadas"] == 1

        slot_id = uuid.UUID(data["slot_id"])
        from sqlalchemy import select
        stmt = select(SlotEncuentro).where(SlotEncuentro.id == slot_id)
        result = await db_session.execute(stmt)
        slot = result.scalar_one()
        assert slot.cant_semanas == 0
        assert slot.fecha_unica == date(2026, 4, 15)


class TestValidacionExclusionMutua:
    """8.4: cant_semanas > 0 Y fecha_unica presente → 422"""

    async def test_rechazar_modos_simultaneos(self, client, db_session):
        user, tenant = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)

        resp = await client.post(
            "/api/v1/encuentros/slots",
            json={
                "materia_id": str(materia.id),
                "asignacion_id": str(asignacion.id),
                "titulo": "Modo Invalido",
                "hora": "10:00",
                "dia_semana": "Lunes",
                "fecha_inicio": "2026-03-02",
                "cant_semanas": 4,
                "fecha_unica": "2026-04-15",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestEditarInstancia:
    """8.5-8.7: Editar instancia"""

    async def test_marcar_realizada_con_video(self, client, db_session):
        """8.5: Cambiar estado a Realizado con video_url"""
        user, tenant = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)
        slot = await _create_slot_recurrente(db_session, tenant.id, asignacion.id, materia.id)
        instancia = await _create_instancia(db_session, tenant.id, slot.id, materia.id, date(2026, 3, 2))

        resp = await client.patch(
            f"/api/v1/encuentros/instancias/{instancia.id}",
            json={
                "estado": "Realizado",
                "video_url": "https://vimeo.com/123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado"] == "Realizado"
        assert data["video_url"] == "https://vimeo.com/123"

    async def test_rechazar_transicion_realizado_a_programado(self, client, db_session):
        """8.6: Rechazar Realizado → Programado (409)"""
        user, tenant = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)
        slot = await _create_slot_recurrente(db_session, tenant.id, asignacion.id, materia.id)
        instancia = await _create_instancia(db_session, tenant.id, slot.id, materia.id, date(2026, 3, 2), EstadoInstancia.REALIZADO)

        resp = await client.patch(
            f"/api/v1/encuentros/instancias/{instancia.id}",
            json={"estado": "Programado"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    async def test_rechazar_video_url_sin_realizado(self, client, db_session):
        """8.7: Rechazar video_url si estado no es Realizado (422)"""
        user, tenant = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)
        slot = await _create_slot_recurrente(db_session, tenant.id, asignacion.id, materia.id)
        instancia = await _create_instancia(db_session, tenant.id, slot.id, materia.id, date(2026, 3, 2))

        resp = await client.patch(
            f"/api/v1/encuentros/instancias/{instancia.id}",
            json={
                "estado": "Programado",
                "video_url": "https://vimeo.com/123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestExportarHTML:
    """8.8-8.9: Exportar HTML"""

    async def test_exportar_html_excluye_canceladas(self, client, db_session):
        """8.8: Exportar HTML — verificar formato y exclusión de Canceladas"""
        user, tenant = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)
        slot = await _create_slot_recurrente(db_session, tenant.id, asignacion.id, materia.id)

        # Create instances: 2 Programadas, 1 Realizada, 1 Cancelada
        await _create_instancia(db_session, tenant.id, slot.id, materia.id, date(2026, 3, 2), EstadoInstancia.PROGRAMADO)
        inst2 = await _create_instancia(db_session, tenant.id, slot.id, materia.id, date(2026, 3, 9), EstadoInstancia.PROGRAMADO)
        inst3 = await _create_instancia(db_session, tenant.id, slot.id, materia.id, date(2026, 3, 16), EstadoInstancia.REALIZADO)
        inst3.video_url = "https://vimeo.com/recorded"
        await _create_instancia(db_session, tenant.id, slot.id, materia.id, date(2026, 3, 23), EstadoInstancia.CANCELADO)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/encuentros/{materia.id}/exportar-html",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/html; charset=utf-8"
        html = resp.text
        # Should have 3 data rows (Programadas + Realizada, exclude Cancelada)
        # Total <tr> = 1 header + 3 data = 4
        assert html.count("<tr>") == 4
        # The Cancelada (2026-03-23) should NOT appear
        assert "2026-03-23" not in html
        # Realizada should have video link
        assert "https://vimeo.com/recorded" in html
        # Should not include Cancelada
        assert "Cancelado" not in html

    async def test_exportar_html_vacio(self, client, db_session):
        """8.9: Exportar HTML vacío — 200 con mensaje"""
        user, tenant = await _setup_tenant_with_user(db_session)
        token = _make_token(user, tenant)
        materia = await _create_materia(db_session, tenant.id)

        resp = await client.get(
            f"/api/v1/encuentros/{materia.id}/exportar-html",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert "No hay encuentros programados" in resp.text


class TestVistaAdmin:
    """8.10-8.11: Vista admin"""

    async def test_coordinador_ve_todo_el_tenant(self, client, db_session):
        """8.10: COORDINADOR ve instancias de todo el tenant"""
        user, tenant = await _setup_tenant_with_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)
        slot = await _create_slot_recurrente(db_session, tenant.id, asignacion.id, materia.id)
        await _create_instancia(db_session, tenant.id, slot.id, materia.id, date(2026, 3, 2))
        await _create_instancia(db_session, tenant.id, slot.id, materia.id, date(2026, 3, 9))

        resp = await client.get(
            "/api/v1/encuentros/admin",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    async def test_tutor_recibe_403_en_admin(self, client, db_session):
        """8.11: TUTOR recibe 403 en vista admin"""
        user, tenant = await _setup_tenant_with_user(db_session, "TUTOR")
        token = _make_token(user, tenant, ["TUTOR"])
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)
        slot = await _create_slot_recurrente(db_session, tenant.id, asignacion.id, materia.id)
        await _create_instancia(db_session, tenant.id, slot.id, materia.id, date(2026, 3, 2))

        resp = await client.get(
            "/api/v1/encuentros/admin",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestRegistrarGuardia:
    """8.12-8.13: Registrar guardia"""

    async def test_tutor_registra_guardia_exito(self, client, db_session):
        """8.12: Registrar guardia como TUTOR — éxito"""
        user, tenant = await _setup_tenant_with_user(db_session, "TUTOR")
        token = _make_token(user, tenant, ["TUTOR"])
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id, rol="TUTOR")

        resp = await client.post(
            "/api/v1/guardias/",
            json={
                "asignacion_id": str(asignacion.id),
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "dia": "Martes",
                "horario": "14:00–14:45",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["estado"] == "Pendiente"
        assert "id" in data

    async def test_tutor_no_puede_registrar_para_otra_asignacion(self, client, db_session):
        """8.13: Registrar guardia con asignación ajena — 403"""
        user, tenant = await _setup_tenant_with_user(db_session, "TUTOR")
        token = _make_token(user, tenant, ["TUTOR"])
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

        # Create another user and their asignacion
        otro_user = User(
            tenant_id=tenant.id,
            email=f"otro-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="Otro",
            apellido="User",
            password_hash=PasswordService.hash("pass"),
        )
        db_session.add(otro_user)
        await db_session.flush()

        otra_asignacion = await _create_asignacion(db_session, tenant.id, otro_user.id, materia.id, rol="TUTOR")

        resp = await client.post(
            "/api/v1/guardias/",
            json={
                "asignacion_id": str(otra_asignacion.id),
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "dia": "Martes",
                "horario": "14:00–14:45",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestActualizarEstadoGuardia:
    """8.14: Actualizar estado de guardia"""

    async def test_actualizar_estado_guardia(self, client, db_session):
        user, tenant = await _setup_tenant_with_user(db_session, "TUTOR")
        token = _make_token(user, tenant, ["TUTOR"])
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id, rol="TUTOR")

        # Create guardia directly
        guardia = Guardia(
            tenant_id=tenant.id,
            asignacion_id=asignacion.id,
            materia_id=materia.id,
            carrera_id=carrera.id,
            cohorte_id=cohorte.id,
            dia=DiaGuardia.MARTES,
            horario="14:00–14:45",
            estado=EstadoGuardia.PENDIENTE,
        )
        db_session.add(guardia)
        await db_session.flush()

        resp = await client.patch(
            f"/api/v1/guardias/{guardia.id}",
            json={"estado": "Realizada"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado"] == "Realizada"


class TestListarGuardias:
    """8.15: Listar guardias con filtros"""

    async def test_listar_guardias_filtradas(self, client, db_session):
        user, tenant = await _setup_tenant_with_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)

        # Create 2 guardias
        for i in range(2):
            g = Guardia(
                tenant_id=tenant.id,
                asignacion_id=asignacion.id,
                materia_id=materia.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                dia=DiaGuardia.MARTES,
                horario=f"14:00–14:{45 + i}",
                estado=EstadoGuardia.PENDIENTE,
            )
            db_session.add(g)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/guardias/?materia_id={materia.id}&estado=Pendiente",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2


class TestExportarGuardiasCSV:
    """8.16: Exportar guardias a CSV"""

    async def test_exportar_csv_guardias(self, client, db_session):
        user, tenant = await _setup_tenant_with_user(db_session, "COORDINADOR")
        token = _make_token(user, tenant, ["COORDINADOR"])
        materia = await _create_materia(db_session, tenant.id)
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)
        asignacion = await _create_asignacion(db_session, tenant.id, user.id, materia.id)

        g = Guardia(
            tenant_id=tenant.id,
            asignacion_id=asignacion.id,
            materia_id=materia.id,
            carrera_id=carrera.id,
            cohorte_id=cohorte.id,
            dia=DiaGuardia.MARTES,
            horario="14:00–14:45",
            estado=EstadoGuardia.PENDIENTE,
        )
        db_session.add(g)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/guardias/exportar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "Materia" in resp.text


class TestAislamientoTenant:
    """8.17: Datos del tenant A no visibles en tenant B"""

    async def test_aislamiento_tenant_encuentros(self, client, db_session):
        user_a, tenant_a = await _setup_tenant_with_user(db_session)
        user_b, tenant_b = await _setup_second_tenant(db_session)
        token_a = _make_token(user_a, tenant_a)

        # Create data in tenant A
        materia_a = await _create_materia(db_session, tenant_a.id)
        asignacion_a = await _create_asignacion(db_session, tenant_a.id, user_a.id, materia_a.id)
        slot_a = await _create_slot_recurrente(db_session, tenant_a.id, asignacion_a.id, materia_a.id)
        await _create_instancia(db_session, tenant_a.id, slot_a.id, materia_a.id, date(2026, 3, 2))

        # Try to access from tenant B
        token_b = _make_token(user_b, tenant_b)
        resp = await client.get(
            f"/api/v1/encuentros/slots/{slot_a.id}/instancias",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        # Should get 404 (tenant isolation) or empty list
        assert resp.status_code == 404 or resp.status_code == 200
        if resp.status_code == 200:
            data = resp.json()
            assert data["total"] == 0
