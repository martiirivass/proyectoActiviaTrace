## ADDED Requirements

### Requirement: Gestionar fechas académicas
El sistema SHALL permitir crear, listar, obtener, actualizar y eliminar (soft delete) fechas académicas (parciales, TPs, coloquios, recuperatorios) por materia × cohorte × tipo × número dentro de un período.

#### Scenario: Crear fecha académica exitosamente
- **WHEN** se envía POST `/api/v1/fechas-academicas` con `materia_id`, `cohorte_id`, `tipo`, `numero`, `periodo`, `fecha` y `titulo` válidos
- **THEN** retorna 201 con la fecha creada

#### Scenario: Combinación materia-cohorte-tipo-numero duplicada en el mismo periodo
- **WHEN** se crea una fecha con la misma `materia_id`, `cohorte_id`, `tipo`, `numero` y `periodo` que una existente (no eliminada)
- **THEN** retorna 409 Conflict

#### Scenario: Mismo tipo y número en distinto periodo
- **WHEN** se crea una fecha con misma `materia_id`, `cohorte_id`, `tipo` y `numero` pero distinto `periodo`
- **THEN** retorna 201 con la nueva fecha

#### Scenario: Tipo válido
- **WHEN** se envía POST con `tipo` que no está en el enum `Parcial|TP|Coloquio|Recuperatorio`
- **THEN** retorna 422 con error de validación

#### Scenario: Número debe ser positivo
- **WHEN** se envía POST con `numero` igual a 0 o negativo
- **THEN** retorna 422 con error de validación

#### Scenario: Obtener fecha académica por ID
- **WHEN** se consulta GET `/api/v1/fechas-academicas/{id}`
- **THEN** retorna la fecha con todos sus campos

#### Scenario: Listar fechas filtradas por materia
- **WHEN** se consulta GET `/api/v1/fechas-academicas?materia_id=<uuid>`
- **THEN** retorna solo las fechas de esa materia
- **AND** las fechas vienen ordenadas por `fecha` ascendente

#### Scenario: Listar fechas filtradas por cohorte
- **WHEN** se consulta GET `/api/v1/fechas-academicas?cohorte_id=<uuid>`
- **THEN** retorna solo las fechas de esa cohorte

#### Scenario: Listar fechas filtradas por tipo
- **WHEN** se consulta GET `/api/v1/fechas-academicas?tipo=Parcial`
- **THEN** retorna solo las fechas de tipo Parcial

#### Scenario: Listar fechas filtradas por periodo
- **WHEN** se consulta GET `/api/v1/fechas-academicas?periodo=2026-1`
- **THEN** retorna solo las fechas de ese periodo

#### Scenario: Listar fechas con filtros combinados
- **WHEN** se consulta GET `/api/v1/fechas-academicas?materia_id=<uuid>&cohorte_id=<uuid>&tipo=Parcial&periodo=2026-1`
- **THEN** retorna solo las fechas que coinciden con todos los filtros

#### Scenario: Actualizar fecha académica
- **WHEN** se envía PUT `/api/v1/fechas-academicas/{id}` con nuevos datos
- **THEN** retorna la fecha actualizada

#### Scenario: Soft delete fecha académica
- **WHEN** se envía DELETE `/api/v1/fechas-academicas/{id}`
- **THEN** retorna 204
- **AND** la fecha queda con `is_deleted: true`

#### Scenario: Acceso multi-tenant
- **WHEN** usuario del tenant A lista fechas académicas
- **THEN** solo ve fechas de su tenant A
- **AND** usuario del tenant B no puede acceder a fechas del tenant A
- **AND** al intentar GET de fecha de otro tenant retorna 404

### Requirement: Exportar fechas académicas para LMS
El sistema SHALL generar un fragmento de contenido (texto/HTML) con las fechas académicas filtradas, listo para copiar y publicar en el aula virtual del LMS.

#### Scenario: Exportar fechas filtradas
- **WHEN** se consulta GET `/api/v1/fechas-academicas/exportar-lms?materia_id=<uuid>&cohorte_id=<uuid>&periodo=2026-1`
- **THEN** retorna 200 con `Content-Type: text/plain` (o `text/html`)
- **AND** el contenido incluye las fechas formateadas según el tipo y número

#### Scenario: Exportar sin fechas
- **WHEN** se consulta GET `/api/v1/fechas-academicas/exportar-lms?materia_id=<uuid>` y no hay fechas para los filtros
- **THEN** retorna 200 con contenido que indica que no hay fechas registradas

#### Scenario: Exportar requiere al menos materia_id
- **WHEN** se consulta GET `/api/v1/fechas-academicas/exportar-lms` sin filtros
- **THEN** retorna 422 con error de validación (materia_id es requerido)

### Requirement: Permisos y seguridad
Todas las operaciones sobre fechas académicas SHALL requerir el permiso `estructura:gestionar`.

#### Scenario: Endpoint protegido
- **WHEN** se llama a cualquier endpoint ABM de fechas académicas sin token o sin permiso `estructura:gestionar`
- **THEN** retorna 403 Forbidden

#### Scenario: Exportar LMS requiere permiso
- **WHEN** un usuario sin `estructura:gestionar` intenta exportar fechas
- **THEN** retorna 403
