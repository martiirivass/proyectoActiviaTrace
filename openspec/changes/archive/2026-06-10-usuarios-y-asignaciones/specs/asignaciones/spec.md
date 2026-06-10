## ADDED Requirements

### Requirement: Crear asignación
El sistema SHALL permitir crear una asignación que vincula un usuario con un rol dentro de un contexto académico.

#### Scenario: Crear asignación exitosamente
- **WHEN** se envía POST `/api/v1/admin/asignaciones` con `usuario_id`, `rol` (PROFESOR|TUTOR|COORDINADOR|NEXO|ADMIN|FINANZAS), `materia_id`, `carrera_id`, `cohorte_id`, `desde` y opcionalmente `hasta`, `comisiones`, `responsable_id`
- **THEN** retorna 201 con la asignación creada
- **AND** `estado_vigencia` se deriva como "Vigente" si la fecha actual está entre `desde` y `hasta`

#### Scenario: Rol inválido
- **WHEN** se envía POST con un `rol` no válido
- **THEN** retorna 422 con error de validación

#### Scenario: Contexto nullable
- **WHEN** se crea una asignación solo con `usuario_id`, `rol` y `desde` (sin materia/carrera/cohorte)
- **THEN** la asignación se crea exitosamente
- **AND** los campos de contexto son NULL

### Requirement: Listar y obtener asignaciones
El sistema SHALL permitir listar asignaciones con filtros.

#### Scenario: Listar asignaciones paginado
- **WHEN** se consulta GET `/api/v1/admin/asignaciones`
- **THEN** retorna lista paginada de asignaciones del tenant actual

#### Scenario: Filtrar por usuario
- **WHEN** se consulta GET `/api/v1/admin/asignaciones?usuario_id=<uuid>`
- **THEN** retorna solo las asignaciones de ese usuario

#### Scenario: Filtrar por materia
- **WHEN** se consulta GET `/api/v1/admin/asignaciones?materia_id=<uuid>`
- **THEN** retorna solo las asignaciones de esa materia

#### Scenario: Filtrar por rol
- **WHEN** se consulta GET `/api/v1/admin/asignaciones?rol=PROFESOR`
- **THEN** retorna solo las asignaciones con ese rol

### Requirement: Vigencia de asignación
El sistema SHALL derivar `estado_vigencia` comparando fechas.

#### Scenario: Asignación vigente
- **WHEN** la fecha actual está entre `desde` y `hasta` (o `hasta` es NULL)
- **THEN** `estado_vigencia` es "Vigente"

#### Scenario: Asignación vencida
- **WHEN** la fecha actual es posterior a `hasta`
- **THEN** `estado_vigencia` es "Vencida"

#### Scenario: Asignación futura
- **WHEN** la fecha actual es anterior a `desde`
- **THEN** `estado_vigencia` es "Vigente" (o "Pendiente" — se deriva como Vigente porque desde es futuro pero hasta es abierto)

### Requirement: Actualizar y eliminar asignación
El sistema SHALL permitir actualizar y soft-delete asignaciones.

#### Scenario: Actualizar asignación
- **WHEN** se envía PUT `/api/v1/admin/asignaciones/{id}` con nuevos valores
- **THEN** retorna la asignación actualizada

#### Scenario: Soft delete asignación
- **WHEN** se envía DELETE `/api/v1/admin/asignaciones/{id}`
- **THEN** retorna 204
- **AND** la asignación queda con `is_deleted: true`
- **AND** se conserva en el histórico

### Requirement: Jerarquía responsable
El sistema SHALL permitir que una asignación tenga un `responsable_id` que modela la jerarquía docente.

#### Scenario: Asignación con responsable
- **WHEN** se crea una asignación con `responsable_id` válido
- **THEN** el responsable queda registrado
- **AND** se puede consultar la relación desde ambos lados
