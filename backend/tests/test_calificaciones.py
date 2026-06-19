import io
import uuid
from datetime import date, datetime, timezone

import pytest
from fastapi import UploadFile
from sqlalchemy import inspect, select

from app.core.database import Base
from app.core.security import PasswordService
from app.models import (
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
    UserTenant,
)
from app.models.calificacion import Calificacion, OrigenCalificacion
from app.models.umbral_materia import UmbralMateria
from app.models.mixins import SoftDeleteMixin


# ===== Helpers =====


async def _ensure_table(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _setup_tenant_with_user(db_session, tenant=None):
    if tenant is None:
        code = f"CAL{uuid.uuid4().hex[:6].upper()}"
        tenant = Tenant(name=f"Cal Test {code}", code=code)
        db_session.add(tenant)
        await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"cal-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Cal",
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
        nombre="Materia Test",
    )
    db_session.add(m)
    await db_session.flush()
    return m


async def _create_cohorte(db_session, tenant_id, carrera_id=None):
    from app.models.cohorte import Cohorte
    from app.models.carrera import Carrera

    if carrera_id is None:
        c = Carrera(
            tenant_id=tenant_id,
            codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
            nombre="Carrera Test",
        )
        db_session.add(c)
        await db_session.flush()
        carrera_id = c.id

    coh = Cohorte(
        tenant_id=tenant_id,
        carrera_id=carrera_id,
        nombre=f"COH-{uuid.uuid4().hex[:6].upper()}",
        anio=2026,
    )
    db_session.add(coh)
    await db_session.flush()
    return coh


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


async def _create_entrada_padron(db_session, tenant_id, version_id, nombre="Juan", apellidos="Perez", email=None):
    from app.models.entrada_padron import EntradaPadron

    if email is None:
        email = f"{nombre.lower()}.{apellidos.lower()}@test.com"

    e = EntradaPadron(
        version_id=version_id,
        tenant_id=tenant_id,
        nombre=nombre,
        apellidos=apellidos,
        email=email,
    )
    db_session.add(e)
    await db_session.flush()
    return e


async def _create_asignacion(db_session, tenant_id, materia_id, user_id):
    from app.models.asignacion import Asignacion

    a = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user_id,
        rol="PROFESOR",
        materia_id=materia_id,
        desde=date(2026, 1, 1),
    )
    db_session.add(a)
    await db_session.flush()
    return a


def _make_xlsx_bytes(headers, data_rows):
    """Create an xlsx file in memory."""
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(headers)
    for row in data_rows:
        ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _make_csv_bytes(headers, data_rows, delimiter=","):
    """Create a CSV file in memory."""
    import csv
    import io as io_module

    buf = io_module.StringIO()
    writer = csv.writer(buf, delimiter=delimiter)
    writer.writerow(headers)
    for row in data_rows:
        writer.writerow(row)
    return io_module.BytesIO(buf.getvalue().encode("utf-8-sig"))


# ===== 1.1 & 1.2 Tests de modelos =====


