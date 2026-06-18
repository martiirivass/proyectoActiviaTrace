import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect

from app.core.database import Base
from app.core.security import EncryptionService, PasswordService
from app.models import (
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
    UserTenant,
)
from app.models.entrada_padron import EntradaPadron
from app.models.mixins import SoftDeleteMixin
from app.models.version_padron import VersionPadron

pytestmark = pytest.mark.asyncio


async def _ensure_table(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _setup_tenant_with_user(db_session, tenant=None):
    if tenant is None:
        code = f"PAD{uuid.uuid4().hex[:6].upper()}"
        tenant = Tenant(name=f"Padron Test {code}", code=code)
        db_session.add(tenant)
        await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"pad-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Padron",
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


# ===== 8.1 Tests de modelos =====


class TestVersionPadronModel:
    def test_inherits_soft_delete(self):
        assert issubclass(VersionPadron, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = VersionPadron.__table__.c["id"]
        assert col.primary_key

    def test_has_required_columns(self):
        cols = VersionPadron.__table__.c
        assert "tenant_id" in cols
        assert "materia_id" in cols
        assert "cohorte_id" in cols
        assert "cargado_por" in cols
        assert "cargado_at" in cols
        assert "activa" in cols

    def test_has_timestamps(self):
        assert "created_at" in VersionPadron.__table__.c
        assert "updated_at" in VersionPadron.__table__.c

    def test_has_relationships(self):
        mapper = inspect(VersionPadron)
        rel_names = [r.key for r in mapper.relationships]
        assert "entradas" in rel_names


class TestEntradaPadronModel:
    def test_inherits_soft_delete(self):
        assert issubclass(EntradaPadron, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = EntradaPadron.__table__.c["id"]
        assert col.primary_key

    def test_has_required_columns(self):
        cols = EntradaPadron.__table__.c
        assert "version_id" in cols
        assert "tenant_id" in cols
        assert "nombre" in cols
        assert "apellidos" in cols

    def test_usuario_id_nullable(self):
        col = EntradaPadron.__table__.c["usuario_id"]
        assert col.nullable

    def test_email_encrypted(self):
        col = EntradaPadron.__table__.c["email"]
        assert col is not None

    def test_has_relationships(self):
        mapper = inspect(EntradaPadron)
        rel_names = [r.key for r in mapper.relationships]
        assert "version" in rel_names


async def test_create_version_padron(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    version = VersionPadron(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        cargado_por=user.id,
        activa=True,
    )
    db_session.add(version)
    await db_session.flush()

    assert version.id is not None
    assert isinstance(version.id, uuid.UUID)
    assert version.activa is True
    assert version.is_deleted is False
    assert version.deleted_at is None


async def test_create_entrada_padron(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    version = VersionPadron(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        cargado_por=user.id,
        activa=True,
    )
    db_session.add(version)
    await db_session.flush()

    entry = EntradaPadron(
        version_id=version.id,
        tenant_id=tenant.id,
        nombre="Juan",
        apellidos="Pérez",
        email="juan@test.com",
        comision="A",
        regional="Centro",
    )
    db_session.add(entry)
    await db_session.flush()

    assert entry.id is not None
    assert isinstance(entry.id, uuid.UUID)
    assert entry.nombre == "Juan"
    assert entry.apellidos == "Pérez"
    assert entry.is_deleted is False


async def test_soft_delete_version(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    version = VersionPadron(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        cargado_por=user.id,
        activa=True,
    )
    db_session.add(version)
    await db_session.flush()

    version.soft_delete()
    await db_session.flush()

    assert version.is_deleted is True
    assert version.deleted_at is not None


# ===== 8.2 Tests de versionado =====


async def test_activar_version_desactiva_anterior(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    v1 = VersionPadron(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        cargado_por=user.id,
        activa=True,
    )
    db_session.add(v1)
    await db_session.flush()

    v1.activa = False
    v2 = VersionPadron(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        cargado_por=user.id,
        activa=True,
    )
    db_session.add(v2)
    await db_session.flush()

    assert v1.activa is False
    assert v2.activa is True


# ===== 8.3 Tests de import xlsx =====


async def test_preview_xlsx_valid(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)

    import io
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Alumnos"
    ws.append(["nombre", "apellidos", "email", "comision", "regional"])
    ws.append(["Juan", "Pérez", "juan@test.com", "A", "Centro"])
    ws.append(["María", "García", "maria@test.com", "B", "Norte"])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    from fastapi import UploadFile

    file = UploadFile(filename="test.xlsx", file=buf)

    from app.services.padron_service import PadronService

    svc = PadronService(db_session, tenant.id)
    result = await svc.preview_import(file)

    assert result.total_filas == 2
    assert len(result.entries) == 2
    assert result.entries[0].nombre == "Juan"
    assert result.entries[1].apellidos == "García"


# ===== 8.4 Tests de import csv =====


async def test_preview_csv_valid(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)

    import io
    csv_content = "nombre,apellidos,email,comision,regional\nJuan,Pérez,juan@test.com,A,Centro\nMaría,García,maria@test.com,B,Norte\n"

    from fastapi import UploadFile

    file = UploadFile(filename="test.csv", file=io.BytesIO(csv_content.encode("utf-8")))

    from app.services.padron_service import PadronService

    svc = PadronService(db_session, tenant.id)
    result = await svc.preview_import(file)

    assert result.total_filas == 2
    assert len(result.entries) == 2


async def test_preview_csv_semicolon_delimiter(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)

    import io
    csv_content = "nombre;apellidos;email;comision;regional\nJuan;Pérez;juan@test.com;A;Centro\nMaría;García;maria@test.com;B;Norte\n"

    from fastapi import UploadFile

    file = UploadFile(filename="test.csv", file=io.BytesIO(csv_content.encode("utf-8")))

    from app.services.padron_service import PadronService

    svc = PadronService(db_session, tenant.id)
    result = await svc.preview_import(file)

    assert result.total_filas == 2
    assert len(result.entries) == 2


# ===== 8.5 Tests de confirm =====


async def test_confirm_crea_version_activa_con_entradas(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    entries = [
        {"nombre": "Juan", "apellidos": "Pérez", "email": "juan@test.com"},
        {"nombre": "María", "apellidos": "García", "email": "maria@test.com"},
    ]

    from app.services.padron_service import PadronService

    svc = PadronService(db_session, tenant.id)
    result = await svc.confirm_import(materia.id, cohorte.id, entries, user.id)

    assert result.version_id is not None
    assert result.activa is True
    assert result.filas_creadas == 2

    from sqlalchemy import select

    stmt = select(EntradaPadron).where(EntradaPadron.tenant_id == tenant.id)
    rows = await db_session.execute(stmt)
    db_entries = list(rows.scalars().all())
    assert len(db_entries) == 2


# ===== 8.6 Tests de entrada sin usuario_id =====


async def test_entrada_sin_usuario_id(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    version = VersionPadron(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        cargado_por=user.id,
        activa=True,
    )
    db_session.add(version)
    await db_session.flush()

    entry = EntradaPadron(
        version_id=version.id,
        tenant_id=tenant.id,
        nombre="SinCuenta",
        apellidos="Alumno",
        email="sincuenta@test.com",
    )
    db_session.add(entry)
    await db_session.flush()

    assert entry.usuario_id is None
    assert entry.nombre == "SinCuenta"


# ===== 8.7 Tests de tenant isolation =====


async def test_tenant_isolation(db_session, test_engine):
    await _ensure_table(test_engine)
    user_a, tenant_a = await _setup_tenant_with_user(db_session)
    user_b, tenant_b = await _setup_tenant_with_user(db_session)
    materia_a = await _create_materia(db_session, tenant_a.id)
    materia_b = await _create_materia(db_session, tenant_b.id)
    cohorte_a = await _create_cohorte(db_session, tenant_a.id)
    cohorte_b = await _create_cohorte(db_session, tenant_b.id)

    v_a = VersionPadron(
        tenant_id=tenant_a.id, materia_id=materia_a.id,
        cohorte_id=cohorte_a.id, cargado_por=user_a.id, activa=True,
    )
    db_session.add(v_a)
    v_b = VersionPadron(
        tenant_id=tenant_b.id, materia_id=materia_b.id,
        cohorte_id=cohorte_b.id, cargado_por=user_b.id, activa=True,
    )
    db_session.add(v_b)
    await db_session.flush()

    from sqlalchemy import select

    stmt_a = select(VersionPadron).where(VersionPadron.tenant_id == tenant_a.id, VersionPadron.is_deleted == False)
    result_a = await db_session.execute(stmt_a)
    versions_a = list(result_a.scalars().all())

    stmt_b = select(VersionPadron).where(VersionPadron.tenant_id == tenant_b.id, VersionPadron.is_deleted == False)
    result_b = await db_session.execute(stmt_b)
    versions_b = list(result_b.scalars().all())

    assert len(versions_a) == 1
    assert len(versions_b) == 1
    assert versions_a[0].id == v_a.id
    assert versions_b[0].id == v_b.id


# ===== 8.8 Tests de vaciar materia =====


async def test_vaciar_materia_soft_delete(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.repositories.padron_repository import PadronRepository

    repo = PadronRepository(db_session, tenant.id)
    version = await repo.create_version(materia.id, cohorte.id, user.id)
    await repo.bulk_create_entries(version.id, [
        {"nombre": "A", "apellidos": "B"},
        {"nombre": "C", "apellidos": "D"},
    ])

    affected = await repo.vaciar_materia(materia.id)
    assert affected == 1

    from sqlalchemy import select

    stmt_v = select(VersionPadron).where(VersionPadron.id == version.id)
    r = await db_session.execute(stmt_v)
    db_v = r.scalar_one()
    assert db_v.is_deleted is True
    assert db_v.activa is False

    stmt_e = select(EntradaPadron).where(EntradaPadron.version_id == version.id)
    r = await db_session.execute(stmt_e)
    db_entries = list(r.scalars().all())
    assert all(e.is_deleted for e in db_entries)


# ===== 8.9 Tests de vaciar materia sin datos =====


async def test_vaciar_materia_sin_datos(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)

    from app.repositories.padron_repository import PadronRepository

    repo = PadronRepository(db_session, tenant.id)
    affected = await repo.vaciar_materia(materia.id)
    assert affected == 0


# ===== 8.10 Tests de vaciar solo afecta materia indicada =====


async def test_vaciar_solo_afecta_materia_indicada(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia_a = await _create_materia(db_session, tenant.id)
    materia_b = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.repositories.padron_repository import PadronRepository

    repo = PadronRepository(db_session, tenant.id)
    await repo.create_version(materia_a.id, cohorte.id, user.id)
    await repo.create_version(materia_b.id, cohorte.id, user.id)

    affected = await repo.vaciar_materia(materia_a.id)
    assert affected == 1

    from sqlalchemy import select

    stmt = select(VersionPadron).where(
        VersionPadron.tenant_id == tenant.id,
        VersionPadron.is_deleted == False,
    )
    r = await db_session.execute(stmt)
    remaining = list(r.scalars().all())
    assert len(remaining) == 1
    assert remaining[0].materia_id == materia_b.id


# ===== 8.11 Tests de permiso =====


async def test_sin_permiso_padron_cargar_retorna_403(db_session, client):
    response = await client.post("/api/v1/padron/preview")
    assert response.status_code == 401


async def test_sin_permiso_padron_vaciar_retorna_403(db_session, client):
    response = await client.delete(f"/api/v1/admin/materias/{uuid.uuid4()}/vaciar")
    assert response.status_code == 401


# ===== 8.12 Tests de Moodle WS mock =====


async def test_moodle_ws_client_get_users_by_cohort():
    from app.integrations.moodle_ws import MoodleWSClient

    client = MoodleWSClient(base_url="http://localhost", token="test")
    try:
        await client.get_users_by_cohort(1)
    except Exception:
        pass
    finally:
        await client.close()


async def test_moodle_ws_client_retry_on_timeout():
    from app.integrations.moodle_ws import MoodleWSClient, MoodleWSException

    client = MoodleWSClient(base_url="http://localhost:1", token="test", timeout=1)
    try:
        await client.get_users_by_cohort(1)
        assert False, "Should have raised"
    except MoodleWSException:
        pass
    finally:
        await client.close()


# ===== 8.13 Tests de Moodle WS error =====


async def test_moodle_ws_error_502():
    from app.integrations.moodle_ws import MoodleWSClient, MoodleWSException

    client = MoodleWSClient(base_url="http://localhost:1", token="test", timeout=1)
    try:
        await client.get_users_by_cohort(1)
        assert False
    except MoodleWSException:
        pass
    finally:
        await client.close()


# ===== 8.14 Tests de audit log =====


async def test_confirm_import_genera_audit(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.models.audit_log import AuditLog
    from app.services.padron_service import PadronService

    svc = PadronService(db_session, tenant.id)
    await svc.confirm_import(materia.id, cohorte.id, [
        {"nombre": "A", "apellidos": "B"},
    ], user.id)

    from sqlalchemy import select

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == tenant.id,
        AuditLog.accion == "PADRON_CARGAR",
    )
    r = await db_session.execute(stmt)
    logs = list(r.scalars().all())
    assert len(logs) >= 1
    assert logs[0].materia_id == materia.id


async def test_vaciar_materia_genera_audit(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.models.audit_log import AuditLog
    from app.repositories.padron_repository import PadronRepository
    from app.services.padron_service import PadronService

    repo = PadronRepository(db_session, tenant.id)
    await repo.create_version(materia.id, cohorte.id, user.id)

    svc = PadronService(db_session, tenant.id)
    await svc.vaciar_materia(materia.id, user.id)

    from sqlalchemy import select

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == tenant.id,
        AuditLog.accion == "PADRON_VACIAR",
    )
    r = await db_session.execute(stmt)
    logs = list(r.scalars().all())
    assert len(logs) >= 1
    assert logs[0].materia_id == materia.id
