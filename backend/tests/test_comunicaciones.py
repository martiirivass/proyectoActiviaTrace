import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

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
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.lote_comunicacion import EstadoLote, LoteComunicacion
from app.models.mixins import SoftDeleteMixin
from app.models.audit_log import AuditLog


# ===== Helpers =====


async def _ensure_table(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _setup_tenant_with_user(db_session, tenant=None):
    if tenant is None:
        code = f"COM{uuid.uuid4().hex[:6].upper()}"
        tenant = Tenant(name=f"Com Test {code}", code=code)
        db_session.add(tenant)
        await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"com-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Com",
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
        nombre="Materia Com Test",
    )
    db_session.add(m)
    await db_session.flush()
    return m


async def _create_lote(db_session, tenant_id, materia_id, user_id, total=5):
    lote = LoteComunicacion(
        tenant_id=tenant_id,
        materia_id=materia_id,
        enviado_por=user_id,
        total_mensajes=total,
    )
    db_session.add(lote)
    await db_session.flush()
    return lote


async def _create_comunicacion(
    db_session, tenant_id, materia_id, user_id,
    email="alumno@test.com", lote_id=None, estado=EstadoComunicacion.PENDIENTE,
):
    c = Comunicacion(
        tenant_id=tenant_id,
        lote_id=lote_id,
        enviado_por=user_id,
        materia_id=materia_id,
        destinatario=email,
        asunto="Test Asunto",
        cuerpo="Test Cuerpo",
        estado=estado,
    )
    db_session.add(c)
    await db_session.flush()
    return c