class TestCalificacionModel:
    def test_inherits_soft_delete(self):
        assert issubclass(Calificacion, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = Calificacion.__table__.c["id"]
        assert col.primary_key

    def test_has_required_columns(self):
        cols = Calificacion.__table__.c
        assert "tenant_id" in cols
        assert "entrada_padron_id" in cols
        assert "materia_id" in cols
        assert "actividad" in cols
        assert "aprobado" in cols
        assert "origen" in cols

    def test_nota_numerica_nullable(self):
        col = Calificacion.__table__.c["nota_numerica"]
        assert col.nullable

    def test_nota_textual_nullable(self):
        col = Calificacion.__table__.c["nota_textual"]
        assert col.nullable

    def test_has_origen_enum(self):
        col = Calificacion.__table__.c["origen"]
        assert col is not None

    def test_has_importado_at(self):
        cols = Calificacion.__table__.c
        assert "importado_at" in cols

    def test_has_timestamps(self):
        assert "created_at" in Calificacion.__table__.c
        assert "updated_at" in Calificacion.__table__.c


class TestUmbralMateriaModel:
    def test_inherits_soft_delete(self):
        assert issubclass(UmbralMateria, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = UmbralMateria.__table__.c["id"]
        assert col.primary_key

    def test_has_required_columns(self):
        cols = UmbralMateria.__table__.c
        assert "tenant_id" in cols
        assert "asignacion_id" in cols
        assert "materia_id" in cols
        assert "umbral_pct" in cols

    def test_has_valores_aprobatorios(self):
        cols = UmbralMateria.__table__.c
        assert "valores_aprobatorios" in cols

    def test_umbral_pct_default(self):
        col = UmbralMateria.__table__.c["umbral_pct"]
        assert col.server_default is not None

    def test_has_timestamps(self):
        assert "created_at" in UmbralMateria.__table__.c
        assert "updated_at" in UmbralMateria.__table__.c


# ===== 7.1 Tests de derivación aprobado =====


class TestDerivarAprobado:
    """Tests for _derivar_aprobado pure function (no DB needed)."""

    def test_nota_numerica_sobre_umbral_es_true(self):
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService.__new__(CalificacionService)
        assert svc._derivar_aprobado(nota_numerica=75, nota_textual=None, umbral_pct=60) is True

    def test_nota_numerica_bajo_umbral_es_false(self):
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService.__new__(CalificacionService)
        assert svc._derivar_aprobado(nota_numerica=45, nota_textual=None, umbral_pct=60) is False

    def test_nota_numerica_igual_umbral_es_true(self):
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService.__new__(CalificacionService)
        assert svc._derivar_aprobado(nota_numerica=60, nota_textual=None, umbral_pct=60) is True

    def test_solo_textual_aprobatorio_es_true(self):
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService.__new__(CalificacionService)
        assert svc._derivar_aprobado(
            nota_numerica=None, nota_textual="Satisfactorio", umbral_pct=60,
            valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
        ) is True

    def test_solo_textual_supera_lo_esperado_es_true(self):
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService.__new__(CalificacionService)
        assert svc._derivar_aprobado(
            nota_numerica=None, nota_textual="Supera lo esperado", umbral_pct=60,
            valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
        ) is True

    def test_solo_textual_no_aprobatorio_es_false(self):
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService.__new__(CalificacionService)
        assert svc._derivar_aprobado(
            nota_numerica=None, nota_textual="No satisfactorio", umbral_pct=60,
            valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
        ) is False

    def test_sin_notas_es_false(self):
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService.__new__(CalificacionService)
        assert svc._derivar_aprobado(
            nota_numerica=None, nota_textual=None, umbral_pct=60,
        ) is False

    def test_textual_con_umbral_personalizado(self):
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService.__new__(CalificacionService)
        # "Excelente" is in custom valores_aprobatorios
        assert svc._derivar_aprobado(
            nota_numerica=None, nota_textual="Excelente", umbral_pct=60,
            valores_aprobatorios=["Excelente", "Muy bueno"],
        ) is True
        # "Regular" is not
        assert svc._derivar_aprobado(
            nota_numerica=None, nota_textual="Regular", umbral_pct=60,
            valores_aprobatorios=["Excelente", "Muy bueno"],
        ) is False

    def test_numerica_con_umbral_personalizado(self):
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService.__new__(CalificacionService)
        assert svc._derivar_aprobado(nota_numerica=80, nota_textual=None, umbral_pct=75) is True
        assert svc._derivar_aprobado(nota_numerica=70, nota_textual=None, umbral_pct=75) is False


# ===== 7.2 Tests de import =====


class TestPreviewImport:
    async def test_preview_xlsx_detecta_columnas(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)

        headers = ["nombre", "apellidos", "email", "TP1 (Real)", "TP2 (Real)", "Estado TP1"]
        data = [
            ["Juan", "Perez", "juan@test.com", 80, 90, "Satisfactorio"],
            ["Maria", "Garcia", "maria@test.com", 60, 75, "No satisfactorio"],
        ]
        buf = _make_xlsx_bytes(headers, data)
        file = UploadFile(filename="calificaciones.xlsx", file=buf)

        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)
        result = await svc.preview_import(file)

        assert result.total_filas == 2
        assert result.alumnos_count == 2
        assert len(result.actividades) == 3

        # Check numeric detection (sufijo (Real))
        tp1 = [a for a in result.actividades if a.nombre == "TP1 (Real)"]
        assert len(tp1) == 1
        assert tp1[0].tipo == "numerica"

        tp2 = [a for a in result.actividades if a.nombre == "TP2 (Real)"]
        assert len(tp2) == 1
        assert tp2[0].tipo == "numerica"

        # Check textual detection
        estado = [a for a in result.actividades if a.nombre == "Estado TP1"]
        assert len(estado) == 1
        assert estado[0].tipo == "textual"

    async def test_preview_csv_valido(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)

        headers = ["nombre", "apellidos", "email", "TP1 (Real)", "Estado TP1"]
        data = [
            ["Juan", "Perez", "juan@test.com", "80", "Satisfactorio"],
            ["Maria", "Garcia", "maria@test.com", "60", "No satisfactorio"],
        ]
        buf = _make_csv_bytes(headers, data)
        file = UploadFile(filename="calificaciones.csv", file=buf)

        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)
        result = await svc.preview_import(file)

        assert result.total_filas == 2
        assert len(result.actividades) == 2

    async def test_preview_formato_no_soportado_retorna_422(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)

        buf = io.BytesIO(b"dummy content")
        file = UploadFile(filename="datos.txt", file=buf)

        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await svc.preview_import(file)
        assert exc.value.status_code == 422
        assert "no soportado" in exc.value.detail

    async def test_preview_sin_actividades_retorna_lista_vacia(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)

        headers = ["nombre", "apellidos", "email"]
        data = [
            ["Juan", "Perez", "juan@test.com"],
            ["Maria", "Garcia", "maria@test.com"],
        ]
        buf = _make_xlsx_bytes(headers, data)
        file = UploadFile(filename="calificaciones.xlsx", file=buf)

        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)
        result = await svc.preview_import(file)

        assert len(result.actividades) == 0
        assert result.alumnos_count == 2
        assert result.total_filas == 2


