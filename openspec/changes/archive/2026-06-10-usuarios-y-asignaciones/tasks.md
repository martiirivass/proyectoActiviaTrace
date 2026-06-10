## 1. EncryptedString TypeDecorator

## 1. EncryptedString TypeDecorator

- [x] 1.1 Crear `backend/app/core/encrypted_types.py` con `EncryptedString` TypeDecorator que usa `EncryptionService` para encriptar/desencriptar automáticamente en SQLAlchemy

## 2. Modelos

- [x] 2.1 Extender modelo `User`: agregar campos `tenant_id` (FK, UUID), `dni` (EncryptedString), `cuil` (EncryptedString), `cbu` (EncryptedString), `alias_cbu` (EncryptedString), `banco` (String), `regional` (String), `legajo_profesional` (String), `facturador` (Boolean, default False), `estado` (String, default "Activo")
- [x] 2.2 Ajustar modelo `User`: `legajo` nullable (atributo de negocio, no obligatorio), `email` unique compuesto `(tenant_id, email)` en vez de global
- [x] 2.3 Crear modelo `Asignacion` (id, tenant_id, usuario_id FK, rol String, materia_id FK nullable, carrera_id FK nullable, cohorte_id FK nullable, dictado_id FK nullable, comisiones JSON nullable, responsable_id FK nullable, desde Date, hasta Date nullable — hereda SoftDeleteMixin)
- [x] 2.4 Registrar `Asignacion` en `backend/app/models/__init__.py`

## 3. Migración

- [x] 3.1 Crear migration 006: ALTER TABLE users ADD COLUMNS + CREATE TABLE asignaciones + index `ix_users_email_tenant` (permisos ya existían de C-04)

## 4. Repositorios

- [x] 4.1 Crear `UsuarioRepository` (scoped, métodos: create, find_by_email scoped tenant, list, get, update, soft_delete)
- [x] 4.2 Crear `AsignacionRepository` (scoped, métodos: create, list con filtros por usuario/materia/rol, get, update, soft_delete)

## 5. Schemas

- [x] 5.1 Crear `backend/app/schemas/usuarios.py`: `UserCreate`, `UserUpdate`, `UserResponse` (sin password_hash, sin totp_secret), `UserList`
- [x] 5.2 Crear `backend/app/schemas/asignaciones.py`: `AsignacionCreate`, `AsignacionUpdate`, `AsignacionResponse` (con estado_vigencia derivado), `AsignacionList`

## 6. Servicios

- [x] 6.1 Crear `UsuarioService`: CRUD + hasheo de password con Argon2id + validación email único por tenant
- [x] 6.2 Crear `AsignacionService`: CRUD + helper `is_vigente()` + validación de roles + filtros

## 7. Routers

- [x] 7.1 Crear router `/api/v1/admin/usuarios` con ABM + permiso `usuarios:gestionar`
- [x] 7.2 Crear router `/api/v1/admin/asignaciones` con ABM + permiso `equipos:asignar`
- [x] 7.3 Registrar routers en `backend/app/main.py`

## 8. Tests

- [x] 8.1 Test: crear usuario con todos los campos PII
- [x] 8.2 Test: PII cifrada en DB (consultar directo la tabla, verificar que dni/cuil/cbu/alias_cbu están cifrados)
- [x] 8.3 Test: PII desencriptada en respuesta API
- [x] 8.4 Test: email duplicado en mismo tenant → 409
- [x] 8.5 Test: mismo email en tenants distintos → OK
- [x] 8.6 Test: soft delete usuario → no aparece en list/get
- [x] 8.7 Test: crear asignación con todos los campos
- [x] 8.8 Test: crear asignación sin contexto (solo usuario+rol)
- [x] 8.9 Test: estado_vigencia derivado correctamente (vigente, vencida)
- [x] 8.10 Test: filtrar asignaciones por usuario/materia/rol
- [x] 8.11 Test: jerarquía responsable se registra correctamente
- [x] 8.12 Test: soft delete asignación → no aparece en list
- [x] 8.13 Test: 403 sin permiso `usuarios:gestionar`
- [x] 8.14 Test: 403 sin permiso `equipos:asignar`
- [x] 8.15 Test: usuario response NO expone password_hash
