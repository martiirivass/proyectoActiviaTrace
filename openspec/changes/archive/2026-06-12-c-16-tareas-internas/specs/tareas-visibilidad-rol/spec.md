## ADDED Requirements

### Requirement: Listar tareas con filtros por rol
El sistema SHALL exponer GET /api/v1/tareas que lista tareas según el rol del usuario:
- **PROFESOR/TUTOR** (`tareas:gestionar`): ven solo tareas donde `asignado_a` = usuario autenticado.
- **COORDINADOR/ADMIN** (`tareas:admin`): ven todas las tareas del tenant.

Los listados SHALL excluir tareas soft-deleteadas.

#### Scenario: PROFESOR lista solo sus tareas
- **WHEN** un PROFESOR hace GET /api/v1/tareas
- **THEN** el sistema retorna 200 con un array que solo contiene tareas donde `asignado_a` = ID del PROFESOR

#### Scenario: COORDINADOR lista todas las tareas
- **WHEN** un COORDINADOR hace GET /api/v1/tareas
- **THEN** el sistema retorna 200 con todas las tareas del tenant (no soft-deleteadas)

#### Scenario: Tareas soft-deleteadas no aparecen
- **WHEN** un COORDINADOR lista tareas y existe una tarea con `deleted_at` seteado
- **THEN** esa tarea no aparece en el listado

### Requirement: Filtros en listado de tareas
El sistema SHALL soportar los siguientes filtros via query params en GET /api/v1/tareas:
- `estado`: filtrar por estado (Pendiente, EnProgreso, Resuelta, Cancelada)
- `asignado_a`: UUID del usuario asignado
- `asignado_por`: UUID del usuario que asignó
- `materia_id`: UUID de materia
- `q`: búsqueda libre en `descripcion` (ILIKE)
- `limit`: máximo de resultados (defecto 50)
- `offset`: desplazamiento para paginación (defecto 0)

Los filtros SHALL ser aplicables solo para usuarios con `tareas:admin`. Para `tareas:gestionar`, el filtro `asignado_a` es ignorado (siempre es el usuario autenticado).

#### Scenario: Filtrar por estado
- **WHEN** un COORDINADOR hace GET /api/v1/tareas?estado=Pendiente
- **THEN** el sistema retorna solo tareas en estado Pendiente

#### Scenario: Filtrar por materia
- **WHEN** un COORDINADOR hace GET /api/v1/tareas?materia_id={uuid}
- **THEN** el sistema retorna solo tareas de esa materia (incluyendo materia_id = null si no se filtra)

#### Scenario: Búsqueda libre en descripción
- **WHEN** un COORDINADOR hace GET /api/v1/tareas?q=programación
- **THEN** el sistema retorna tareas cuya descripción contiene "programación" (case-insensitive)

#### Scenario: Paginación con limit y offset
- **WHEN** un COORDINADOR hace GET /api/v1/tareas?limit=10&offset=20
- **THEN** el sistema retorna hasta 10 resultados, saltando los primeros 20

#### Scenario: PROFESOR no puede filtrar por asignado_a
- **WHEN** un PROFESOR hace GET /api/v1/tareas?asignado_a={otro_uuid}
- **THEN** el sistema ignora el filtro y retorna solo tareas del PROFESOR autenticado
