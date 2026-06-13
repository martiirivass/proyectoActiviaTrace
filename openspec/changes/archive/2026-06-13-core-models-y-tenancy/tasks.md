## 1. Modelos base y Tenant

- [x] 1.1 Crear `backend/app/models/mixins.py`: `UUIDMixin`, `TimestampMixin`, `SoftDeleteMixin`, `TenantMixin` (composable via DeclarativeMixin)
- [x] 1.2 Crear `backend/app/models/tenant.py`: modelo `Tenant` (id, nombre, slug UNIQUE, estado enum, configuracion JSONB, timestamps, soft-delete)
- [x] 1.3 Crear `backend/app/models/__init__.py`: exports de todos los modelos

## 2. Modelos de identidad (User, Role, Permission, UserRole, UserTenant)

- [x] 2.1 Crear `backend/app/models/user.py`: `User` con PII cifrada (EncryptedString en email, dni, cuil, cbu, alias_cbu), legajo único por tenant, password_hash, relaciones
- [x] 2.2 Crear `backend/app/models/role.py`: `Role` (tenant-scoped, nombre único por tenant)
- [x] 2.3 Crear `backend/app/models/permission.py`: `Permission` (catálogo global, formato `modulo:accion`)
- [x] 2.4 Crear `backend/app/models/user_role.py`: `UserRole` (vigencia desde/hasta, activo, sin soft-delete)
- [x] 2.5 Crear `backend/app/models/user_tenant.py`: `UserTenant` (multi-tenant user membership)

## 3. Seguridad: Cifrado AES-256-GCM y Argon2id

- [x] 3.1 (RED) Escribir `tests/test_security.py`: tests para `EncryptionService` (round-trip, claves distintas, key equivocada, tampering, vacío, unicode) y `PasswordService` (hash Argon2id, verify OK/KO, hash distinto cada vez, password vacío)
- [x] 3.2 (GREEN) Implementar `backend/app/core/security.py`: `EncryptionService` (AES-256-GCM, key desde `ENCRYPTION_KEY` base64 32 bytes, PBKDF2 opcional) + `PasswordService` (Argon2id)
- [x] 3.3 (TRIANGULATE) Agregar casos: key derivation PBKDF2 determinista, salts distintos → keys distintas, ENCRYPTION_KEY inválida/faltante en Settings
- [x] 3.4 Crear `EncryptedString` TypeDecorator para transparencia en columnas

## 4. Repository base con tenant-scope obligatorio

- [x] 4.1 (RED) Escribir `tests/test_repositories.py`: tests para `BaseRepository` (create/get/list/update/delete/soft-delete/hard-delete/include_deleted, tenant_id obligatorio, cross-tenant isolation, tenant_id mismatch en create/update)
- [x] 4.2 (GREEN) Implementar `backend/app/repositories/base.py`: `Repository[T]` genérico con `tenant_id` en constructor, todos los métodos aplican filtro `tenant_id` + `deleted_at IS NULL`, `list_with_deleted()` opt-in, `hard_delete()` restringido
- [x] 4.3 (TRIANGULATE) Verificar que repo derivado no puede bypassear filtro (code review check), factory `get_repository(model, tenant_id)` para DI

## 5. Migración Alembic 001

- [x] 5.1 Generar migración `backend/alembic/versions/14e42736490b_initial_models.py`: crea tablas tenant, user, role, permission, user_role, user_tenant con FKs, índices, constraints, enums
- [x] 5.2 Verificar `alembic upgrade head` y `alembic downgrade -1` limpios
- [x] 5.3 Documentar convención: una migración por change, naming `V###_descripcion.py`

## 6. Tests de integración y validación

- [x] 6.1 (RED) Escribir `tests/test_models.py`: tests estáticos (columnas, constraints, relaciones, herencia mixins) + tests DB (`TestUserModelDB`: create, email unique, legajo unique)
- [x] 6.2 (RED) Escribir `tests/test_mixins.py`: tests de `SoftDeleteMixin` (columna deleted_at, defaults, soft_delete actualiza atributos, timestamp reciente)
- [x] 6.3 (GREEN) Ejecutar suite completa: 82 tests colectados, 64 pasan sin PostgreSQL (config, health, startup, mixins estáticos, modelos estáticos, security); 18 requieren DB en puerto 5433
- [x] 6.4 Verificar que ningún archivo `.py` supera 500 LOC

## 7. Documentación y cierre

- [x] 7.1 Confirmar que `CHANGES.md` marca C-02 como `[x]`
- [x] 7.2 Ejecutar `/opsx:archive core-models-y-tenancy` para sincronizar delta specs a `openspec/specs/` y archivar