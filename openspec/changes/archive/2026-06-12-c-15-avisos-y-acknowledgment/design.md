## Context

El módulo de **Avisos y Acknowledgment** cubre la Épica 3 (F3.5) del producto. Los COORDINADORES y ADMIN necesitan publicar comunicaciones institucionales segmentadas por audiencia. Todos los roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) necesitan un tablón central donde consultar avisos activos. Los avisos críticos requieren confirmación de lectura obligatoria.

Actualmente el backend tiene una arquitectura consolidada:
- FastAPI con routers → services → repositories (TenantScopedRepository)
- SQLAlchemy 2.0 async con modelos que heredan de `SoftDeleteMixin` y usan UUID PK
- Pydantic v2 schemas con `ConfigDict(extra='forbid')`
- Permisos finos via `require_permission(codename)`
- Auditoría via `AuditService.log(...)` con códigos en `audit_codes.py`
- Tests con base de datos real (sin mocks de DB)

Este change sigue el patrón establecido. Governance level: MEDIO — implementación con checkpoints.

**Dependencia**: C-06 (estructura académica) — las tablas `Materia` y `Cohorte` existen y son referenciables.

## Goals / Non-Goals

**Goals:**
- Modelar `Aviso` con alcance (Global|PorMateria|PorCohorte|PorRol), severidad (Info|Advertencia|Crítico), ventana de vigencia, orden de prioridad y flag requiere_ack
- Modelar `AcknowledgmentAviso` como tabla de confirmaciones de lectura
- Implementar CRUD completo de avisos protegido con permiso `avisos:publicar`
- Implementar listado de avisos activos filtrado automáticamente por tenant, rol, alcance, contexto académico (materias/cohortes del usuario) y ventana de vigencia
- Implementar confirmación de lectura (ack) con idempotencia (segundo ack es no-op)
- Implementar estadísticas de confirmación por aviso para COORDINADOR/ADMIN
- Contadores derivados de la tabla `AcknowledgmentAviso` (no desnormalizados)
- Soft delete en todos los modelos
- Auditoría de todas las operaciones del módulo
- Proteger el módulo con permisos `avisos:publicar` y `avisos:ver`

**Non-Goals:**
- Notificaciones push o emails al publicar un aviso (la visibilidad es pull-based: el usuario ve los avisos al consultar el tablón)
- Programación de publicación diferida (el aviso se crea con `inicio_en`/`fin_en` ya definidos; la visibilidad se resuelve al consultar)
- Frontend de este módulo (se implementa en C-23 frontend-coordinacion)
- Eliminación física de datos (soft delete solamente)
- Edición de avisos ya visibles (se puede desactivar o editar, pero no se elimina el registro de ack existente)
- Categorización más allá de severidad y alcance (tags, etiquetas personalizadas)

## Decisions

### D1: Filtrado de audiencia en el repository query (no post-filter en service)
- **Opción A (elegida)**: El repository `aviso_repository.py` recibe `usuario_id`, `rol`, `cohorte_ids`, `materia_ids` y construye un único query SQL con los filtros de alcance, vigencia, rol destino y contexto académico. El `AvisoService` resuelve los datos del usuario (roles, asignaciones) y los pasa al repository.
- **Opción B**: El repository devuelve todos los avisos activos del tenant y el service filtra en memoria.
- **Razón**: Para un tenant con muchos avisos y usuarios, el post-filter en memoria es ineficiente. El query con filtros en SQL es óptimo porque PostgreSQL puede usar índices compuestos en `tenant_id + activo + inicio_en + fin_en`. La lógica de filtrado es puramente data-oriented y no requiere reglas de dominio complejas post-query.

### D2: Vista de avisos unifica avisos globales + contextuales en un solo endpoint
- **Opción A (elegida)**: `GET /api/v1/avisos` devuelve la lista de avisos activos para el usuario actual, combinando en un solo response: avisos globales + avisos por materia (si el usuario tiene asignaciones en esa materia) + avisos por cohorte (si el usuario pertenece a esa cohorte) + avisos por rol (si coincide el rol del usuario). Ordenados por `orden ASC, inicio_en DESC`.
- **Opción B**: Endpoints separados para cada tipo de alcance.
- **Razón**: La experiencia de usuario es un tablón unificado. Separar por alcance obligaría al frontend a hacer N requests y mergear resultados. Un solo endpoint simplifica el consumo y permite paginación consistente.

