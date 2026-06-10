## ADDED Requirements

### Requirement: Gestionar carreras
El sistema SHALL permitir crear, listar, obtener, actualizar y eliminar (soft delete) carreras.

#### Scenario: Crear carrera exitosamente
- **WHEN** se envía POST `/api/v1/admin/carreras` con `codigo` y `nombre` válidos
- **THEN** retorna 201 con la carrera creada
- **AND** la carrera tiene `estado: "Activa"` por defecto

#### Scenario: Código duplicado en el mismo tenant
- **WHEN** se crea una carrera con un `codigo` ya existente en el mismo tenant
- **THEN** retorna 409 Conflict

#### Scenario: Mismo código en distintos tenants
- **WHEN** dos tenants crean carreras con el mismo `codigo`
- **THEN** ambas creaciones son exitosas

#### Scenario: Obtener carrera por ID
- **WHEN** se consulta GET `/api/v1/admin/carreras/{id}`
- **THEN** retorna la carrera con todos sus campos

#### Scenario: Listar carreras paginado
- **WHEN** se consulta GET `/api/v1/admin/carreras`
- **THEN** retorna lista paginada de carreras del tenant actual

#### Scenario: Actualizar carrera
- **WHEN** se envía PUT `/api/v1/admin/carreras/{id}` con nuevos datos
- **THEN** retorna la carrera actualizada

#### Scenario: Soft delete carrera
- **WHEN** se envía DELETE `/api/v1/admin/carreras/{id}`
- **THEN** retorna 204
- **AND** la carrera queda con `is_deleted: true`

#### Scenario: Acceso multi-tenant
- **WHEN** usuario del tenant A lista carreras
- **THEN** solo ve carreras de su tenant A

### Requirement: Gestionar cohortes
El sistema SHALL permitir crear, listar, obtener, actualizar y eliminar (soft delete) cohortes, validadas contra la carrera.

#### Scenario: Crear cohorte exitosamente
- **WHEN** se envía POST `/api/v1/admin/cohortes` con `carrera_id`, `nombre`, `anio` válidos
- **THEN** retorna 201 con la cohorte creada
- **AND** la cohorte tiene `estado: "Activa"` por defecto

#### Scenario: Nombre duplicado en misma carrera y tenant
- **WHEN** se crea una cohorte con `nombre` ya existente en la misma carrera y tenant
- **THEN** retorna 409 Conflict

#### Scenario: Carrera inactiva no admite cohortes activas
- **WHEN** se intenta crear una cohorte para una carrera con `estado: "Inactiva"`
- **THEN** retorna 422 con error de validación

#### Scenario: Listar cohortes filtradas por carrera
- **WHEN** se consulta GET `/api/v1/admin/cohortes?carrera_id=<uuid>`
- **THEN** retorna solo las cohortes de esa carrera

#### Scenario: Soft delete cohorte
- **WHEN** se envía DELETE `/api/v1/admin/cohortes/{id}`
- **THEN** retorna 204
- **AND** la cohorte queda con `is_deleted: true`

### Requirement: Gestionar materias (catálogo)
El sistema SHALL permitir crear, listar, obtener, actualizar y eliminar (soft delete) materias del catálogo del tenant.

#### Scenario: Crear materia exitosamente
- **WHEN** se envía POST `/api/v1/admin/materias` con `codigo` y `nombre` válidos
- **THEN** retorna 201 con la materia creada
- **AND** la materia tiene `estado: "Activa"` por defecto

#### Scenario: Código de materia duplicado en el mismo tenant
- **WHEN** se crea una materia con `codigo` ya existente en el mismo tenant
- **THEN** retorna 409 Conflict

#### Scenario: Listar materias paginado
- **WHEN** se consulta GET `/api/v1/admin/materias`
- **THEN** retorna lista paginada de materias del tenant actual

#### Scenario: Soft delete materia
- **WHEN** se envía DELETE `/api/v1/admin/materias/{id}`
- **THEN** retorna 204
- **AND** la materia queda con `is_deleted: true`

### Requirement: Gestionar dictados (instancia materia × carrera × cohorte)
El sistema SHALL permitir crear, listar, obtener, actualizar y eliminar (soft delete) dictados.

#### Scenario: Crear dictado exitosamente
- **WHEN** se envía POST `/api/v1/admin/dictados` con `materia_id`, `carrera_id`, `cohorte_id` y `nombre` válidos
- **THEN** retorna 201 con el dictado creado

#### Scenario: Combinación materia-cohorte duplicada
- **WHEN** se crea un dictado con la misma `materia_id` y `cohorte_id` que uno existente
- **THEN** retorna 409 Conflict

#### Scenario: Dictado tiene nombre descriptivo propio
- **WHEN** se crea un dictado con `nombre` distinto al de la materia
- **THEN** el dictado se crea con ese nombre
- **AND** el nombre de la materia permanece sin cambios

#### Scenario: Listar dictados filtrados por materia o cohorte
- **WHEN** se consulta GET `/api/v1/admin/dictados?materia_id=<uuid>` o `?cohorte_id=<uuid>`
- **THEN** retorna solo los dictados que coinciden

#### Scenario: Soft delete dictado
- **WHEN** se envía DELETE `/api/v1/admin/dictados/{id}`
- **THEN** retorna 204
- **AND** el dictado queda con `is_deleted: true`

### Requirement: Permisos y seguridad
Todas las operaciones de estructura académica SHALL requerir el permiso `estructura:gestionar`.

#### Scenario: Endpoint protegido
- **WHEN** se llama a cualquier endpoint ABM sin token o sin permiso `estructura:gestionar`
- **THEN** retorna 403 Forbidden

#### Scenario: Sin permiso no se crea carrera
- **WHEN** un usuario sin `estructura:gestionar` intenta crear una carrera
- **THEN** retorna 403
- **AND** la carrera no se crea
