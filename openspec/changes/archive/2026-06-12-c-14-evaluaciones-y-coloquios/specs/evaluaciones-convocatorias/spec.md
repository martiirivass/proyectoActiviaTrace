## ADDED Requirements

### Requirement: Importar alumnos a convocatoria de coloquio (F7.2)
El sistema SHALL exponer un endpoint para que COORDINADOR y ADMIN (con permiso `coloquios:gestionar`) importen el padrón de alumnos habilitados para una convocatoria específica de coloquio.
El endpoint SHALL ser `POST /api/v1/evaluaciones/{id}/convocados` que recibe una lista de UUIDs de alumnos (`list[uuid.UUID]`).
La operación SHALL ser reemplazo atómico: elimina todas las relaciones existentes e inserta las nuevas en una sola transacción.
Los alumnos SHALL ser usuarios existentes con rol ALUMNO en el tenant. Si algún UUID no corresponde a un alumno válido, SHALL responder 422 con detalle.

#### Scenario: Importar padrón exitosamente
- **WHEN** un COORDINADOR envía POST `/api/v1/evaluaciones/{id}/convocados` con `["uuid1", "uuid2", "uuid3"]`
- **THEN** el sistema reemplaza el padrón de la convocatoria con esos 3 alumnos
- **AND** responde 200 con la cantidad de alumnos convocados

#### Scenario: Importar con alumno inexistente
- **WHEN** un ADMIN envía POST `/api/v1/evaluaciones/{id}/convocados` con `["uuid_valido", "uuid_inexistente"]`
- **THEN** el sistema responde 422 indicando qué UUIDs no son válidos

#### Scenario: Ver lista de convocados
- **WHEN** un COORDINADOR envía GET `/api/v1/evaluaciones/{id}/convocados`
- **THEN** el sistema responde con la lista de alumnos habilitados para esa convocatoria

### Requirement: Crear convocatoria de coloquio (F7.3)
El sistema SHALL exponer `POST /api/v1/evaluaciones` para que COORDINADOR y ADMIN creen una convocatoria de coloquio.
El body SHALL incluir: `materia_id`, `cohorte_id`, `tipo: "Coloquio"`, `instancia` (texto libre), y `dias: list[{fecha: date, cupo_maximo: int}]`.
El servicio SHALL crear la Evaluacion y los N registros DiaConvocatoria en una sola transacción.
El campo `tipo` SHALL estar restringido a `"Coloquio"` para este módulo (el modelo soporta otros tipos pero no se exponen).

#### Scenario: Crear convocatoria con 3 días de cupo
- **WHEN** un COORDINADOR envía POST `/api/v1/evaluaciones` con materia_id, cohorte_id, instancia="Coloquio Final" y 3 días con cupo_maximo=10 cada uno
- **THEN** el sistema crea la convocatoria
- **AND** responde 201 con los datos de la convocatoria y los días creados

#### Scenario: Crear convocatoria sin días lista 422
- **WHEN** un ADMIN envía POST `/api/v1/evaluaciones` con `dias: []`
- **THEN** el sistema responde 422

### Requirement: Editar convocatoria (F7.5)
El sistema SHALL exponer `PATCH /api/v1/evaluaciones/{id}` para editar campos editables de una convocatoria: `instancia`.
Los días de convocatoria NO se editan por este endpoint (se gestionan por separado si es necesario).
Si la convocatoria tiene reservas activas, SHALL rechazar la edición con 409.

#### Scenario: Editar instancia de convocatoria
- **WHEN** un ADMIN envía PATCH `/api/v1/evaluaciones/{id}` con `{"instancia": "Coloquio Final 2026"}`
- **THEN** el sistema actualiza y responde 200

#### Scenario: Editar convocatoria con reservas activas
- **WHEN** un COORDINADOR intenta editar una convocatoria que tiene reservas Activas
- **THEN** el sistema responde 409 Conflict

### Requirement: Cerrar convocatoria (F7.5)
El sistema SHALL exponer `POST /api/v1/evaluaciones/{id}/cerrar` para cerrar una convocatoria.
Al cerrar, las reservas Activas pasan a estado Cancelada y no se permiten nuevas reservas.
Solo ADMIN puede cerrar convocatorias.

#### Scenario: Cerrar convocatoria exitosamente
- **WHEN** un ADMIN envía POST `/api/v1/evaluaciones/{id}/cerrar`
- **THEN** el sistema cierra la convocatoria
- **AND** todas las reservas Activas pasan a Cancelada
- **AND** responde 200

### Requirement: Listado de convocatorias (F7.4)
El sistema SHALL exponer `GET /api/v1/evaluaciones` con paginación (`offset`, `limit`).
Cada item SHALL incluir métricas: `total_convocados`, `reservas_activas`, `cupos_libres` (suma de cupos disponibles en todos los días).
Filtros opcionales: `materia_id`, `cohorte_id`, `activa` (boolean).

#### Scenario: Listar convocatorias activas
- **WHEN** un COORDINADOR envía GET `/api/v1/evaluaciones?activa=true`
- **THEN** el sistema devuelve las convocatorias activas paginadas con métricas

#### Scenario: Listar convocatorias con filtro de materia
- **WHEN** un ADMIN envía GET `/api/v1/evaluaciones?materia_id=UUID`
- **THEN** el sistema devuelve solo las convocatorias de esa materia

### Requirement: Obtener detalle de convocatoria
El sistema SHALL exponer `GET /api/v1/evaluaciones/{id}` con detalle completo incluyendo días, métricas y lista de convocados.

#### Scenario: Ver detalle de convocatoria
- **WHEN** un COORDINADOR envía GET `/api/v1/evaluaciones/{id}`
- **THEN** el sistema responde con todos los datos de la convocatoria, sus días, métricas y convocados
