## ADDED Requirements

### Requirement: Registrar guardia (F6.6)
El sistema SHALL permitir a TUTORES y DOCENTES registrar una guardia.
Los datos REQUERIDOS son: `asignacion_id`, `materia_id`, `carrera_id`, `cohorte_id`, `dia`, `horario`.
Los datos OPCIONALES son: `comentarios`.
El estado inicial de una guardia SHALL ser `Pendiente`.
Solo usuarios con permiso `encuentros:gestionar` pueden registrar guardias.
Un TUTOR SOLO puede registrar guardias para su propia asignación (verificado contra `asignacion_id`).

#### Scenario: TUTOR registra guardia exitosamente
- **WHEN** un TUTOR envía POST `/api/v1/guardias` con `asignacion_id` propio, `materia_id=UUID`, `carrera_id=UUID`, `cohorte_id=UUID`, `dia="Martes"`, `horario="14:00–14:45"`
- **THEN** el sistema crea la guardia con estado "Pendiente"
- **AND** audita la operación como `GUARDIA_REGISTRAR`
- **AND** la respuesta 201 incluye `id` y `estado`

#### Scenario: TUTOR no puede registrar guardia para otra asignación
- **WHEN** un TUTOR envía POST `/api/v1/guardias` con `asignacion_id` que NO le pertenece
- **THEN** el sistema responde 403 Forbidden

### Requirement: Actualizar estado de guardia
El sistema SHALL permitir cambiar el estado de una guardia a `Realizada` o `Cancelada`.
Solo el TUTOR que creó la guardia o un COORDINADOR pueden modificar el estado.

#### Scenario: Marcar guardia como realizada
- **WHEN** un TUTOR envía PATCH `/api/v1/guardias/{id}` con `estado="Realizada"`
- **THEN** el sistema actualiza la guardia a estado "Realizada"

#### Scenario: Cancelar guardia
- **WHEN** un COORDINADOR envía PATCH `/api/v1/guardias/{id}` con `estado="Cancelada"`
- **THEN** el sistema actualiza la guardia a estado "Cancelada"

### Requirement: Consulta global de guardias (COORDINADOR/ADMIN)
El sistema SHALL exponer un endpoint para consultar todas las guardias del tenant.
El endpoint SHALL ser `GET /api/v1/guardias` con filtros opcionales: `materia_id`, `carrera_id`, `cohorte_id`, `dia`, `estado`, `fecha_desde`, `fecha_hasta` (por `creada_at`).
La respuesta SHALL ser paginada con `offset` y `limit`.

#### Scenario: COORDINADOR consulta guardias filtradas por materia
- **WHEN** un COORDINADOR envía GET `/api/v1/guardias?materia_id=UUID&estado=Pendiente`
- **THEN** el sistema devuelve las guardias Pendientes de esa materia

### Requirement: Exportar guardias
El sistema SHALL permitir exportar el listado de guardias del tenant a formato CSV.
El endpoint SHALL ser `GET /api/v1/guardias/exportar`.
Los mismos filtros de consulta global aplican al export.
El CSV SHALL incluir columnas: Materia, Carrera, Cohorte, Día, Horario, Tutor, Estado, Comentarios, Creada.
La respuesta SHALL tener `Content-Type: text/csv`.

#### Scenario: COORDINADOR exporta guardias a CSV
- **WHEN** un COORDINADOR envía GET `/api/v1/guardias/exportar?carrera_id=UUID`
- **THEN** el sistema devuelve un archivo CSV descargable con las guardias filtradas
- **AND** el Content-Type es text/csv