class TestConfirmImport:
    async def test_confirm_crea_calificaciones_con_aprobado(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        version = await _create_version_padron(db_session, tenant.id, materia.id, cohorte.id, user.id)
        entrada = await _create_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez", "juan@test.com")

        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)

        entries = [
            {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com", "TP1 (Real)": 80, "TP2 (Real)": 45},
        ]

        result = await svc.confirm_import(
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            actividades_seleccionadas=["TP1 (Real)", "TP2 (Real)"],
            entries=entries,
            actor_id=user.id,
        )

        assert result.registros_creados == 2
        assert result.materia_id == materia.id
        assert result.cohorte_id == cohorte.id

        # Verify calificaciones in DB
        stmt = select(Calificacion).where(Calificacion.tenant_id == tenant.id)
        rows = await db_session.execute(stmt)
        calificaciones = list(rows.scalars().all())
        assert len(calificaciones) == 2

        # Check aprobado derivation
        tp1 = [c for c in calificaciones if c.actividad == "TP1 (Real)"][0]
        assert tp1.aprobado is True  # 80 >= 60
        assert tp1.nota_numerica == 80

        tp2 = [c for c in calificaciones if c.actividad == "TP2 (Real)"][0]
        assert tp2.aprobado is False  # 45 < 60
        assert tp2.nota_numerica == 45

    async def test_confirm_genera_audit(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        version = await _create_version_padron(db_session, tenant.id, materia.id, cohorte.id, user.id)
        await _create_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez", "juan@test.com")

        from app.models.audit_log import AuditLog
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)
        entries = [{"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com", "TP1 (Real)": 80}]

        await svc.confirm_import(
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            actividades_seleccionadas=["TP1 (Real)"],
            entries=entries,
            actor_id=user.id,
        )

        stmt = select(AuditLog).where(
            AuditLog.tenant_id == tenant.id,
            AuditLog.accion == "CALIFICACIONES_IMPORTAR",
        )
        result = await db_session.execute(stmt)
        logs = list(result.scalars().all())
        assert len(logs) >= 1
        assert logs[0].materia_id == materia.id
        assert logs[0].filas_afectadas == 1


# ===== 7.3 Tests de selección de actividades =====


class TestSeleccionActividades:
    async def test_import_solo_incluye_seleccionadas(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        version = await _create_version_padron(db_session, tenant.id, materia.id, cohorte.id, user.id)
        await _create_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez", "juan@test.com")

        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)
        entries = [{"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com", "TP1 (Real)": 80, "TP2 (Real)": 90}]

        result = await svc.confirm_import(
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            actividades_seleccionadas=["TP1 (Real)"],  # Only TP1 selected
            entries=entries,
            actor_id=user.id,
        )

        assert result.registros_creados == 1

        stmt = select(Calificacion).where(Calificacion.tenant_id == tenant.id)
        rows = await db_session.execute(stmt)
        calificaciones = list(rows.scalars().all())
        assert len(calificaciones) == 1
        assert calificaciones[0].actividad == "TP1 (Real)"

    async def test_actividades_no_seleccionadas_no_generan_registros(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        version = await _create_version_padron(db_session, tenant.id, materia.id, cohorte.id, user.id)
        await _create_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez", "juan@test.com")

        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)
        entries = [{"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com", "TP1 (Real)": 80}]

        # Select an activity that doesn't exist in data
        result = await svc.confirm_import(
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            actividades_seleccionadas=["Actividad Inexistente"],
            entries=entries,
            actor_id=user.id,
        )

        assert result.registros_creados == 0


# ===== 7.4 Tests de umbral por asignación =====


class TestUmbralMateria:
    async def test_configurar_umbral_crea_registro(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, materia.id, user.id)

        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)
        result = await svc.configurar_umbral(
            asignacion_id=asignacion.id,
            materia_id=materia.id,
            umbral_pct=75,
            valores_aprobatorios=["Satisfactorio", "Supera lo esperado", "Excelente"],
            actor_id=user.id,
        )

        assert result.asignacion_id == asignacion.id
        assert result.materia_id == materia.id
        assert result.umbral_pct == 75
        assert "Excelente" in (result.valores_aprobatorios or [])

        # Verify in DB
        stmt = select(UmbralMateria).where(UmbralMateria.tenant_id == tenant.id)
        rows = await db_session.execute(stmt)
        umbrales = list(rows.scalars().all())
        assert len(umbrales) == 1

    async def test_umbral_docente_a_no_afecta_docente_b(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user_a, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        # Create second user in same tenant
        user_b = User(
            tenant_id=tenant.id,
            email=f"cal-b-{uuid.uuid4().hex[:8]}@test.com",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            nombre="CalB",
            apellido="Test",
            password_hash=PasswordService.hash("pass"),
        )
        db_session.add(user_b)
        await db_session.flush()

        ut_b = UserTenant(user_id=user_b.id, tenant_id=tenant.id, is_active=True)
        db_session.add(ut_b)
        await db_session.flush()

        asignacion_a = await _create_asignacion(db_session, tenant.id, materia.id, user_a.id)
        asignacion_b = await _create_asignacion(db_session, tenant.id, materia.id, user_b.id)

        from app.services.calificacion_service import CalificacionService

        svc_a = CalificacionService(db_session, tenant.id)
        await svc_a.configurar_umbral(
            asignacion_id=asignacion_a.id,
            materia_id=materia.id,
            umbral_pct=80,
            valores_aprobatorios=[],
            actor_id=user_a.id,
        )

        svc_b = CalificacionService(db_session, tenant.id)
        umbral_b = await svc_b.get_umbral(asignacion_b.id)

        # Docente B should get default (no umbral configured)
        assert umbral_b["umbral_pct"] == 60

        # Docente A should have 80
        umbral_a = await svc_a.get_umbral(asignacion_a.id)
        assert umbral_a.umbral_pct == 80

    async def test_sin_umbral_configurado_usa_default_60(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, materia.id, user.id)

        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)
        result = await svc.get_umbral(asignacion.id)

        assert result["umbral_pct"] == 60

    async def test_umbral_fuera_de_rango_rechazado(self):
        from app.schemas.calificaciones import UmbralMateriaRequest

        with pytest.raises(ValueError):
            UmbralMateriaRequest(
                asignacion_id=uuid.uuid4(),
                materia_id=uuid.uuid4(),
                umbral_pct=150,
                valores_aprobatorios=[],
            )

        with pytest.raises(ValueError):
            UmbralMateriaRequest(
                asignacion_id=uuid.uuid4(),
                materia_id=uuid.uuid4(),
                umbral_pct=-1,
                valores_aprobatorios=[],
            )

    async def test_umbral_en_limite_inferior_aceptado(self):
        from app.schemas.calificaciones import UmbralMateriaRequest

        req = UmbralMateriaRequest(
            asignacion_id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            umbral_pct=0,
            valores_aprobatorios=[],
        )
        assert req.umbral_pct == 0

    async def test_recalcular_aprobados_tras_cambio_umbral(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        asignacion = await _create_asignacion(db_session, tenant.id, materia.id, user.id)

        version = await _create_version_padron(db_session, tenant.id, materia.id, cohorte.id, user.id)
        entrada = await _create_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez", "juan@test.com")

        # Create calificacion with 70 (would be aprobado with default 60)
        cal = Calificacion(
            tenant_id=tenant.id,
            entrada_padron_id=entrada.id,
            materia_id=materia.id,
            actividad="TP1 (Real)",
            nota_numerica=70.0,
            aprobado=True,
            origen=OrigenCalificacion.IMPORTADO,
            importado_at=datetime.now(timezone.utc),
        )
        db_session.add(cal)
        await db_session.flush()

        # Now set umbral to 80
        from app.services.calificacion_service import CalificacionService

        svc = CalificacionService(db_session, tenant.id)
        await svc.configurar_umbral(
            asignacion_id=asignacion.id,
            materia_id=materia.id,
            umbral_pct=80,
            valores_aprobatorios=[],
            actor_id=user.id,
        )

        # Recalcular
        result = await svc.recalcular_aprobados(asignacion.id)
        assert result["registros_actualizados"] == 1

        # Verify cal is now no aprobado
        await db_session.refresh(cal)
        assert cal.aprobado is False


# ===== 7.5 Tests de reporte de finalización =====


class TestReporteFinalizacion:
    async def test_reporte_detecta_textual_sin_calificar(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        version = await _create_version_padron(db_session, tenant.id, materia.id, cohorte.id, user.id)
        entrada = await _create_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez", "juan@test.com")

        # Create report file with textual activity "Estado TP1" marked as "Finalizado"
        headers = ["nombre", "apellidos", "email", "Estado TP1"]
        data = [
            ["Juan", "Perez", "juan@test.com", "Finalizado"],
        ]
        buf = _make_csv_bytes(headers, data)
        file = UploadFile(filename="reporte.csv", file=buf)

        from app.services.reporte_finalizacion_service import ReporteFinalizacionService

        svc = ReporteFinalizacionService(db_session, tenant.id)
        result = await svc.procesar_reporte(file, materia.id)

        assert result.total == 1
        assert len(result.sin_corregir) == 1
        assert result.sin_corregir[0].actividad == "Estado TP1"
        assert "Juan" in result.sin_corregir[0].alumno_nombre

    async def test_numerica_sin_calificar_no_aparece(self, db_session, test_engine):
        """RN-08: Actividad numérica sin calificación no aparece en listado."""
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        version = await _create_version_padron(db_session, tenant.id, materia.id, cohorte.id, user.id)
        await _create_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez", "juan@test.com")

        # Create a report with a numeric-like activity "TP1 (Real)" 
        # The reporte_finalizacion service only looks at textual activities
        headers = ["nombre", "apellidos", "email", "TP1 (Real)"]
        data = [
            ["Juan", "Perez", "juan@test.com", "75"],
        ]
        buf = _make_csv_bytes(headers, data)
        file = UploadFile(filename="reporte_numerico.csv", file=buf)

        from app.services.reporte_finalizacion_service import ReporteFinalizacionService

        svc = ReporteFinalizacionService(db_session, tenant.id)
        result = await svc.procesar_reporte(file, materia.id)

        # Numeric activity should NOT appear in sin_corregir (RN-08)
        assert result.total == 0
        assert len(result.sin_corregir) == 0

    async def test_con_calificacion_existente_no_aparece(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        version = await _create_version_padron(db_session, tenant.id, materia.id, cohorte.id, user.id)
        entrada = await _create_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez", "juan@test.com")

        # Create an existing calificacion for "Estado TP1"
        cal = Calificacion(
            tenant_id=tenant.id,
            entrada_padron_id=entrada.id,
            materia_id=materia.id,
            actividad="Estado TP1",
            nota_textual="Satisfactorio",
            aprobado=True,
            origen=OrigenCalificacion.IMPORTADO,
            importado_at=datetime.now(timezone.utc),
        )
        db_session.add(cal)
        await db_session.flush()

        # Report says it's finalizado but we already have calificacion
        headers = ["nombre", "apellidos", "email", "Estado TP1"]
        data = [
            ["Juan", "Perez", "juan@test.com", "Finalizado"],
        ]
        buf = _make_csv_bytes(headers, data)
        file = UploadFile(filename="reporte.csv", file=buf)

        from app.services.reporte_finalizacion_service import ReporteFinalizacionService

        svc = ReporteFinalizacionService(db_session, tenant.id)
        result = await svc.procesar_reporte(file, materia.id)

        # Should not appear because calificacion already exists
        assert result.total == 0


# ===== 7.6 Tests de tenant isolation =====


class TestTenantIsolation:
    async def test_tenant_a_no_ve_calificaciones_de_tenant_b(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user_a, tenant_a = await _setup_tenant_with_user(db_session)
        user_b, tenant_b = await _setup_tenant_with_user(db_session)
        materia_a = await _create_materia(db_session, tenant_a.id)
        materia_b = await _create_materia(db_session, tenant_b.id)
        cohorte_a = await _create_cohorte(db_session, tenant_a.id)
        cohorte_b = await _create_cohorte(db_session, tenant_b.id)

        version_a = await _create_version_padron(db_session, tenant_a.id, materia_a.id, cohorte_a.id, user_a.id)
        version_b = await _create_version_padron(db_session, tenant_b.id, materia_b.id, cohorte_b.id, user_b.id)

        entrada_a = await _create_entrada_padron(db_session, tenant_a.id, version_a.id, "Juan", "Perez", "juan@a.com")
        entrada_b = await _create_entrada_padron(db_session, tenant_b.id, version_b.id, "Maria", "Garcia", "maria@b.com")

        # Create calificacion for tenant A
        cal_a = Calificacion(
            tenant_id=tenant_a.id,
            entrada_padron_id=entrada_a.id,
            materia_id=materia_a.id,
            actividad="TP1",
            nota_numerica=80,
            aprobado=True,
            origen=OrigenCalificacion.IMPORTADO,
            importado_at=datetime.now(timezone.utc),
        )
        db_session.add(cal_a)
        await db_session.flush()

        # Create calificacion for tenant B
        cal_b = Calificacion(
            tenant_id=tenant_b.id,
            entrada_padron_id=entrada_b.id,
            materia_id=materia_b.id,
            actividad="TP1",
            nota_numerica=90,
            aprobado=True,
            origen=OrigenCalificacion.IMPORTADO,
            importado_at=datetime.now(timezone.utc),
        )
        db_session.add(cal_b)
        await db_session.flush()

        # Tenant A should only see their calificacion
        from app.repositories.calificacion_repository import CalificacionRepository

        repo_a = CalificacionRepository(db_session, tenant_a.id)
        cal_a_list = await repo_a.list_by_materia(materia_a.id)
        assert len(cal_a_list) == 1
        assert cal_a_list[0].nota_numerica == 80

        # Tenant A should not see B's calificacion even querying by materia
        cal_b_from_a = await repo_a.list_by_materia(materia_b.id)
        assert len(cal_b_from_a) == 0

    async def test_tenant_a_no_ve_umbrales_de_tenant_b(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user_a, tenant_a = await _setup_tenant_with_user(db_session)
        user_b, tenant_b = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant_a.id)
        # Same materia code for tenant B
        from app.models.materia import Materia

        materia_b = Materia(
            tenant_id=tenant_b.id,
            codigo=f"MAT-{uuid.uuid4().hex[:6].upper()}",
            nombre="Materia Test B",
        )
        db_session.add(materia_b)
        await db_session.flush()

        asignacion_a = await _create_asignacion(db_session, tenant_a.id, materia.id, user_a.id)
        asignacion_b = await _create_asignacion(db_session, tenant_b.id, materia_b.id, user_b.id)

        from app.services.calificacion_service import CalificacionService

        svc_a = CalificacionService(db_session, tenant_a.id)
        await svc_a.configurar_umbral(
            asignacion_id=asignacion_a.id,
            materia_id=materia.id,
            umbral_pct=90,
            valores_aprobatorios=[],
            actor_id=user_a.id,
        )

        # Tenant B should not see Tenant A's umbral
        from app.repositories.umbral_materia_repository import UmbralMateriaRepository

        repo_b = UmbralMateriaRepository(db_session, tenant_b.id)
        umbral_b = await repo_b.get_by_asignacion(asignacion_b.id)
        assert umbral_b is None

        # Tenant B also shouldn't see A's umbral even querying by different keys
        # Only B's tenant-scoped query works
        repo_a = UmbralMateriaRepository(db_session, tenant_a.id)
        umbral_a = await repo_a.get_by_asignacion(asignacion_a.id)
        assert umbral_a is not None
        assert umbral_a.umbral_pct == 90


# ===== 7.7 Tests de permisos =====


class TestPermisos:
    async def test_sin_permiso_calificaciones_importar_retorna_401(self, client):
        response = await client.post("/api/v1/calificaciones/preview")
        assert response.status_code == 401

    async def test_sin_permiso_umbral_get_retorna_401(self, client):
        response = await client.get("/api/v1/calificaciones/umbral?asignacion_id=" + str(uuid.uuid4()))
        assert response.status_code == 401

    async def test_sin_permiso_umbral_put_retorna_401(self, client):
        from app.schemas.calificaciones import UmbralMateriaRequest

        response = await client.put(
            "/api/v1/calificaciones/umbral",
            json={"asignacion_id": str(uuid.uuid4()), "materia_id": str(uuid.uuid4()), "umbral_pct": 60, "valores_aprobatorios": []},
        )
        assert response.status_code == 401

    async def test_sin_permiso_recalcular_retorna_401(self, client):
        response = await client.post(
            "/api/v1/calificaciones/umbral/recalcular?asignacion_id=" + str(uuid.uuid4()),
        )
        assert response.status_code == 401

    async def test_sin_permiso_reporte_finalizacion_retorna_401(self, client):
        response = await client.post("/api/v1/calificaciones/reporte-finalizacion")
        assert response.status_code == 401
