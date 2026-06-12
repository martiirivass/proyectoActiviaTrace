## 1. Models

- [x] 1.1 Create `backend/app/models/tarea.py` with `Tarea` model (UUID PK, tenant_id, materia_id nullable, asignado_a FK, asignado_por FK, estado enum, descripcion text, contexto_id UUID nullable, SoftDeleteMixin, TimestampMixin)
- [x] 1.2 Create `backend/app/models/comentario_tarea.py` with `ComentarioTarea` model (UUID PK, tenant_id, tarea_id FK, autor_id FK, texto text, creado_at datetime, SoftDeleteMixin)
- [x] 1.3 Register both models in `backend/app/models/__init__.py`

## 2. Alembic Migration

- [x] 2.1 Generate migration for `tarea` and `comentario_tarea` tables
- [x] 2.2 Define enum type for `tarea.estado` (Pendiente, EnProgreso, Resuelta, Cancelada)
- [x] 2.3 Add foreign keys: tarea.asignado_a → usuario.id, tarea.asignado_por → usuario.id, tarea.materia_id → materia.id, comentario_tarea.tarea_id → tarea.id, comentario_tarea.autor_id → usuario.id
- [x] 2.4 Add tenant_id FK and indexes for all tenant_id columns
- [x] 2.5 Add soft delete columns (deleted_at) via SoftDeleteMixin

## 3. Schemas

- [x] 3.1 Create `backend/app/schemas/tareas.py` with `TareaCreate` (asignado_a, descripcion, materia_id opcional, contexto_id opcional; extra='forbid')
- [x] 3.2 Add `TareaUpdate` (estado opcional, asignado_a opcional, descripcion opcional)
- [x] 3.3 Add `TareaResponse` (all fields, including timestamps, with model_config = ConfigDict(from_attributes=True))
- [x] 3.4 Add `TareaListResponse` as a paginated wrapper
- [x] 3.5 Add `ComentarioCreate` (texto requerido; extra='forbid')
- [x] 3.6 Add `ComentarioResponse` (all fields, from_attributes=True)

## 4. Repositories

- [x] 4.1 Create `backend/app/repositories/tarea_repository.py` with methods: `create`, `get_by_id` (scoped by tenant), `list` (with filters: estado, asignado_a, asignado_por, materia_id, q for ILIKE on descripcion, limit, offset; always scoped by tenant + excludes soft-deleted), `update`, `soft_delete`
- [x] 4.2 Create `backend/app/repositories/comentario_repository.py` with methods: `create`, `list_by_tarea` (ordered by creado_at asc, scoped by tenant, excludes soft-deleted)
- [x] 4.3 Register both repositories in the DI container or provide factory functions

## 5. Service

- [x] 5.1 Create `backend/app/services/tarea_service.py` with:
  - `create_tarea`: validates permisos (tareas:admin), auto-sets asignado_por = current_user, estado = Pendiente
  - `get_tarea`: validates access (own task for gestionar, any for admin)
  - `list_tareas`: applies role-based filtering + optional query filters
  - `update_tarea`: validates state transitions (forward-only), role-based update scope, handles reassign
  - `delete_tarea`: validates tareas:admin, soft delete
  - `add_comentario`: validates access to tarea, creates comment with autor_id = current_user
  - `list_comentarios`: delegates to repository, validates access

## 6. Router

- [x] 6.1 Create `backend/app/api/v1/routers/tareas.py` with endpoints:
  - `GET /api/v1/tareas` — require_permission("tareas:gestionar"), returns paginated filtered list
  - `POST /api/v1/tareas` — require_permission("tareas:admin"), returns 201
  - `GET /api/v1/tareas/{id}` — require_permission("tareas:gestionar"), returns detail
  - `PUT /api/v1/tareas/{id}` — require_permission("tareas:gestionar"), updates estado/reassign
  - `DELETE /api/v1/tareas/{id}` — require_permission("tareas:admin"), returns 204
  - `POST /api/v1/tareas/{id}/comentarios` — require_permission("tareas:gestionar"), returns 201
  - `GET /api/v1/tareas/{id}/comentarios` — require_permission("tareas:gestionar"), returns list
- [x] 6.2 Register router in `backend/app/api/v1/__init__.py` or main app

## 7. Permissions Seed

- [x] 7.1 Add `tareas:gestionar` and `tareas:admin` to the permission catalog seed data
- [x] 7.2 Map `tareas:gestionar` → roles: PROFESOR, TUTOR, COORDINADOR, ADMIN
- [x] 7.3 Map `tareas:admin` → roles: COORDINADOR, ADMIN

## 8. Tests

- [x] 8.1 Write test: COORDINADOR crea tarea → 201, campos correctos
- [x] 8.2 Write test: PROFESOR sin tareas:admin intenta crear → 403
- [x] 8.3 Write test: Transición Pendiente→EnProgreso→Resuelta válida
- [x] 8.4 Write test: Transición inválida (retroceso) → 422
- [x] 8.5 Write test: PROFESOR no cambia estado de tarea ajena → 403
- [x] 8.6 Write test: COORDINADOR cancela tarea desde cualquier estado → 200
- [x] 8.7 Write test: PROFESOR lista solo sus tareas (no ve ajenas)
- [x] 8.8 Write test: COORDINADOR ve todas las tareas del tenant
- [x] 8.9 Write test: Filtros por estado, materia, búsqueda libre
- [x] 8.10 Write test: Paginación (limit, offset)
- [x] 8.11 Write test: Soft delete por ADMIN → 204, tarea no aparece en listado
- [x] 8.12 Write test: PROFESOR no puede borrar → 403
- [x] 8.13 Write test: Agregar comentario → 201, autor correcto
- [x] 8.14 Write test: Listar comentarios de tarea → ordenados por fecha
- [x] 8.15 Write test: Comentario sin texto → 422
- [x] 8.16 Write test: Aislamiento multi-tenant (tenant A no ve tareas de tenant B)
- [x] 8.17 Write test: Reasignación por COORDINADOR mantiene asignado_por original