async def _setup_role_and_permission(db_session, tenant_id, user_id, perm_codename):
    """Assign a permission to a user via role."""
    role = Role(name=f"role-{uuid.uuid4().hex[:6]}", tenant_id=tenant_id)
    db_session.add(role)
    await db_session.flush()

    # Get or create permission
    stmt = select(Permission).where(Permission.codename == perm_codename)
    result = await db_session.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        perm = Permission(
            codename=perm_codename,
            nombre=perm_codename,
            modulo=perm_codename.split(":")[0],
        )
        db_session.add(perm)
        await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id)
    db_session.add(rp)
    await db_session.flush()

    ur = UserRole(user_id=user_id, tenant_id=tenant_id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    return role


# ===== 9.1 Tests de creación de comunicaciones =====


class TestCreacionComunicaciones:
    async def test_preview_retorna_representacion_correcta(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        result = await svc.preview(
            asunto="Test Asunto",
            cuerpo="Test Cuerpo",
            materia_id=materia.id,
            destinatarios=["alumno1@test.com", "alumno2@test.com"],
        )

        assert result.asunto == "Test Asunto"
        assert result.cuerpo_renderizado == "Test Cuerpo"
        assert result.cantidad_destinatarios == 2

    async def test_enviar_individual_crea_comunicacion_pendiente(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        result = await svc.enviar_individual(
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=materia.id,
            destinatario_email="alumno@test.com",
            actor_id=user.id,
        )

        assert result.estado == "Pendiente"

        # Verify in DB
        stmt = select(Comunicacion).where(Comunicacion.tenant_id == tenant.id)
        rows = await db_session.execute(stmt)
        comunicaciones = list(rows.scalars().all())
        assert len(comunicaciones) == 1
        assert comunicaciones[0].estado == EstadoComunicacion.PENDIENTE
        assert comunicaciones[0].asunto == "Test"
        assert comunicaciones[0].lote_id is None

    async def test_enviar_masivo_crea_lote_y_n_comunicaciones(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        result = await svc.enviar_masivo(
            asunto="Test Masivo",
            cuerpo="Cuerpo",
            materia_id=materia.id,
            destinatarios=["alumno1@test.com", "alumno2@test.com", "alumno3@test.com"],
            actor_id=user.id,
        )

        assert result.total_mensajes == 3
        assert result.estado_lote == "Pendiente"

        # Verify lote in DB
        stmt = select(LoteComunicacion).where(LoteComunicacion.tenant_id == tenant.id)
        rows = await db_session.execute(stmt)
        lotes = list(rows.scalars().all())
        assert len(lotes) == 1
        assert lotes[0].estado == EstadoLote.PENDIENTE
        assert lotes[0].total_mensajes == 3

        # Verify comunicaciones in DB
        stmt = select(Comunicacion).where(Comunicacion.tenant_id == tenant.id)
        rows = await db_session.execute(stmt)
        comunicaciones = list(rows.scalars().all())
        assert len(comunicaciones) == 3
        for c in comunicaciones:
            assert c.lote_id == lotes[0].id
            assert c.estado == EstadoComunicacion.PENDIENTE

    async def test_envio_masivo_dedup_destinatarios(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        result = await svc.enviar_masivo(
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=materia.id,
            destinatarios=["alumno@test.com", "alumno@test.com", "otro@test.com"],
            actor_id=user.id,
        )

        # Should deduplicate to 2
        assert result.total_mensajes == 2

        stmt = select(Comunicacion).where(Comunicacion.tenant_id == tenant.id)
        rows = await db_session.execute(stmt)
        comunicaciones = list(rows.scalars().all())
        assert len(comunicaciones) == 2

    async def test_preview_asunto_vacio_rechazado(self):
        from app.schemas.comunicaciones import ComunicacionPreviewRequest

        with pytest.raises(ValueError):
            ComunicacionPreviewRequest(
                asunto="   ",
                cuerpo="Cuerpo",
                materia_id=uuid.uuid4(),
                destinatarios=["test@test.com"],
            )

    async def test_envio_masivo_sin_destinatarios_rechazado(self):
        from app.schemas.comunicaciones import ComunicacionMasivaRequest

        with pytest.raises(ValueError):
            ComunicacionMasivaRequest(
                asunto="Test",
                cuerpo="Cuerpo",
                materia_id=uuid.uuid4(),
                destinatarios=[],
            )

    async def test_envio_individual_sin_asunto_rechazado(self):
        from app.schemas.comunicaciones import ComunicacionIndividualRequest

        with pytest.raises(ValueError):
            ComunicacionIndividualRequest(
                asunto="",
                cuerpo="Cuerpo",
                materia_id=uuid.uuid4(),
                destinatario_email="test@test.com",
            )


# ===== 9.2 Tests de aprobación =====


class TestAprobacionLotes:
    async def test_listar_lotes_pendientes(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        await _create_lote(db_session, tenant.id, materia.id, user.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        lotes = await svc.listar_lotes_pendientes()
        assert len(lotes) == 1
        assert lotes[0].materia_id == materia.id
        assert lotes[0].total_mensajes == 5

    async def test_listar_lotes_pendientes_solo_pendientes(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        # Create one Pendiente and one Aprobado
        lote1 = await _create_lote(db_session, tenant.id, materia.id, user.id)
        lote2 = await _create_lote(db_session, tenant.id, materia.id, user.id)
        lote2.estado = EstadoLote.APROBADO
        await db_session.flush()

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        lotes = await svc.listar_lotes_pendientes()
        assert len(lotes) == 1
        assert lotes[0].id == lote1.id

    async def test_aprobar_lote_cambia_estado(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        lote = await _create_lote(db_session, tenant.id, materia.id, user.id, total=3)

        # Create some comunicaciones for the lote
        for i in range(3):
            await _create_comunicacion(
                db_session, tenant.id, materia.id, user.id,
                email=f"alumno{i}@test.com", lote_id=lote.id,
            )

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        result = await svc.aprobar_lote(lote_id=lote.id, aprobado_por=user.id)

        assert result.estado == "Aprobado"
        assert result.mensajes_liberados == 3

        await db_session.refresh(lote)
        assert lote.estado == EstadoLote.APROBADO
        assert lote.aprobado_por == user.id
        assert lote.aprobado_en is not None

    async def test_aprobar_lote_ya_aprobado_retorna_409(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        lote = await _create_lote(db_session, tenant.id, materia.id, user.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        await svc.aprobar_lote(lote_id=lote.id, aprobado_por=user.id)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await svc.aprobar_lote(lote_id=lote.id, aprobado_por=user.id)
        assert exc.value.status_code == 409

    async def test_rechazar_lote_cancela_mensajes(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        lote = await _create_lote(db_session, tenant.id, materia.id, user.id, total=2)

        for i in range(2):
            await _create_comunicacion(
                db_session, tenant.id, materia.id, user.id,
                email=f"alumno{i}@test.com", lote_id=lote.id,
            )

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        result = await svc.rechazar_lote(lote_id=lote.id, actor_id=user.id)

        assert result.estado == "Rechazado"
        assert result.mensajes_cancelados == 2

        await db_session.refresh(lote)
        assert lote.estado == EstadoLote.RECHAZADO
        assert lote.rechazado_en is not None

        # Check comunicaciones are canceled
        stmt = select(Comunicacion).where(
            Comunicacion.lote_id == lote.id,
            Comunicacion.estado == EstadoComunicacion.CANCELADO,
        )
        rows = await db_session.execute(stmt)
        cancelados = list(rows.scalars().all())
        assert len(cancelados) == 2


# ===== 9.3 Tests de seguimiento =====


class TestSeguimiento:
    async def test_obtener_detalle_lote_con_distribucion(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        lote = await _create_lote(db_session, tenant.id, materia.id, user.id, total=4)

        # Create 4 comunicaciones with various states
        estados = [
            EstadoComunicacion.PENDIENTE,
            EstadoComunicacion.ENVIADO,
            EstadoComunicacion.ERROR,
            EstadoComunicacion.CANCELADO,
        ]
        for i, est in enumerate(estados):
            await _create_comunicacion(
                db_session, tenant.id, materia.id, user.id,
                email=f"alumno{i}@test.com", lote_id=lote.id, estado=est,
            )

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        detalle = await svc.obtener_detalle_lote(lote_id=lote.id)

        assert detalle.id == lote.id
        assert detalle.total_mensajes == 4
        assert detalle.distribucion_estados.pendiente == 1
        assert detalle.distribucion_estados.enviado == 1
        assert detalle.distribucion_estados.error == 1
        assert detalle.distribucion_estados.cancelado == 1
        assert detalle.distribucion_estados.enviando == 0

    async def test_consultar_lote_inexistente_retorna_404(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await svc.obtener_detalle_lote(lote_id=uuid.uuid4())
        assert exc.value.status_code == 404

    async def test_listar_por_materia_retorna_paginado(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        for i in range(5):
            await _create_comunicacion(
                db_session, tenant.id, materia.id, user.id,
                email=f"alumno{i}@test.com",
            )

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        result = await svc.listar_por_materia(materia_id=materia.id, offset=0, limit=3)

        assert len(result.items) == 3
        assert result.total == 5
        assert result.offset == 0
        assert result.limit == 3

    async def test_distribucion_retorna_conteos_correctos(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        # Create 3 comunicaciones with different states
        for est in [EstadoComunicacion.PENDIENTE, EstadoComunicacion.ENVIADO, EstadoComunicacion.ERROR]:
            await _create_comunicacion(
                db_session, tenant.id, materia.id, user.id,
                email="test@test.com", estado=est,
            )

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        dist = await svc.obtener_distribucion(materia_id=materia.id)

        assert dist.pendiente == 1
        assert dist.enviado == 1
        assert dist.error == 1
        assert dist.enviando == 0
        assert dist.cancelado == 0


# ===== 9.4 Tests de cifrado =====


class TestCifrado:
    async def test_destinatario_se_almacena_cifrado(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        await svc.enviar_individual(
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=materia.id,
            destinatario_email="alumno@test.com",
            actor_id=user.id,
        )

        # Read raw from DB (bypassing ORM decryption)
        from sqlalchemy import text
        result = await db_session.execute(
            text("SELECT destinatario FROM comunicacion WHERE tenant_id = :tid"),
            {"tid": tenant.id},
        )
        raw = result.scalar()
        # Should be encrypted (not plain text)
        assert raw is not None
        assert raw != "alumno@test.com"
        # Encrypted strings are base64 encoded
        import base64
        try:
            base64.b64decode(raw)
            is_encrypted = True
        except Exception:
            is_encrypted = False
        assert is_encrypted, "destinatario should be encrypted in DB"

    async def test_destinatario_se_lee_desencriptado(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        await svc.enviar_individual(
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=materia.id,
            destinatario_email="alumno2@test.com",
            actor_id=user.id,
        )

        # Read via ORM (should auto-decrypt)
        stmt = select(Comunicacion).where(Comunicacion.tenant_id == tenant.id)
        result = await db_session.execute(stmt)
        c = result.scalar_one()
        assert c.destinatario == "alumno2@test.com"


# ===== 9.5 Tests de tenant isolation =====


class TestTenantIsolation:
    async def test_tenant_a_no_ve_comunicaciones_de_tenant_b(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user_a, tenant_a = await _setup_tenant_with_user(db_session)
        user_b, tenant_b = await _setup_tenant_with_user(db_session)
        materia_a = await _create_materia(db_session, tenant_a.id)
        materia_b = await _create_materia(db_session, tenant_b.id)

        # Create comunicacion for tenant A
        await _create_comunicacion(
            db_session, tenant_a.id, materia_a.id, user_a.id,
            email="alumno_a@test.com",
        )
        # Create comunicacion for tenant B
        await _create_comunicacion(
            db_session, tenant_b.id, materia_b.id, user_b.id,
            email="alumno_b@test.com",
        )

        # Tenant A should see only theirs
        from app.repositories.comunicacion_repository import ComunicacionRepository
        repo_a = ComunicacionRepository(db_session, tenant_a.id)
        coms_a = await repo_a.list_by_materia(materia_a.id)
        assert len(coms_a) == 1
        assert coms_a[0].destinatario == "alumno_a@test.com"

        # Tenant A should not see B's
        coms_b_from_a = await repo_a.list_by_materia(materia_b.id)
        assert len(coms_b_from_a) == 0

    async def test_tenant_a_no_ve_lotes_de_tenant_b(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user_a, tenant_a = await _setup_tenant_with_user(db_session)
        user_b, tenant_b = await _setup_tenant_with_user(db_session)
        materia_a = await _create_materia(db_session, tenant_a.id)
        materia_b = await _create_materia(db_session, tenant_b.id)

        await _create_lote(db_session, tenant_a.id, materia_a.id, user_a.id)
        await _create_lote(db_session, tenant_b.id, materia_b.id, user_b.id)

        from app.repositories.lote_comunicacion_repository import LoteComunicacionRepository
        repo_a = LoteComunicacionRepository(db_session, tenant_a.id)
        lotes = await repo_a.list_pendientes()
        assert len(lotes) == 1
        assert lotes[0].materia_id == materia_a.id


# ===== 9.6 Tests de auditoría =====


class TestAuditoria:
    async def test_envio_individual_genera_audit(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        await svc.enviar_individual(
            asunto="Test", cuerpo="Cuerpo",
            materia_id=materia.id, destinatario_email="alumno@test.com",
            actor_id=user.id,
        )

        stmt = select(AuditLog).where(
            AuditLog.tenant_id == tenant.id,
            AuditLog.accion == "COMUNICACION_ENVIAR",
        )
        result = await db_session.execute(stmt)
        logs = list(result.scalars().all())
        assert len(logs) >= 1
        assert logs[0].materia_id == materia.id
        assert logs[0].actor_id == user.id

    async def test_envio_masivo_genera_audit_con_lote_id(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        result = await svc.enviar_masivo(
            asunto="Test", cuerpo="Cuerpo",
            materia_id=materia.id,
            destinatarios=["a@test.com", "b@test.com"],
            actor_id=user.id,
        )

        stmt = select(AuditLog).where(
            AuditLog.tenant_id == tenant.id,
            AuditLog.accion == "COMUNICACION_ENVIAR",
        )
        rows = await db_session.execute(stmt)
        logs = list(rows.scalars().all())
        assert len(logs) >= 1
        # The audit log for envío masivo has detalle with lote_id
        assert logs[0].materia_id == materia.id

    async def test_aprobacion_lote_genera_audit(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        lote = await _create_lote(db_session, tenant.id, materia.id, user.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        await svc.aprobar_lote(lote_id=lote.id, aprobado_por=user.id)

        stmt = select(AuditLog).where(
            AuditLog.tenant_id == tenant.id,
            AuditLog.accion == "COMUNICACION_ENVIAR",
        )
        rows = await db_session.execute(stmt)
        logs = list(rows.scalars().all())
        assert len(logs) >= 1

    async def test_rechazo_lote_genera_audit(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)
        lote = await _create_lote(db_session, tenant.id, materia.id, user.id)

        from app.services.comunicacion_service import ComunicacionService

        svc = ComunicacionService(db_session, tenant.id)
        await svc.rechazar_lote(lote_id=lote.id, actor_id=user.id)

        stmt = select(AuditLog).where(
            AuditLog.tenant_id == tenant.id,
            AuditLog.accion == "COMUNICACION_ENVIAR",
        )
        rows = await db_session.execute(stmt)
        logs = list(rows.scalars().all())
        assert len(logs) >= 1


# ===== 9.7 Tests de worker =====


class TestWorker:
    async def test_find_pendientes_procesables_sin_lote(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        # Create a Pendiente individual (sin lote) — should be found
        await _create_comunicacion(
            db_session, tenant.id, materia.id, user.id,
            email="alumno@test.com",
            estado=EstadoComunicacion.PENDIENTE,
        )
        # Create a non-Pendiente — should NOT be found
        await _create_comunicacion(
            db_session, tenant.id, materia.id, user.id,
            email="alumno2@test.com",
            estado=EstadoComunicacion.ENVIADO,
        )

        from app.repositories.comunicacion_repository import ComunicacionRepository
        repo = ComunicacionRepository(db_session, tenant.id)
        pendientes = await repo.find_pendientes_para_procesar(limit=10)
        assert len(pendientes) == 1
        assert pendientes[0].estado == EstadoComunicacion.PENDIENTE
        assert pendientes[0].lote_id is None

    async def test_omite_pendientes_con_lote_no_aprobado(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        # Create lote PENDIENTE (not approved)
        lote = await _create_lote(db_session, tenant.id, materia.id, user.id)
        await _create_comunicacion(
            db_session, tenant.id, materia.id, user.id,
            email="alumno@test.com", lote_id=lote.id,
            estado=EstadoComunicacion.PENDIENTE,
        )

        from app.repositories.comunicacion_repository import ComunicacionRepository
        repo = ComunicacionRepository(db_session, tenant.id)
        pendientes = await repo.find_pendientes_para_procesar(limit=10)
        # Should NOT include the one with lote no aprobado
        assert len(pendientes) == 0

    async def test_incluye_pendientes_con_lote_aprobado(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        lote = await _create_lote(db_session, tenant.id, materia.id, user.id)
        lote.estado = EstadoLote.APROBADO
        await db_session.flush()

        await _create_comunicacion(
            db_session, tenant.id, materia.id, user.id,
            email="alumno@test.com", lote_id=lote.id,
            estado=EstadoComunicacion.PENDIENTE,
        )

        from app.repositories.comunicacion_repository import ComunicacionRepository
        repo = ComunicacionRepository(db_session, tenant.id)
        pendientes = await repo.find_pendientes_para_procesar(limit=10)
        assert len(pendientes) == 1

    async def test_procesa_pendientes_sin_lote_individuales(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        c = await _create_comunicacion(
            db_session, tenant.id, materia.id, user.id,
            email="alumno@test.com",
            estado=EstadoComunicacion.PENDIENTE,
        )

        # Simulate worker processing (just transition)
        from app.repositories.comunicacion_repository import ComunicacionRepository
        repo = ComunicacionRepository(db_session, tenant.id)

        # Transition to Enviando
        await repo.actualizar_estado(
            comunicacion_id=c.id,
            estado=EstadoComunicacion.ENVIANDO,
        )
        await db_session.refresh(c)
        assert c.estado == EstadoComunicacion.ENVIANDO

    async def test_worker_transiciona_a_enviando(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        c = await _create_comunicacion(
            db_session, tenant.id, materia.id, user.id,
            email="alumno@test.com",
            estado=EstadoComunicacion.PENDIENTE,
        )

        # Update to Enviando
        from app.repositories.comunicacion_repository import ComunicacionRepository
        repo = ComunicacionRepository(db_session, tenant.id)
        await repo.actualizar_estado(
            comunicacion_id=c.id,
            estado=EstadoComunicacion.ENVIANDO,
        )
        await db_session.refresh(c)
        assert c.estado == EstadoComunicacion.ENVIANDO

    async def test_worker_registra_enviado_con_timestamp(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        c = await _create_comunicacion(
            db_session, tenant.id, materia.id, user.id,
            email="alumno@test.com",
            estado=EstadoComunicacion.PENDIENTE,
        )

        from app.repositories.comunicacion_repository import ComunicacionRepository
        repo = ComunicacionRepository(db_session, tenant.id)
        now = datetime.now(timezone.utc)
        await repo.actualizar_estado(
            comunicacion_id=c.id,
            estado=EstadoComunicacion.ENVIADO,
            enviado_at=now,
        )
        await db_session.refresh(c)
        assert c.estado == EstadoComunicacion.ENVIADO
        assert c.enviado_at is not None

    async def test_worker_registra_error_con_mensaje(self, db_session, test_engine):
        await _ensure_table(test_engine)
        user, tenant = await _setup_tenant_with_user(db_session)
        materia = await _create_materia(db_session, tenant.id)

        c = await _create_comunicacion(
            db_session, tenant.id, materia.id, user.id,
            email="alumno@test.com",
            estado=EstadoComunicacion.PENDIENTE,
        )

        from app.repositories.comunicacion_repository import ComunicacionRepository
        repo = ComunicacionRepository(db_session, tenant.id)
        await repo.actualizar_estado(
            comunicacion_id=c.id,
            estado=EstadoComunicacion.ERROR,
            error_msg="SMTP connection refused",
        )
        await db_session.refresh(c)
        assert c.estado == EstadoComunicacion.ERROR
        assert c.error_msg == "SMTP connection refused"


# ===== 9.0 Tests de enmascaramiento =====


class TestEnmascaramiento:
    def test_enmascara_email_largo(self):
        from app.services.comunicacion_service import ComunicacionService
        result = ComunicacionService._enmascarar_email("alumno123@test.com")
        assert result == "alum***@test.com"

    def test_enmascara_email_corto(self):
        from app.services.comunicacion_service import ComunicacionService
        result = ComunicacionService._enmascarar_email("ab@test.com")
        assert result == "a***@test.com"

    def test_enmascara_email_sin_arroba(self):
        from app.services.comunicacion_service import ComunicacionService
        result = ComunicacionService._enmascarar_email("invalido")
        assert result == "invalido"
