import uuid
from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
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
from app.models.fecha_academica import FechaAcademica, TipoFecha
from app.models.mixins import SoftDeleteMixin
from app.models.programa_materia import ProgramaMateria

pytestmark = pytest.mark.asyncio


# ===== Helper functions =====


async def _ensure_table(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _setup_tenant_with_user(db_session, tenant=None):
    if tenant is None:
        code = f"PRG{uuid.uuid4().hex[:6].upper()}"
        tenant = Tenant(name=f"Programa Test {code}", code=code)
        db_session.add(tenant)
        await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"prg-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Programa",
        apellido="Test",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    return user, tenant


async def _create_carrera(db_session, tenant_id):
    from app.models.carrera import Carrera

    c = Carrera(
        tenant_id=tenant_id,
        codigo=f"CARR-{uuid.uuid4().hex[:6].upper()}",
        nombre="Carrera Test",
    )
    db_session.add(c)
    await db_session.flush()
    return c


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


async def _setup_permission(db_session, tenant, user, name="estructura:gestionar"):
    """Assign a permission to the user for testing."""
    role = Role(
        tenant_id=tenant.id,
        name=f"ROLE-{uuid.uuid4().hex[:6].upper()}",
        description="Test role",
    )
    db_session.add(role)
    await db_session.flush()

    perm = await db_session.execute(
        select(Permission).where(Permission.name == name)
    )
    perm_obj = perm.scalar_one_or_none()
    if perm_obj is None:
        module, action = name.split(":", 1) if ":" in name else (name, name)
        perm_obj = Permission(
            name=name,
            module=module,
            action=action,
            description=f"Permiso {name}",
        )
        db_session.add(perm_obj)
        await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm_obj.id, tenant_id=tenant.id)
    db_session.add(rp)

    ur = UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant.id)
    db_session.add(ur)
    await db_session.flush()
    return role


# =====================================================================
# 7.1 Tests de modelo ProgramaMateria
# =====================================================================


