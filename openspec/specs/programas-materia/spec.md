## ADDED Requirements

### Requirement: Gestionar programas de materia
El sistema SHALL permitir crear, listar, obtener, actualizar y eliminar (soft delete) programas de materia asociados a una combinación materia × carrera × cohorte.

#### Scenario: Crear programa exitosamente
- **WHEN** se envía POST `/api/v1/programas` con `materia_id`, `carrera_id`, `cohorte_id`, `titulo` y `referencia_archivo` válidos
- **THEN** retorna 201 con el programa creado
- **AND** el programa tiene `cargado_at` con la fecha/hora actual

#### Scenario: Combinación materia-carrera-cohorte duplicada
- **WHEN** se crea un programa con la misma combinación `materia_id`, `carrera_id`, `cohorte_id` que uno existente (no eliminado)
- **THEN** retorna 409 Conflict

#### Scenario: Combinación duplicada con soft-delete permite recrear
- **WHEN** se crea un programa con la misma combinación que uno previamente eliminado (soft delete)
- **THEN** retorna 201 con el nuevo programa

#### Scenario: Obtener programa por ID
- **WHEN** se consulta GET `/api/v1/programas/{id}`
- **THEN** retorna el programa con todos sus campos

#### Scenario: Listar programas filtrados por materia
- **WHEN** se consulta GET `/api/v1/programas?materia_id=<uuid>`
- **THEN** retorna solo los programas de esa materia

#### Scenario: Listar programas filtrados por carrera
- **WHEN** se consulta GET `/api/v1/programas?carrera_id=<uuid>`
- **THEN** retorna solo los programas de esa carrera

#### Scenario: Listar programas filtrados por cohorte
- **WHEN** se consulta GET `/api/v1/programas?cohorte_id=<uuid>`
- **THEN** retorna solo los programas de esa cohorte

#### Scenario: Listar programas con filtros combinados
- **WHEN** se consulta GET `/api/v1/programas?materia_id=<uuid>&carrera_id=<uuid>&cohorte_id=<uuid>`
- **THEN** retorna solo los programas que coinciden con todos los filtros

#### Scenario: Actualizar programa (titulo, referencia_archivo)
- **WHEN** se envía PUT `/api/v1/programas/{id}` con nuevo `titulo` y/o nueva `referencia_archivo`
- **THEN** retorna el programa actualizado

#### Scenario: Soft delete programa
- **WHEN** se envía DELETE `/api/v1/programas/{id}`
- **THEN** retorna 204
- **AND** el programa queda con `is_deleted: true`

#### Scenario: Acceso multi-tenant
- **WHEN** usuario del tenant A lista programas
- **THEN** solo ve programas de su tenant A
- **AND** usuario del tenant B no puede acceder a programas del tenant A
- **AND** al intentar GET de programa de otro tenant retorna 404

### Requirement: Permisos y seguridad
Todas las operaciones sobre programas SHALL requerir el permiso `estructura:gestionar`.

#### Scenario: Endpoint protegido
- **WHEN** se llama a cualquier endpoint ABM de programas sin token o sin permiso `estructura:gestionar`
- **THEN** retorna 403 Forbidden

#### Scenario: Sin permiso no se crea programa
- **WHEN** un usuario sin `estructura:gestionar` intenta crear un programa
- **THEN** retorna 403
- **AND** el programa no se crea
