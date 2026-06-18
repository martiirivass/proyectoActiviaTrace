## ADDED Requirements

### Requirement: Filtrar asignaciones por dictado
El sistema SHALL permitir filtrar asignaciones por `dictado_id`.

#### Scenario: Filtrar por dictado_id
- **WHEN** se consulta GET `/api/v1/equipos/asignaciones?dictado_id=<uuid>`
- **THEN** retorna solo asignaciones de ese dictado

### Requirement: Filtrar asignaciones por carrera y cohorte
El sistema SHALL permitir filtrar asignaciones por carrera y cohorte a través del dictado.

#### Scenario: Filtrar por carrera
- **WHEN** se consulta GET `/api/v1/equipos/asignaciones?carrera_id=<uuid>`
- **THEN** retorna solo asignaciones de dictados de esa carrera

#### Scenario: Filtrar por cohorte
- **WHEN** se consulta GET `/api/v1/equipos/asignaciones?cohorte_id=<uuid>`
- **THEN** retorna solo asignaciones de dictados de esa cohorte

### Requirement: Asignaciones enriquecidas con datos del dictado
El sistema SHALL devolver datos del dictado (materia, carrera, cohorte) al listar asignaciones.

#### Scenario: List incluye datos del dictado
- **WHEN** se consulta GET `/api/v1/equipos/asignaciones`
- **THEN** cada asignación incluye `dictado` anidado con `materia_nombre`, `carrera_nombre`, `cohorte_nombre`
