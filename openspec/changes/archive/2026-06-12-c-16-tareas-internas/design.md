## Context

Activia Trace ya dispone de los cimientos multi-tenant (C-01, C-02), autenticación JWT + RBAC con permisos finos `modulo:accion` (C-03, C-04), y los modelos base de Usuario y Asignación (C-07). El sistema actualmente no tiene un mecanismo formal de tareas internas entre coordinación y docentes. Este módulo agrega esa capacidad.

El dominio es **alto uso**: cientos de tareas simultáneas durante el período activo, con múltiples actores (COORDINADOR, PROFESOR, TUTOR, ADMIN). La arquitectura sigue Clean Architecture (Routers → Services → Repositories → Models) con inyección de dependencias, multi-tenancy row-level, soft delete, y Pydantic v2 con `extra='forbid'`.

## Goals / Non-Goals

**Goals:**
- Modelar `Tarea` y `ComentarioTarea` según entidades E12 de la KB
- Implementar CRUD completo con transiciones de estado forward-only (Pendiente → EnProgreso → Resuelta → Cancelada)
- Filtrar tareas por rol: PROFESOR/TUTOR solo ven las propias; COORDINADOR/ADMIN ven todas
- Soportar asignación con trazabilidad (asignado_por, asignado_a)
- Comentarios append-only sin edición ni borrado
- Permisos `tareas:gestionar` (gestión propia) y `tareas:admin` (administración global)
- Mínimo 80% cobertura de línea, 90% reglas de negocio
- Strict TDD: test que falla → código mínimo → triangulación → refactor

**Non-Goals:**
- Notificaciones push ni en tiempo real (se puede agregar después sobre el modelo existente)
- Archivos adjuntos a tareas o comentarios
- Workflow de aprobación multinivel (solo asignador → asignado)
- Histórico de cambios de estado (se infiere de comentarios + audit log existente)
- Frontend (se implementa en C-23)

## Decisions

### 1. Transiciones de estado validadas en Service, no en DB
- **Decisión**: La lógica de transiciones (Pendiente → EnProgreso → Resuelta → Cancelada, sin retroceso) se valida en `TareaService`, no con CHECK constraints ni triggers en DB.
- **Rationale**: Las reglas de transición dependen del rol del usuario (PROFESOR/TUTOR solo cambian estado de tareas asignadas a ellos; COORDINADOR/ADMIN pueden cambiar cualquier tarea). La lógica condicional es más expresiva en Python que en SQL. Además, las transiciones inválidas devuelven 422 con mensaje explícito, no un error de base de datos opaco.
- **Alternativa considerada**: CHECK constraint con enum nativo de PostgreSQL. Descartado porque no puede modelar "quién puede transicionar" sin lógica aplicación.

### 2. Contexto_id como UUID opaco sin FK
- **Decisión**: `contexto_id` en Tarea es un UUID nullable sin foreign key. Sirve como referencia opcional a cualquier entidad del dominio (Materia, Asignacion, Comunicacion, etc.).
- **Rationale**: El contexto puede apuntar a distintas entidades según el tipo de tarea. Forzar una FK única limitaría la flexibilidad. El significado del contexto se infiere del contexto de negocio (ej: si `materia_id` está presente y `contexto_id` también, podría ser una asignación específica dentro de esa materia).
- **Alternativa considerada**: Polimorfismo con `contexto_tipo` (text) + `contexto_id` (UUID). Descartado por complejidad adicional sin caso de uso concreto que lo justifique. Se agrega cuando se necesite.

### 3. Repositorio separado para ComentarioTarea
- **Decisión**: `ComentarioTareaRepository` es independiente de `TareaRepository`, no un método dentro de este.
- **Rationale**: Cada repositorio debe tener una responsabilidad única y ≤500 LOC. Aunque hoy los comentarios solo existen vinculados a una tarea, la lógica de consulta (listar por tarea, contar, paginar) y la semántica append-only justifican un repositorio separado.
- **Alternativa considerada**: `TareaRepository` con métodos `add_comment` y `get_comments`. Descartado por violar el límite de LOC a futuro y mezclar responsabilidades.

### 4. Permisos separados: `tareas:gestionar` vs `tareas:admin`
- **Decisión**: Dos permisos en el catálogo RBAC. `tareas:gestionar` para PROFESOR/TUTOR (ver y actualizar estado de tareas propias). `tareas:admin` para COORDINADOR/ADMIN (crear, reasignar, borrar, ver todas).
- **Rationale**: Mapea exactamente a la matriz de permisos definida en `03_actores_y_roles.md` §3.3. Permite futuro refinamiento (ej: un rol que solo vea但不能 borre).
- **Alternativa considerada**: Un único permiso `tareas:full` con chequeo de "propiedad" en Service. Descartado porque mezcla dos niveles de autorización distintos.

### 5. Soft delete via mixin existente
- **Decisión**: Tarea y ComentarioTarea usan `SoftDeleteMixin` (timestamps y lógica existente del core). No se reabren migraciones.
- **Rationale**: Consistent con el resto del modelo. El soft delete de ComentarioTarea solo aplica a COORDINADOR/ADMIN (aunque la funcionalidad no se expone en esta versión, el modelo lo soporta).

### 6. Listado con filtros en query params
- **Decisión**: `GET /api/v1/tareas` acepta query params: `estado`, `asignado_a`, `asignado_por`, `materia_id`, `q` (búsqueda libre en descripción). Paginación con `limit` y `offset`.
- **Rationale**: Sigue el patrón de filtros del proyecto (ej: monitor general, comunicaciones). Los filtros se aplican en el Repository, no en Service.
- **Alternativa considerada**: Búsqueda全文 con Postgres TSVECTOR. Descartado por ahora; `q` usa `ILIKE` sobre `descripcion` que es suficiente para cientos de registros.

## Risks / Trade-offs

- **[Performance] Búsqueda ILIKE en descripción**: Si el volumen crece a miles de tareas, el ILIKE sin índice puede ser lento. → Mitigación: migración futura agrega índice GIN con `pg_trgm` si es necesario.
- **[Security] Profesor podría intentar ver tareas de otros alterando query params**: El Service filtra por `asignado_a = current_user.id` para roles sin `tareas:admin`. Nunca se confía en los params del cliente. → Mitigación: tests específicos que verifican que PROFESOR no ve tareas ajenas aunque manipule la URL.
- **[Data integrity] Sin FK en contexto_id**: Podría quedar un UUID huérfano. → Mitigación: es una referencia semántica (no relacional), aceptable para este caso de uso. Se documenta en el modelo.
- **[Convention] ≤500 LOC**: TareaService podría acercarse al límite con toda la lógica de transiciones + filtros. → Mitigación: si excede, se extrae lógica de validación de estados a un `tarea_machine.py` separado.
