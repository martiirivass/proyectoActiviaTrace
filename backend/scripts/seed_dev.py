#!/usr/bin/env python
"""
seed_dev.py — Inicializa datos de desarrollo para activia-trace.

Crea o recupera de forma idempotente:
  - Tenant de desarrollo
  - Usuarios: admin@admin.com, profesor@test.com
  - 3 carreras, 9 materias, 4 cohortes, 11 dictados
  - Asignaciones docentes para ambos usuarios

Uso:
  docker compose exec api python scripts/seed_dev.py

Se puede correr N veces sin romper nada.
"""
import os
import sys

# Asegura que el directorio raíz del proyecto esté en sys.path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_app_root = os.path.abspath(os.path.join(_script_dir, ".."))
if _app_root not in sys.path:
    sys.path.insert(0, _app_root)

import asyncio
import uuid
from datetime import date, datetime

from sqlalchemy import select, and_

from app.core.database import async_session_factory
from app.core.security import PasswordService
from app.models import (
    Tenant, User, UserTenant, Role, UserRole,
    Carrera, Materia, Cohorte, Dictado, Asignacion,
)
from app.models.mixins import SoftDeleteMixin


# ────────────────────── Helper ──────────────────────


async def get_or_create(session, model, filters: dict, defaults: dict) -> tuple:
    """Busca por filters, crea con filters+defaults si no existe.

    Devuelve (instancia, creado: bool).
    """
    stmt = select(model).where(
        *[getattr(model, k) == v for k, v in filters.items()]
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing, False

    instance = model(**filters, **defaults)
    session.add(instance)
    await session.flush()
    return instance, True


# ────────────────────── Seed ──────────────────────


async def seed():
    print("🌱  activia-trace — seed_dev.py")
    print("=" * 50)

    async with async_session_factory() as session:

        # ── 1. Tenant ──
        tenant, created = await get_or_create(
            session, Tenant,
            filters={"code": "UNIVPRUEBA"},
            defaults={"name": "Universidad de Prueba", "is_active": True},
        )
        status = "creado" if created else "ya existe"
        print(f"  [1/8] Tenant «{tenant.code}» — {status}")

        # ── 2. Roles (ya existen de la migración, los recuperamos) ──
        roles = {}
        for name in ("ADMIN", "PROFESOR", "COORDINADOR", "TUTOR", "NEXO", "FINANZAS"):
            stmt = select(Role).where(Role.name == name)
            result = await session.execute(stmt)
            role = result.scalar_one_or_none()
            if role:
                roles[name] = role
        print(f"  [2/8] Roles cargados: {', '.join(roles.keys())}")

        # ── 3. Usuarios ──
        users_data = [
            {
                "email": "admin@admin.com",
                "password": "admin123",
                "nombre": "Admin",
                "apellido": "Sistema",
                "rol": "ADMIN",
            },
            {
                "email": "profesor@test.com",
                "password": "profesor123",
                "nombre": "Profesor",
                "apellido": "Prueba",
                "rol": "PROFESOR",
            },
        ]

        users = {}
        for ud in users_data:
            user, created = await get_or_create(
                session, User,
                filters={"email": ud["email"]},
                defaults={
                    "nombre": ud["nombre"],
                    "apellido": ud["apellido"],
                    "password_hash": PasswordService.hash(ud["password"]),
                    "tenant_id": tenant.id,
                },
            )
            users[ud["rol"]] = user
            status = "creado" if created else "ya existe"
            print(f"  [3/8] Usuario «{ud['email']}» — {status}")

            # UserTenant
            await get_or_create(
                session, UserTenant,
                filters={"user_id": user.id, "tenant_id": tenant.id},
                defaults={"is_active": True},
            )

            # UserRole
            await get_or_create(
                session, UserRole,
                filters={
                    "user_id": user.id,
                    "role_id": roles[ud["rol"]].id,
                    "tenant_id": tenant.id,
                },
                defaults={},
            )

        admin = users["ADMIN"]
        profesor = users["PROFESOR"]

        # ── 4. Carreras ──
        carreras_def = [
            {"codigo": "LI", "nombre": "Licenciatura en Informática"},
            {"codigo": "LM", "nombre": "Licenciatura en Matemática"},
            {"codigo": "CP", "nombre": "Contador Público"},
        ]
        carreras = {}
        for cd in carreras_def:
            carrera, created = await get_or_create(
                session, Carrera,
                filters={"codigo": cd["codigo"], "tenant_id": tenant.id},
                defaults={"nombre": cd["nombre"]},
            )
            carreras[cd["codigo"]] = carrera
            status = "creada" if created else "ya existe"
            print(f"  [4/8] Carrera «{cd['codigo']}» — {status}")

        # ── 5. Materias ──
        materias_def = [
            ("INFO01", "Programación I"),
            ("INFO02", "Programación II"),
            ("INFO03", "Base de Datos I"),
            ("INFO04", "Redes"),
            ("INFO05", "Ingeniería de Software"),
            ("MATE01", "Análisis Matemático I"),
            ("MATE02", "Álgebra Lineal"),
            ("CONT01", "Contabilidad Básica"),
            ("CONT02", "Contabilidad de Costos"),
        ]
        materias = {}
        for codigo, nombre in materias_def:
            materia, created = await get_or_create(
                session, Materia,
                filters={"codigo": codigo, "tenant_id": tenant.id},
                defaults={"nombre": nombre},
            )
            materias[codigo] = materia
            status = "creada" if created else "ya existe"
            print(f"  [5/8] Materia «{codigo}» — {status}")

        # ── 6. Cohortes ──
        cohortes_def = [
            {"nombre": "2024 - Informática", "anio": 2024, "carrera": "LI"},
            {"nombre": "2025 - Informática", "anio": 2025, "carrera": "LI"},
            {"nombre": "2024 - Matemática",  "anio": 2024, "carrera": "LM"},
            {"nombre": "2025 - Contador",    "anio": 2025, "carrera": "CP"},
        ]
        cohortes = []
        for cd in cohortes_def:
            carrera = carreras[cd["carrera"]]
            coh, created = await get_or_create(
                session, Cohorte,
                filters={
                    "carrera_id": carrera.id,
                    "nombre": cd["nombre"],
                    "anio": cd["anio"],
                    "tenant_id": tenant.id,
                },
                defaults={},
            )
            cohortes.append(coh)
            status = "creado" if created else "ya existe"
            print(f"  [6/8] Cohorte «{cd['nombre']}» — {status}")

        # ── 7. Dictados (comisiones) ──
        # (materia_codigo, carrera_codigo, cohorte_index, nombre)
        dictados_def = [
            ("INFO01", "LI", 0, "Programación I - 2024"),
            ("INFO02", "LI", 0, "Programación II - 2024"),
            ("INFO03", "LI", 0, "Base de Datos I - 2024"),
            ("INFO04", "LI", 0, "Redes - 2024"),
            ("INFO05", "LI", 0, "Ing. de Software - 2024"),
            ("INFO01", "LI", 1, "Programación I - 2025"),
            ("INFO02", "LI", 1, "Programación II - 2025"),
            ("MATE01", "LM", 2, "Análisis Matemático I - 2024"),
            ("MATE02", "LM", 2, "Álgebra Lineal - 2024"),
            ("CONT01", "CP", 3, "Contabilidad Básica - 2025"),
            ("CONT02", "CP", 3, "Contabilidad de Costos - 2025"),
        ]
        dictados = []
        for mat_cod, carr_cod, coh_idx, nombre in dictados_def:
            materia = materias[mat_cod]
            carrera = carreras[carr_cod]
            cohorte = cohortes[coh_idx]
            d, created = await get_or_create(
                session, Dictado,
                filters={
                    "materia_id": materia.id,
                    "cohorte_id": cohorte.id,
                    "tenant_id": tenant.id,
                },
                defaults={
                    "carrera_id": carrera.id,
                    "nombre": nombre,
                },
            )
            dictados.append(d)
            status = "creado" if created else "ya existe"
            print(f"  [7/8] Dictado «{nombre}» — {status}")

        # ── 8. Asignaciones docentes ──
        hoy = date.today()
        asignaciones_hechas = 0
        for user, rol in [(admin, "ADMIN"), (profesor, "PROFESOR")]:
            for d in dictados:
                # Chequear si ya existe esta asignación
                stmt = select(Asignacion).where(
                    and_(
                        Asignacion.usuario_id == user.id,
                        Asignacion.materia_id == d.materia_id,
                        Asignacion.cohorte_id == d.cohorte_id,
                        Asignacion.rol == rol,
                        Asignacion.is_deleted == False,
                    )
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    continue

                asignacion = Asignacion(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    usuario_id=user.id,
                    rol=rol,
                    materia_id=d.materia_id,
                    carrera_id=d.carrera_id,
                    cohorte_id=d.cohorte_id,
                    dictado_id=d.id,
                    desde=hoy,
                )
                session.add(asignacion)
                asignaciones_hechas += 1
        await session.flush()

        if asignaciones_hechas:
            print(f"  [8/8] Asignaciones creadas: {asignaciones_hechas}")
        else:
            print(f"  [8/8] Asignaciones — ya existen todas")

        # ── Done ──
        await session.commit()

    print("=" * 50)
    print(f"✅  Seed completado")
    print()
    print(f"   Usuarios:")
    print(f"     admin@admin.com     / admin123     (ADMIN)")
    print(f"     profesor@test.com   / profesor123  (PROFESOR)")
    print()
    print(f"   Estructura: {len(carreras)} carreras, {len(materias)} materias,", end=" ")
    print(f"{len(cohortes)} cohortes, {len(dictados)} dictados")
    print()
    print("👉  http://localhost:5173")


if __name__ == "__main__":
    asyncio.run(seed())
