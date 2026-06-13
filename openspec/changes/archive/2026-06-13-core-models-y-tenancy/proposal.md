## Why

activia-trace es una plataforma multi-tenant que orquesta datos académicos sobre Moodle. **Cada institución (tenant) debe estar completamente aislada a nivel de datos** — un query sin scope de tenant es un bug crítico. Además, el sistema maneja PII sensible (DNI, CUIL, CBU, email) que **debe cifrarse en reposo (AES-256)** y los passwords con Argon2id. Sin estos cimientos, ningún módulo posterior puede construirse con seguridad.

Este change establece: el modelo raíz `Tenant`, el mixin base con soft-delete y tenant-scope, el repository genérico que **fuerza el filtro por tenant_id por defecto** (ADR-002), utilidades de cifrado AES-256, y la migración Alembic 001. Es el cimiento crítico sobre el que se apoyan auth (C-03), RBAC (C-04) y todo el dominio académico.

## What Changes

- **Nuevo**: Modelo `Tenant` (entidad raíz multi-tenant)
- **Nuevo**: Mixin `TenantScopedMixin` — `id` (UUID), `tenant_id` (FK), `created_at`, `updated_at`, `deleted_at` (soft delete)
- **Nuevo**: `BaseRepository` con **tenant-scope obligatorio** — todo query filtra por `tenant_id` del contexto; query sin scope = error en review
- **Nuevo**: `EncryptionService` (AES-256-GCM) para atributos `[cifrado]` (DNI, CUIL, CBU, email PII) — round-trip testado
- **Nuevo**: `PasswordService` (Argon2id) para hash/verify de passwords
- **Nuevo**: Modelos de identidad: `User`, `Role`, `Permission`, `UserRole`, `UserTenant` (con PII cifrada en User)
- **Nuevo**: Migración Alembic `001_initial_models` — crea todas las tablas arriba
- **Nuevo**: Tests de aislamiento multi-tenant, soft delete, cifrado round-trip, mixin timestamps
- **BREAKING**: Cualquier repository futuro DEBE heredar de `BaseRepository` y recibir `tenant_id` en el contexto

## Capabilities

### New Capabilities

- `multi-tenancy`: Aislamiento row-level por tenant_id en todas las tablas; repository base que fuerza scope
- `identity-management`: Modelos User, Role, Permission, UserRole, UserTenant con relaciones y PII cifrada
- `core-models`: Mixin base (UUID, timestamps, soft-delete), Tenant raíz, convención de migraciones
- `security-encryption`: AES-256-GCM para PII en reposo, Argon2id para passwords, helpers de cifrado/descifrado
- `rbac-fine-grained`: Catálogo Permission (`modulo:accion`), Role, matriz RolePermiso (datos, no hardcode)
- `core-repositories`: Repository genérico con tenant-scope, CRUD, soft-delete, include_deleted opt-in

### Modified Capabilities

- (ninguna — es el primer change de dominio)

## Impact

- **Código nuevo**: `backend/app/models/` (7 archivos), `backend/app/repositories/base.py`, `backend/app/core/security.py`, `backend/alembic/versions/14e42736490b_initial_models.py`
- **Tests**: `backend/tests/test_models.py`, `test_repositories.py`, `test_security.py`, `test_mixins.py`
- **Dependencias**: `argon2-cffi`, `cryptography` (ya en pyproject.toml de C-01)
- **APIs**: Ninguna expuesta aún — son modelos/repos internos; auth (C-03) expondrá login/refresh
- **Sistemas**: Base para todo el dominio académico; sin esto no hay C-03, C-04, C-06...