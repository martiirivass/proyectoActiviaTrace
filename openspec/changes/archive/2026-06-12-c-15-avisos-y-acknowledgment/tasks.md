## 1. Setup — Auditoría y Permisos

- [x] 1.1 Agregar códigos de auditoría `AVISO_CREAR`, `AVISO_EDITAR`, `AVISO_ELIMINAR`, `AVISO_ACK` en `backend/app/core/audit_codes.py`
- [x] 1.2 Agregar permiso `avisos:publicar` en `backend/app/core/permissions.py`
- [x] 1.3 Asignar permiso `avisos:publicar` a COORDINADOR y ADMIN en el seeder de RBAC (ya existe en migración seed)

## 2. Modelos SQLAlchemy

- [x] 2.1 Crear `backend/app/models/aviso.py` con modelo `Aviso`
- [x] 2.2 Crear modelo `AcknowledgmentAviso` en el mismo archivo
- [x] 2.3 Registrar modelos y enums en `backend/app/models/__init__.py`

## 3. Migración Alembic

- [x] 3.1 Migración manual creada (autogenerate no disponible por DB caída)
- [x] 3.2 Revisada y ajustada — enums, FKs, índices, unique constraint OK
- [x] 3.3 Ejecutar migración y verificar que las tablas se crean correctamente

## 4. Repositorios

- [x] 4.1-4.7 `AvisoRepository` + `AcknowledgmentRepository` completos con todos los métodos

## 5. Schemas Pydantic

- [x] 5.1-5.6 Todos los schemas creados y registrados

## 6. Services

- [x] 6.1-6.9 `AvisoService` completo con todas las operaciones y auditoría

## 7. Routers / API Endpoints

- [x] 7.1-7.9 Router completo con 8 endpoints, registrado en `main.py`

## 8. Tests

- [x] 8.1-8.18 Archivo de tests completo con 18 casos
- [x] ⚠️ Tests ejecutados correctamente: 18/18 passed (DB resuelta)
