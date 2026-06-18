## 1. Modelo y migración

- [x] 1.1 Crear `AuditLog` model con todos los campos de E-AUD: `id`, `tenant_id`, `fecha_hora`, `actor_id`, `impersonado_id` (nullable), `materia_id` (nullable), `accion`, `detalle` (JSON), `filas_afectadas`, `ip`, `user_agent` — más `created_at`, `updated_at`
- [x] 1.2 Crear migration 004 con tabla `audit_log`, índices por `(tenant_id, fecha_hora)` y FK a `users(actor_id)` y opcional `users(impersonado_id)`
- [x] 1.3 Registrar modelo en `backend/app/models/__init__.py`

## 2. Códigos de acción

- [x] 2.1 Crear `backend/app/core/audit_codes.py` con constantes tipadas: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`

## 3. Repositorio

- [x] 3.1 Crear `AuditLogRepository` con métodos:
  - `create(db, obj_in)` — inserta el registro
  - `find(db, *, tenant_id, accion=None, actor_id=None, desde=None, hasta=None, offset=0, limit=50)` — consulta paginada con filtros, ordenado por fecha descendente
  - Sin `update()` ni `delete()` — repositorio standalone sin herencia de BaseRepository

## 4. Servicio

- [x] 4.1 Crear `AuditService` con:
  - `log(db, *, tenant_id, actor_id, accion, detalle=None, impersonado_id=None, materia_id=None, filas_afectadas=0, ip=None, user_agent=None)` — crea el registro
  - `get_log(db, *, tenant_id, accion=None, actor_id=None, desde=None, hasta=None, offset=0, limit=50)` — delega al repositorio

## 5. Endpoint REST

- [x] 5.1 Crear `backend/app/api/v1/routers/audit.py` con:
  - `GET /api/v1/audit/log` — listar registros con filtros por query params
  - Requiere permiso `auditoria:ver`
  - Paginación: `offset`, `limit` (default 50, max 200)
  - Filtros: `accion`, `actor_id`, `desde`, `hasta` (fechas ISO)
  - Scoped por tenant automáticamente
- [x] 5.2 Registrar router en `backend/app/main.py`

## 6. AuditDependency (middleware opt-in)

- [x] 6.1 Crear `backend/app/core/audit_dependency.py` con:
  - `AuditDependency` clase/inyectable FastAPI que recibe `action_code`, opcionalmente extrae `ip` y `user_agent` del request, y llama a `AuditService.log()` después de ejecutar el endpoint
  - Debe funcionar como dependency en endpoints individuales

## 7. Tests

- [x] 7.1 Test: modelo crea registro correctamente
- [x] 7.2 Test: registro con impersonación (`impersonado_id` seteado)
- [x] 7.3 Test: repositorio rechaza update (método no disponible)
- [x] 7.4 Test: repositorio rechaza delete (método no disponible)
- [x] 7.5 Test: consulta paginada sin filtros
- [x] 7.6 Test: filtrar por `accion`
- [x] 7.7 Test: filtrar por `actor_id`
- [x] 7.8 Test: filtrar por rango de fechas
- [x] 7.9 Test: multi-tenant aislamiento (usuario T1 no ve registros T2)
- [x] 7.10 Test: endpoint GET 200 con datos
- [x] 7.11 Test: endpoint GET 403 sin permiso `auditoria:ver`
- [x] 7.12 Test: endpoint GET paginación respeta límites
- [x] 7.13 Test: `AuditDependency` registra automáticamente en endpoint marcado
- [x] 7.14 Test: `AuditDependency` registra `ip` y `user_agent` correctamente
- [x] 7.15 Test: códigos de acción existen como constantes
