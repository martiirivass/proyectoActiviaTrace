## ADDED Requirements

### Requirement: Docente ve sus propios equipos
El sistema SHALL permitir que un usuario autenticado consulte sus propias asignaciones activas sin necesidad de permisos especiales.

#### Scenario: Ver mis equipos exitosamente
- **WHEN** un PROFESOR envía GET `/api/v1/equipos/mis-equipos`
- **THEN** retorna 200 con la lista de asignaciones donde `usuario_id = current_user.id`
- **AND** cada asignación incluye datos del dictado (materia, carrera, cohorte)
- **AND** cada asignación incluye `estado_vigencia` derivado

#### Scenario: Filtrar mis equipos por estado
- **WHEN** un PROFESOR envía GET `/api/v1/equipos/mis-equipos?estado=Vigente`
- **THEN** retorna solo las asignaciones vigentes del usuario

#### Scenario: Filtrar mis equipos por rol
- **WHEN** un TUTOR envía GET `/api/v1/equipos/mis-equipos?rol=TUTOR`
- **THEN** retorna solo las asignaciones con ese rol

#### Scenario: Usuario sin asignaciones ve lista vacía
- **WHEN** un usuario sin ninguna asignación consulta sus equipos
- **THEN** retorna 200 con lista vacía

### Requirement: Coordinador consulta asignaciones del tenant
El sistema SHALL permitir a COORDINADOR y ADMIN consultar todas las asignaciones con filtros avanzados.

#### Scenario: Listar todas las asignaciones del tenant
- **WHEN** un COORDINADOR envía GET `/api/v1/equipos/asignaciones`
- **THEN** retorna lista paginada de todas las asignaciones del tenant

#### Scenario: Filtrar por dictado
- **WHEN** se envía GET `/api/v1/equipos/asignaciones?dictado_id=<uuid>`
- **THEN** retorna solo asignaciones de ese dictado

#### Scenario: Filtrar por carrera
- **WHEN** se envía GET `/api/v1/equipos/asignaciones?carrera_id=<uuid>`
- **THEN** retorna solo asignaciones de dictados de esa carrera

#### Scenario: Combinar filtros
- **WHEN** se envía GET `/api/v1/equipos/asignaciones?carrera_id=<uuid>&rol=PROFESOR`
- **THEN** retorna solo PROFESORES de esa carrera
