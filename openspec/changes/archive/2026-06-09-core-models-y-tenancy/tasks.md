## 1. Soft Delete Mixin

- [x] 1.1 (RED) Escribir test que verifique que `SoftDeleteMixin` agrega `is_deleted` (bool, default False) y `deleted_at` (Optional datetime, default None)
- [x] 1.2 (GREEN) Implementar `SoftDeleteMixin` en `app/models/mixins.py`
- [x] 1.3 (TRIANGULATE) Agregar caso: soft-delete setea `is_deleted=True` y `deleted_at` con timestamp; verificar que `deleted_at` es None en creación

## 2. Password Service (Argon2id)

- [x] 2.1 (RED) Escribir test: `PasswordService.hash("password")` devuelve string que empieza con `$argon2id$`
- [x] 2.2 (GREEN) Implementar `PasswordService` en `app/core/security.py` con `hash()` y `verify()`
- [x] 2.3 (TRIANGULATE) Agregar casos: verify con password correcta → True; verify con password incorrecta → False

## 3. Encryption Service (AES-256-GCM)

- [x] 3.1 (RED) Escribir test: `EncryptionService.encrypt("plaintext")` devuelve string != input
- [x] 3.2 (GREEN) Implementar `EncryptionService` en `app/core/security.py`
- [x] 3.3 (TRIANGULATE) Agregar casos: decrypt(encrypt("plaintext")) == "plaintext"; decrypt(tampered) → error de autenticación

## 4. Core SQLAlchemy Models

- [x] 4.1 Crear `app/models/__init__.py` con imports públicos
- [x] 4.2 (RED) Escribir tests para cada modelo: User, Tenant, Role, Permission, UserRole, UserTenant con sus constraints (unicidad, FKs, defaults)
- [x] 4.3 (GREEN) Implementar `User` model en `app/models/user.py` con UUID pk, email único, legajo único, indexed, `SoftDeleteMixin`
- [x] 4.4 (GREEN) Implementar `Tenant` model en `app/models/tenant.py` con UUID pk, name, code único, is_active
- [x] 4.5 (GREEN) Implementar `Role` model en `app/models/role.py` con UUID pk, name + tenant_id unique constraint
- [x] 4.6 (GREEN) Implementar `Permission` model en `app/models/permission.py` con UUID pk, name único en formato `modulo:accion`
- [x] 4.7 (GREEN) Implementar `UserRole` model en `app/models/user_role.py` como tabla de asociación user+tenant+role
- [x] 4.8 (GREEN) Implementar `UserTenant` model en `app/models/user_tenant.py` como tabla de asociación user+tenant

## 5. Base Repository + TenantScopedRepository

- [x] 5.1 (RED) Escribir test: `BaseRepository` tiene create(), get(), list(), update(), soft_delete() que interactúan con DB
- [x] 5.2 (GREEN) Implementar `BaseRepository[T]` en `app/repositories/base.py`
- [x] 5.3 (RED) Escribir test: `TenantScopedRepository` filtra automáticamente por tenant_id en todos los métodos
- [x] 5.4 (GREEN) Implementar `TenantScopedRepository[T]` en `app/repositories/base.py`
- [x] 5.5 (TRIANGULATE) Verificar: query sin tenant scope falla; cross-tenant isolation; `include_deleted()` opt-in funciona

## 6. Alembic Migration

- [x] 6.1 Crear migración Alembic `initial_models` con todas las tablas, FKs, índices y constraints únicos
- [x] 6.2 (RED) Escribir test: correr `alembic upgrade head` y verificar que las 6 tablas existen con columnas correctas
- [x] 6.3 (GREEN) Ajustar migración hasta que el test pase
- [x] 6.4 (TRIANGULATE) Verificar `alembic downgrade -1` drop de tablas; volver a upgrade

## 7. Verificación Final

- [x] 7.1 Ejecutar suite completa de tests (`pytest`) y confirmar verde (82 passed)
- [x] 7.2 Verificar que ningún archivo supera 500 LOC
