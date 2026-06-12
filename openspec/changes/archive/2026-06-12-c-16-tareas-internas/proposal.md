## Why

El equipo docente y de coordinación necesita un canal formal de seguimiento de tareas internas dentro de la plataforma. Hoy no existe trazabilidad entre coordinación y docentes: las solicitudes, delegaciones y reportes se manejan por canales externos (WhatsApp, email, verbal), sin registro, sin estados, sin accountability. Este módulo resuelve eso: tareas asignables con estado, comentarios en hilo, contexto académico (materia) y visibilidad granular por rol.

Es un módulo de **alto uso**: cientos de tareas simultáneas durante el período activo. Sin esto, la plataforma no puede reemplazar las herramientas externas que los equipos usan hoy.

## What Changes

- Nuevos modelos de dominio: `Tarea` (E12) y `ComentarioTarea` (E12)
- Nuevos schemas Pydantic v2 con `extra='forbid'` para request/response de tareas y comentarios
- Nuevos repositories con tenant scope: `TareaRepository`, `ComentarioRepository`
- Nuevo service: `TareaService` con lógica de transiciones de estado, creación con trazabilidad, filtros por rol
- Nuevo router REST: `GET/POST /api/v1/tareas`, `GET/PUT/DELETE /api/v1/tareas/{id}`, `POST/GET /api/v1/tareas/{id}/comentarios`
- Nuevos permisos RBAC: `tareas:gestionar` (PROFESOR, TUTOR, COORDINADOR, ADMIN) y `tareas:admin` (COORDINADOR, ADMIN)
- Migración Alembic para tablas `tarea` y `comentario_tarea`
- Tests completos (strict TDD): creación, transiciones de estado, filtros por rol, comentarios en hilo, soft delete, aislamiento multi-tenant, permisos

## Capabilities

### New Capabilities
- `tareas-workflow`: Creación, asignación, delegación y transición de estados (Pendiente → EnProgreso → Resuelta → Cancelada) de tareas internas entre roles del equipo docente. Incluye trazabilidad asignador/asignado, contexto opcional de materia, y soft delete.
- `tareas-comentarios`: Comentarios append-only en hilo por tarea. Solo creación y lectura (sin edición ni borrado). Autor y timestamp registrados automáticamente.
- `tareas-visibilidad-rol`: Filtrado de tareas según el rol del usuario: PROFESOR/TUTOR ven solo sus tareas asignadas; COORDINADOR/ADMIN ven todas las tareas del tenant con filtros (docente, asignador, materia, estado, búsqueda libre).
- `tareas-permisos`: Permisos `tareas:gestionar` para manage propio + `tareas:admin` para administración global, reasignación y borrado.

### Modified Capabilities
<!-- No existing capabilities are being modified -->

## Impact

- **Models**: `backend/app/models/tarea.py`, `backend/app/models/comentario_tarea.py` (nuevos)
- **Schemas**: `backend/app/schemas/tareas.py` (nuevo)
- **Repositories**: `backend/app/repositories/tarea_repository.py`, `backend/app/repositories/comentario_repository.py` (nuevos)
- **Services**: `backend/app/services/tarea_service.py` (nuevo)
- **Routers**: `backend/app/api/v1/routers/tareas.py` (nuevo)
- **Permissions**: Se agregan `tareas:gestionar` y `tareas:admin` al catálogo de permisos existente (seed en C-04)
- **DB Migration**: Nueva migración Alembic para tablas `tarea` y `comentario_tarea`
- **Tests**: `backend/tests/test_tareas.py` (nuevo)