### D3: Acknowledgment idempotente con upsert
- **Opción A (elegida)**: `POST /api/v1/avisos/{id}/ack` hace un INSERT ... ON CONFLICT (aviso_id, usuario_id) DO NOTHING. Si ya existe un ack, la operación es un no-op (HTTP 200 igual, idempotente). El service no valida pre-existencia — lo delega a la constraint UNIQUE.
- **Opción B**: Validación en service: si ya existe ack, devolver 409 Conflict.
- **Razón**: La idempotencia es más amigable para el frontend y evita race conditions. Un usuario puede hacer clic múltiples veces sin error. El `INSERT ... ON CONFLICT DO NOTHING` es atómico y eficiente.

### D4: Sin tabla de "vistas" separada — el ack es la única interacción tracking
- **Opción A (elegida)**: `AcknowledgmentAviso` solo registra confirmaciones explícitas. No hay registro de "vista" pasiva (cuando el usuario solo ve el aviso sin confirmar). Las estadísticas expuestas son: total de usuarios alcanzados (derivado de la audiencia calculada) vs total de acknowledges (count de la tabla).
- **Opción B**: Tabla separada `VistaAviso` que registra cada vez que un usuario ve un aviso, además del ack.
- **Razón**: Para el MVP, registrar "vistas" pasivas agrega complejidad y storage sin valor claro de negocio. El indicador útil es cuántos confirmaron vs cuántos deberían confirmar. Si en el futuro se necesita tracking de vistas, se puede agregar como una tabla separada sin cambiar la estructura de ack. Ver RN-19.

### D5: Endpoints planos bajo un solo router `/api/v1/avisos`
- **Opción A (elegida)**: Un solo router `avisos.py` con prefijo `/api/v1/avisos`. Los endpoints de ack y stats usan sub-rutas: `POST /api/v1/avisos/{id}/ack`, `GET /api/v1/avisos/{id}/stats`.
- **Opción B**: Routers separados para avisos, ack y stats.
- **Razón**: Un solo router mantiene cohesión del módulo. Es el patrón usado en C-14 (evaluaciones), C-13 (encuentros) y otros módulos existentes.

### D6: Permisos `avisos:publicar` y `avisos:ver` con asignación por rol
- **Opción A (elegida)**: Dos permisos diferenciados. `avisos:publicar` cubre CRUD completo de avisos + stats (COORDINADOR, ADMIN). `avisos:ver` cubre visualización de tablón + ack (todos los roles).
- **Opción B**: Un solo permiso para todo.
- **Razón**: Todo usuario debe poder ver avisos y confirmar lectura, pero solo COORDINADOR/ADMIN deben poder crearlos/editarlos/eliminarlos. Consistente con el modelo RBAC fino del sistema y con la matriz del KB (§3.3: "Publicar avisos" solo COORDINADOR/ADMIN; "Confirmar avisos" todos los roles).

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|-----------|
| [R1] Query de avisos activos puede ser lento si hay muchos avisos y usuarios con muchas asignaciones | Índice compuesto en `(tenant_id, activo, inicio_en, fin_en)`. El repository usa `EXISTS` para subqueries de alcance por materia/cohorte, no JOINs que multipliquen filas. Paginación obligatoria (default 20, max 100). |
| [R2] El cálculo de "usuarios alcanzados" para stats es una estimación (depende de asignaciones vigentes al momento de la consulta) | Documentar que el contador es "alcanzados potenciales" basado en asignaciones activas al momento de la consulta, no un histórico. Es aceptable para el caso de uso (gestión). |
| [R3] Avisos con `requiere_ack=true` y alcance muy amplio (Global, todos los roles) pueden generar millones de rows en AcknowledgmentAviso | PostgreSQL maneja millones de rows sin problema con índices en `(aviso_id, usuario_id)`. La tabla es append-only y liviana (3 columnas + UUID PK). Si el volumen es crítico, se puede particionar por aviso_id en el futuro. |
| [R4] Sin edición de avisos ya visibles, si un coordinador publica un error debe desactivar y crear uno nuevo | Aceptado como trade-off. La alternativa (permitir editar avisos con ack existentes) rompe la integridad del registro de confirmaciones. Un aviso corregido debe ser nuevo. |