class TestProgramaMateriaModel:
    def test_inherits_soft_delete(self):
        assert issubclass(ProgramaMateria, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = ProgramaMateria.__table__.c["id"]
        assert col.primary_key

    def test_has_required_columns(self):
        cols = ProgramaMateria.__table__.c
        assert "tenant_id" in cols
        assert "materia_id" in cols
        assert "carrera_id" in cols
        assert "cohorte_id" in cols
        assert "titulo" in cols
        assert "referencia_archivo" in cols
        assert "cargado_at" in cols

    def test_has_timestamps(self):
        assert "created_at" in ProgramaMateria.__table__.c
        assert "updated_at" in ProgramaMateria.__table__.c

    def test_unique_constraint(self):
        # Check unique constraint on (materia_id, carrera_id, cohorte_id)
        constraints = [c for c in ProgramaMateria.__table__.constraints if c.name == "uq_programa_materia_carrera_cohorte"]
        assert len(constraints) == 1


async def test_create_programa_materia(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    programa = ProgramaMateria(
        tenant_id=tenant.id,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        titulo="Programa 2026",
        referencia_archivo="s3://bucket/programa.pdf",
    )
    db_session.add(programa)
    await db_session.flush()

    assert programa.id is not None
    assert isinstance(programa.id, uuid.UUID)
    assert programa.titulo == "Programa 2026"
    assert programa.referencia_archivo == "s3://bucket/programa.pdf"
    assert programa.cargado_at is not None
    assert programa.is_deleted is False
    assert programa.deleted_at is None


async def test_programa_materia_unique_constraint(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    p1 = ProgramaMateria(
        tenant_id=tenant.id,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        titulo="Programa 2026",
    )
    db_session.add(p1)
    await db_session.flush()

    p2 = ProgramaMateria(
        tenant_id=tenant.id,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        titulo="Programa 2026 v2",
    )
    db_session.add(p2)
    with pytest.raises(Exception) as exc:
        await db_session.flush()
    err_str = str(exc.value)
    assert "violates unique constraint" in err_str or "llave duplicada" in err_str or "UniqueViolation" in err_str


async def test_programa_materia_soft_delete(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    programa = ProgramaMateria(
        tenant_id=tenant.id,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        titulo="Programa 2026",
    )
    db_session.add(programa)
    await db_session.flush()

    programa.soft_delete()
    await db_session.flush()

    assert programa.is_deleted is True
    assert programa.deleted_at is not None


async def test_programa_materia_timestamps(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    programa = ProgramaMateria(
        tenant_id=tenant.id,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        titulo="Programa 2026",
    )
    db_session.add(programa)
    await db_session.flush()

    assert programa.created_at is not None
    assert programa.updated_at is not None


# =====================================================================
# 7.2 Tests de modelo FechaAcademica
# =====================================================================


class TestFechaAcademicaModel:
    def test_inherits_soft_delete(self):
        assert issubclass(FechaAcademica, SoftDeleteMixin)

    def test_has_uuid_pk(self):
        col = FechaAcademica.__table__.c["id"]
        assert col.primary_key

    def test_has_required_columns(self):
        cols = FechaAcademica.__table__.c
        assert "tenant_id" in cols
        assert "materia_id" in cols
        assert "cohorte_id" in cols
        assert "tipo" in cols
        assert "numero" in cols
        assert "periodo" in cols
        assert "fecha" in cols
        assert "titulo" in cols

    def test_has_timestamps(self):
        assert "created_at" in FechaAcademica.__table__.c
        assert "updated_at" in FechaAcademica.__table__.c

    def test_unique_constraint(self):
        constraints = [c for c in FechaAcademica.__table__.constraints if c.name == "uq_fecha_materia_cohorte_tipo_numero_periodo"]
        assert len(constraints) == 1

    def test_tipo_enum_values(self):
        assert TipoFecha.PARCIAL.value == "Parcial"
        assert TipoFecha.TP.value == "TP"
        assert TipoFecha.COLOQUIO.value == "Coloquio"
        assert TipoFecha.RECUPERATORIO.value == "Recuperatorio"


async def test_create_fecha_academica_all_types(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    for tipo in TipoFecha:
        fa = FechaAcademica(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=tipo,
            numero=1,
            periodo="2026-1",
            fecha=date(2026, 4, 15),
            titulo=f"{tipo.value} 1",
        )
        db_session.add(fa)
    await db_session.flush()

    stmt = select(FechaAcademica).where(FechaAcademica.tenant_id == tenant.id)
    result = await db_session.execute(stmt)
    fechas = list(result.scalars().all())
    assert len(fechas) == 4


async def test_fecha_academica_unique_constraint(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    f1 = FechaAcademica(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo=TipoFecha.PARCIAL,
        numero=1,
        periodo="2026-1",
        fecha=date(2026, 4, 15),
        titulo="Parcial 1",
    )
    db_session.add(f1)
    await db_session.flush()

    f2 = FechaAcademica(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo=TipoFecha.PARCIAL,
        numero=1,
        periodo="2026-1",
        fecha=date(2026, 5, 15),
        titulo="Parcial 1 duplicado",
    )
    db_session.add(f2)
    with pytest.raises(Exception) as exc:
        await db_session.flush()
    err_str = str(exc.value)
    assert "violates unique constraint" in err_str or "llave duplicada" in err_str or "UniqueViolation" in err_str


async def test_fecha_academica_mismo_tipo_numero_distinto_periodo(db_session, test_engine):
    """Same tipo+numero in different periodo should be allowed."""
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    f1 = FechaAcademica(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo=TipoFecha.PARCIAL,
        numero=1,
        periodo="2026-1",
        fecha=date(2026, 4, 15),
        titulo="Parcial 1",
    )
    db_session.add(f1)
    f2 = FechaAcademica(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo=TipoFecha.PARCIAL,
        numero=1,
        periodo="2026-2",
        fecha=date(2026, 9, 15),
        titulo="Parcial 1 - 2C",
    )
    db_session.add(f2)
    await db_session.flush()

    assert f1.id != f2.id


async def test_fecha_academica_soft_delete(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    fa = FechaAcademica(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo=TipoFecha.PARCIAL,
        numero=1,
        periodo="2026-1",
        fecha=date(2026, 4, 15),
        titulo="Parcial 1",
    )
    db_session.add(fa)
    await db_session.flush()

    fa.soft_delete()
    await db_session.flush()

    assert fa.is_deleted is True
    assert fa.deleted_at is not None


# =====================================================================
# 7.3 Tests de repositorio ProgramaMateriaRepository
# =====================================================================


async def test_repo_programa_list_filtros(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia_a = await _create_materia(db_session, tenant.id)
    materia_b = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.repositories.programa_repository import ProgramaMateriaRepository

    repo = ProgramaMateriaRepository(db_session, tenant.id)

    p1 = await repo.create(
        materia_id=materia_a.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
        titulo="Programa A", referencia_archivo="ref-a",
    )
    p2 = await repo.create(
        materia_id=materia_b.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
        titulo="Programa B", referencia_archivo="ref-b",
    )

    # Filter by materia
    result = await repo.list(materia_id=materia_a.id)
    assert len(result) == 1
    assert result[0].id == p1.id

    # Filter by carrera
    result = await repo.list(carrera_id=carrera.id)
    assert len(result) == 2

    # Filter by cohorte
    result = await repo.list(cohorte_id=cohorte.id)
    assert len(result) == 2

    # Filter combined
    result = await repo.list(materia_id=materia_a.id, carrera_id=carrera.id, cohorte_id=cohorte.id)
    assert len(result) == 1
    assert result[0].id == p1.id

    # No match
    result = await repo.list(materia_id=uuid.uuid4())
    assert len(result) == 0


async def test_repo_programa_tenant_isolation(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant_a = await _setup_tenant_with_user(db_session)
    _, tenant_b = await _setup_tenant_with_user(db_session)
    materia_a = await _create_materia(db_session, tenant_a.id)
    materia_b = await _create_materia(db_session, tenant_b.id)
    carrera_a = await _create_carrera(db_session, tenant_a.id)
    carrera_b = await _create_carrera(db_session, tenant_b.id)
    cohorte_a = await _create_cohorte(db_session, tenant_a.id, carrera_a.id)
    cohorte_b = await _create_cohorte(db_session, tenant_b.id, carrera_b.id)

    from app.repositories.programa_repository import ProgramaMateriaRepository

    repo_a = ProgramaMateriaRepository(db_session, tenant_a.id)
    repo_b = ProgramaMateriaRepository(db_session, tenant_b.id)

    await repo_a.create(materia_id=materia_a.id, carrera_id=carrera_a.id, cohorte_id=cohorte_a.id, titulo="Prog A")
    await repo_b.create(materia_id=materia_b.id, carrera_id=carrera_b.id, cohorte_id=cohorte_b.id, titulo="Prog B")

    list_a = await repo_a.list()
    list_b = await repo_b.list()

    assert len(list_a) == 1
    assert len(list_b) == 1
    assert list_a[0].titulo == "Prog A"
    assert list_b[0].titulo == "Prog B"

    # Tenant B cannot get tenant A's programa
    result = await repo_b.get(list_a[0].id)
    assert result is None


# =====================================================================
# 7.4 Tests de repositorio FechaAcademicaRepository
# =====================================================================


async def test_repo_fecha_list_filtros(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.repositories.fecha_academica_repository import FechaAcademicaRepository
    from app.models.fecha_academica import TipoFecha

    repo = FechaAcademicaRepository(db_session, tenant.id)

    f1 = await repo.create(
        materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL,
        numero=1, periodo="2026-1", fecha=date(2026, 4, 15), titulo="Parcial 1",
    )
    f2 = await repo.create(
        materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.TP,
        numero=1, periodo="2026-1", fecha=date(2026, 4, 10), titulo="TP 1",
    )
    f3 = await repo.create(
        materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL,
        numero=2, periodo="2026-1", fecha=date(2026, 5, 15), titulo="Parcial 2",
    )

    # Filter by materia
    result = await repo.list(materia_id=materia.id)
    assert len(result) == 3

    # Filter by cohorte
    result = await repo.list(cohorte_id=cohorte.id)
    assert len(result) == 3

    # Filter by tipo
    result = await repo.list(tipo=TipoFecha.PARCIAL)
    assert len(result) == 2

    # Filter by periodo
    result = await repo.list(periodo="2026-1")
    assert len(result) == 3

    # Filter combined
    result = await repo.list(materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL, periodo="2026-1")
    assert len(result) == 2

    # Order by fecha ascending
    assert result[0].fecha <= result[1].fecha


async def test_repo_fecha_tenant_isolation(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant_a = await _setup_tenant_with_user(db_session)
    _, tenant_b = await _setup_tenant_with_user(db_session)
    materia_a = await _create_materia(db_session, tenant_a.id)
    materia_b = await _create_materia(db_session, tenant_b.id)
    cohorte_a = await _create_cohorte(db_session, tenant_a.id)
    cohorte_b = await _create_cohorte(db_session, tenant_b.id)

    from app.repositories.fecha_academica_repository import FechaAcademicaRepository
    from app.models.fecha_academica import TipoFecha

    repo_a = FechaAcademicaRepository(db_session, tenant_a.id)
    repo_b = FechaAcademicaRepository(db_session, tenant_b.id)

    await repo_a.create(materia_id=materia_a.id, cohorte_id=cohorte_a.id, tipo=TipoFecha.PARCIAL, numero=1, periodo="2026-1", fecha=date(2026, 4, 15), titulo="P1")
    await repo_b.create(materia_id=materia_b.id, cohorte_id=cohorte_b.id, tipo=TipoFecha.PARCIAL, numero=1, periodo="2026-1", fecha=date(2026, 4, 15), titulo="P1")

    list_a = await repo_a.list()
    list_b = await repo_b.list()

    assert len(list_a) == 1
    assert len(list_b) == 1


# =====================================================================
# 7.5 Tests de servicio ProgramaService
# =====================================================================


async def test_programa_service_create(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.services.programa_service import ProgramaService

    svc = ProgramaService(db_session, tenant.id)
    result = await svc.create(
        materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
        titulo="Programa 2026", referencia_archivo="ref-123",
        actor_id=user.id,
    )

    assert result.id is not None
    assert result.titulo == "Programa 2026"
    assert result.referencia_archivo == "ref-123"
    assert result.cargado_at is not None


async def test_programa_service_duplicate_409(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.services.programa_service import ProgramaService

    svc = ProgramaService(db_session, tenant.id)
    await svc.create(materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="Original", actor_id=user.id)

    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.create(materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="Duplicado", actor_id=user.id)
    assert exc.value.status_code == 409


async def test_programa_service_get_404(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)

    from app.services.programa_service import ProgramaService

    svc = ProgramaService(db_session, tenant.id)
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.get(uuid.uuid4())
    assert exc.value.status_code == 404


async def test_programa_service_update(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.services.programa_service import ProgramaService

    svc = ProgramaService(db_session, tenant.id)
    created = await svc.create(materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="Original", actor_id=user.id)

    updated = await svc.update(created.id, titulo="Actualizado", referencia_archivo="ref-nueva")
    assert updated.titulo == "Actualizado"
    assert updated.referencia_archivo == "ref-nueva"


async def test_programa_service_delete(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.services.programa_service import ProgramaService

    svc = ProgramaService(db_session, tenant.id)
    created = await svc.create(materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="Para borrar", actor_id=user.id)

    await svc.delete(created.id)

    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.get(created.id)
    assert exc.value.status_code == 404


async def test_programa_service_list(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.services.programa_service import ProgramaService

    svc = ProgramaService(db_session, tenant.id)
    await svc.create(materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="P1", actor_id=user.id)

    result = await svc.list(materia_id=materia.id)
    assert len(result) == 1


# =====================================================================
# 7.6 Tests de servicio FechaAcademicaService
# =====================================================================


async def test_fecha_service_create(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService
    from app.models.fecha_academica import TipoFecha

    svc = FechaAcademicaService(db_session, tenant.id)
    result = await svc.create(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo=TipoFecha.PARCIAL, numero=1, periodo="2026-1",
        fecha=date(2026, 4, 15), titulo="Parcial 1",
        actor_id=user.id,
    )

    assert result.id is not None
    assert result.tipo == TipoFecha.PARCIAL
    assert result.numero == 1


async def test_fecha_service_duplicate_409(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService
    from app.models.fecha_academica import TipoFecha

    svc = FechaAcademicaService(db_session, tenant.id)
    await svc.create(materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL, numero=1, periodo="2026-1", fecha=date(2026, 4, 15), titulo="P1", actor_id=user.id)

    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.create(materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL, numero=1, periodo="2026-1", fecha=date(2026, 5, 15), titulo="P1 dup", actor_id=user.id)
    assert exc.value.status_code == 409


async def test_fecha_service_invalid_tipo_422(db_session, test_engine):
    """422 when tipo is not in the enum."""
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService

    svc = FechaAcademicaService(db_session, tenant.id)
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        # tipo is validated at schema level, but service also validates
        await svc.create(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Invalido", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 15), titulo="Bad",
            actor_id=user.id,
        )
    assert exc.value.status_code == 422


async def test_fecha_service_numero_cero_422(db_session, test_engine):
    """422 when numero is 0."""
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService
    from app.models.fecha_academica import TipoFecha

    svc = FechaAcademicaService(db_session, tenant.id)
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.create(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TipoFecha.PARCIAL, numero=0, periodo="2026-1",
            fecha=date(2026, 4, 15), titulo="Bad",
            actor_id=user.id,
        )
    assert exc.value.status_code == 422


async def test_fecha_service_periodo_invalido_422(db_session, test_engine):
    """422 when periodo format is invalid."""
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService
    from app.models.fecha_academica import TipoFecha

    svc = FechaAcademicaService(db_session, tenant.id)
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.create(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TipoFecha.PARCIAL, numero=1, periodo="2026/1",
            fecha=date(2026, 4, 15), titulo="Bad",
            actor_id=user.id,
        )
    assert exc.value.status_code == 422

    with pytest.raises(HTTPException) as exc:
        await svc.create(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TipoFecha.PARCIAL, numero=1, periodo="2026-3",
            fecha=date(2026, 4, 15), titulo="Bad",
            actor_id=user.id,
        )
    assert exc.value.status_code == 422


async def test_fecha_service_get_404(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)

    from app.services.fecha_academica_service import FechaAcademicaService

    svc = FechaAcademicaService(db_session, tenant.id)
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.get(uuid.uuid4())
    assert exc.value.status_code == 404


async def test_fecha_service_update(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService
    from app.models.fecha_academica import TipoFecha

    svc = FechaAcademicaService(db_session, tenant.id)
    created = await svc.create(
        materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL,
        numero=1, periodo="2026-1", fecha=date(2026, 4, 15), titulo="Original",
        actor_id=user.id,
    )

    updated = await svc.update(created.id, titulo="Actualizado", fecha=date(2026, 4, 20))
    assert updated.titulo == "Actualizado"
    assert updated.fecha == date(2026, 4, 20)


async def test_fecha_service_delete(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService
    from app.models.fecha_academica import TipoFecha

    svc = FechaAcademicaService(db_session, tenant.id)
    created = await svc.create(
        materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL,
        numero=1, periodo="2026-1", fecha=date(2026, 4, 15), titulo="Para borrar",
        actor_id=user.id,
    )

    await svc.delete(created.id)

    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.get(created.id)
    assert exc.value.status_code == 404


async def test_fecha_service_list(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService
    from app.models.fecha_academica import TipoFecha

    svc = FechaAcademicaService(db_session, tenant.id)
    await svc.create(materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL, numero=1, periodo="2026-1", fecha=date(2026, 4, 15), titulo="P1", actor_id=user.id)
    await svc.create(materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL, numero=2, periodo="2026-1", fecha=date(2026, 5, 15), titulo="P2", actor_id=user.id)

    result = await svc.list(materia_id=materia.id)
    assert len(result) == 2


async def test_fecha_service_list_filters(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService
    from app.models.fecha_academica import TipoFecha

    svc = FechaAcademicaService(db_session, tenant.id)
    await svc.create(materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL, numero=1, periodo="2026-1", fecha=date(2026, 4, 15), titulo="P1", actor_id=user.id)
    await svc.create(materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.TP, numero=1, periodo="2026-1", fecha=date(2026, 4, 10), titulo="TP1", actor_id=user.id)
    await svc.create(materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL, numero=1, periodo="2026-2", fecha=date(2026, 9, 15), titulo="P1-2C", actor_id=user.id)

    # Filter by tipo
    result = await svc.list(tipo=TipoFecha.PARCIAL)
    assert len(result) == 2

    # Filter by periodo
    result = await svc.list(periodo="2026-1")
    assert len(result) == 2

    # Combined
    result = await svc.list(tipo=TipoFecha.PARCIAL, periodo="2026-1")
    assert len(result) == 1


# =====================================================================
# 7.7 Tests de exportación LMS
# =====================================================================


async def test_fecha_service_exportar_lms_con_fechas(db_session, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService
    from app.models.fecha_academica import TipoFecha

    svc = FechaAcademicaService(db_session, tenant.id)
    await svc.create(materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.PARCIAL, numero=1, periodo="2026-1", fecha=date(2026, 4, 15), titulo="Parcial 1", actor_id=user.id)
    await svc.create(materia_id=materia.id, cohorte_id=cohorte.id, tipo=TipoFecha.TP, numero=1, periodo="2026-1", fecha=date(2026, 4, 10), titulo="TP 1", actor_id=user.id)

    content = await svc.exportar_lms(materia_id=materia.id, cohorte_id=cohorte.id, periodo="2026-1")
    assert isinstance(content, str)
    assert "Parcial 1" in content
    assert "TP 1" in content
    assert "2026-04-15" in content or "15/04" in content


async def test_fecha_service_exportar_lms_sin_fechas(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.services.fecha_academica_service import FechaAcademicaService

    svc = FechaAcademicaService(db_session, tenant.id)
    content = await svc.exportar_lms(materia_id=materia.id, cohorte_id=cohorte.id, periodo="2026-1")
    assert isinstance(content, str)
    assert "No hay fechas" in content or len(content) > 0


async def test_fecha_service_exportar_lms_requiere_materia_id(db_session, test_engine):
    await _ensure_table(test_engine)
    _, tenant = await _setup_tenant_with_user(db_session)

    from app.services.fecha_academica_service import FechaAcademicaService

    svc = FechaAcademicaService(db_session, tenant.id)
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.exportar_lms(materia_id=None, cohorte_id=None, periodo=None)
    assert exc.value.status_code == 422


# =====================================================================
# 7.8 Tests de integración API
# =====================================================================


async def test_api_programas_create_201(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.core.dependencies import get_current_user

    async def override_user():
        from app.schemas.auth import CurrentUser
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    response = await client.post("/api/v1/programas", json={
        "materia_id": str(materia.id),
        "carrera_id": str(carrera.id),
        "cohorte_id": str(cohorte.id),
        "titulo": "Programa 2026",
        "referencia_archivo": "ref-123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Programa 2026"
    assert "id" in data


async def test_api_programas_list(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    # Create one via API
    await client.post("/api/v1/programas", json={
        "materia_id": str(materia.id),
        "carrera_id": str(carrera.id),
        "cohorte_id": str(cohorte.id),
        "titulo": "Programa 2026",
        "referencia_archivo": "ref-123",
    })

    response = await client.get("/api/v1/programas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


async def test_api_programas_get_by_id(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    create_resp = await client.post("/api/v1/programas", json={
        "materia_id": str(materia.id),
        "carrera_id": str(carrera.id),
        "cohorte_id": str(cohorte.id),
        "titulo": "Programa 2026",
        "referencia_archivo": "ref-123",
    })
    prog_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/programas/{prog_id}")
    assert response.status_code == 200
    assert response.json()["titulo"] == "Programa 2026"


async def test_api_programas_update(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    create_resp = await client.post("/api/v1/programas", json={
        "materia_id": str(materia.id),
        "carrera_id": str(carrera.id),
        "cohorte_id": str(cohorte.id),
        "titulo": "Original",
    })
    prog_id = create_resp.json()["id"]

    response = await client.put(f"/api/v1/programas/{prog_id}", json={
        "titulo": "Actualizado",
    })
    assert response.status_code == 200
    assert response.json()["titulo"] == "Actualizado"


async def test_api_programas_delete_204(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id, carrera.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    create_resp = await client.post("/api/v1/programas", json={
        "materia_id": str(materia.id),
        "carrera_id": str(carrera.id),
        "cohorte_id": str(cohorte.id),
        "titulo": "Para borrar",
    })
    prog_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/programas/{prog_id}")
    assert response.status_code == 204


async def test_api_fechas_create_201(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    response = await client.post("/api/v1/fechas-academicas", json={
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "tipo": "Parcial",
        "numero": 1,
        "periodo": "2026-1",
        "fecha": "2026-04-15",
        "titulo": "Parcial 1",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Parcial 1"
    assert "id" in data


async def test_api_fechas_list(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    await client.post("/api/v1/fechas-academicas", json={
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "tipo": "Parcial",
        "numero": 1,
        "periodo": "2026-1",
        "fecha": "2026-04-15",
        "titulo": "Parcial 1",
    })

    response = await client.get("/api/v1/fechas-academicas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


async def test_api_fechas_get_by_id(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    create_resp = await client.post("/api/v1/fechas-academicas", json={
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "tipo": "Parcial",
        "numero": 1,
        "periodo": "2026-1",
        "fecha": "2026-04-15",
        "titulo": "Parcial 1",
    })
    fa_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/fechas-academicas/{fa_id}")
    assert response.status_code == 200
    assert response.json()["titulo"] == "Parcial 1"


async def test_api_fechas_update(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    create_resp = await client.post("/api/v1/fechas-academicas", json={
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "tipo": "Parcial",
        "numero": 1,
        "periodo": "2026-1",
        "fecha": "2026-04-15",
        "titulo": "Original",
    })
    fa_id = create_resp.json()["id"]

    response = await client.put(f"/api/v1/fechas-academicas/{fa_id}", json={
        "titulo": "Actualizado",
        "fecha": "2026-04-20",
    })
    assert response.status_code == 200
    assert response.json()["titulo"] == "Actualizado"


async def test_api_fechas_delete_204(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    create_resp = await client.post("/api/v1/fechas-academicas", json={
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "tipo": "Parcial",
        "numero": 1,
        "periodo": "2026-1",
        "fecha": "2026-04-15",
        "titulo": "Para borrar",
    })
    fa_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/fechas-academicas/{fa_id}")
    assert response.status_code == 204


async def test_api_fechas_exportar_lms(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    # Create some dates
    await client.post("/api/v1/fechas-academicas", json={
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "tipo": "Parcial",
        "numero": 1,
        "periodo": "2026-1",
        "fecha": "2026-04-15",
        "titulo": "Parcial 1",
    })

    response = await client.get(
        f"/api/v1/fechas-academicas/exportar-lms?materia_id={materia.id}&cohorte_id={cohorte.id}&periodo=2026-1"
    )
    assert response.status_code == 200
    assert "Parcial 1" in response.text


async def test_api_fechas_exportar_lms_sin_fechas(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)
    materia = await _create_materia(db_session, tenant.id)
    cohorte = await _create_cohorte(db_session, tenant.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    response = await client.get(
        f"/api/v1/fechas-academicas/exportar-lms?materia_id={materia.id}"
    )
    assert response.status_code == 200
    assert len(response.text) > 0


async def test_api_fechas_exportar_lms_sin_materia_422(db_session, client, test_engine):
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant, user)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    response = await client.get("/api/v1/fechas-academicas/exportar-lms")
    assert response.status_code == 422


async def test_api_requires_auth(db_session, client):
    """Endpoints return 401 without auth."""
    response = await client.get("/api/v1/programas")
    assert response.status_code == 401

    response = await client.get("/api/v1/fechas-academicas")
    assert response.status_code == 401

    response = await client.get("/api/v1/fechas-academicas/exportar-lms?materia_id=" + str(uuid.uuid4()))
    assert response.status_code == 401


async def test_api_requires_permission(db_session, client, test_engine):
    """Endpoints return 403 without correct permission."""
    await _ensure_table(test_engine)
    user, tenant = await _setup_tenant_with_user(db_session)
    # Don't assign any permission

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    async def override_user():
        return CurrentUser(id=user.id, email=user.email, tenant_id=tenant.id, roles=[])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user

    response = await client.get("/api/v1/programas")
    assert response.status_code == 403

    response = await client.get("/api/v1/fechas-academicas")
    assert response.status_code == 403


async def test_api_multi_tenant_isolation(db_session, client, test_engine):
    """Tenant A cannot see tenant B's data."""
    await _ensure_table(test_engine)
    user_a, tenant_a = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant_a, user_a)
    user_b, tenant_b = await _setup_tenant_with_user(db_session)
    await _setup_permission(db_session, tenant_b, user_b)

    materia_a = await _create_materia(db_session, tenant_a.id)
    carrera_a = await _create_carrera(db_session, tenant_a.id)
    cohorte_a = await _create_cohorte(db_session, tenant_a.id, carrera_a.id)

    from app.core.dependencies import get_current_user
    from app.schemas.auth import CurrentUser

    # Create as tenant A
    async def override_user_a():
        return CurrentUser(id=user_a.id, email=user_a.email, tenant_id=tenant_a.id, roles=["admin"])

    app = client._transport.app
    app.dependency_overrides[get_current_user] = override_user_a

    await client.post("/api/v1/programas", json={
        "materia_id": str(materia_a.id),
        "carrera_id": str(carrera_a.id),
        "cohorte_id": str(cohorte_a.id),
        "titulo": "Programa A",
    })

    # Read as tenant B
    async def override_user_b():
        return CurrentUser(id=user_b.id, email=user_b.email, tenant_id=tenant_b.id, roles=["admin"])

    app.dependency_overrides[get_current_user] = override_user_b

    response = await client.get("/api/v1/programas")
    assert response.status_code == 200
    assert len(response.json()) == 0


# =====================================================================
# 7.9 Verificar cobertura
# =====================================================================
# Note: coverage verification is done via pytest-cov at the CLI level.
# This test is a placeholder to mark task 7.9 as testable.
# Actual coverage check: pytest --cov=app.models.programa_materia --cov=app.models.fecha_academica --cov=app.repositories.programa_repository --cov=app.repositories.fecha_academica_repository --cov=app.services.programa_service --cov=app.services.fecha_academica_service --cov=app.schemas.programas --cov=app.schemas.fechas_academicas --cov=app.api.v1.routers.programas --cov=app.api.v1.routers.fechas_academicas --cov-fail-under=80 tests/
