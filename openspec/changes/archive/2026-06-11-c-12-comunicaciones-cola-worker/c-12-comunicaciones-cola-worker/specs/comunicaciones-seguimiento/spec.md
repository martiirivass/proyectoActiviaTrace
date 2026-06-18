## ADDED Requirements

### Requirement: Usuario puede consultar estado de comunicaciones por lote
El sistema SHALL permitir al usuario con permiso `comunicacion:enviar` consultar el estado de todas las comunicaciones de un lote específico.

#### Scenario: Consultar lote con distribución de estados
- **WHEN** el usuario consulta un lote con id específico
- **THEN** el sistema retorna el resumen del lote (id, materia, total_mensajes, estado del lote) y la distribución de estados de sus mensajes (Pendiente, Enviando, Enviado, Error, Cancelado) con cantidades

#### Scenario: Consultar lote inexistente
- **WHEN** el usuario consulta un lote_id que no existe
- **THEN** el sistema rechaza con error 404

#### Scenario: Consultar lote de otro tenant
- **WHEN** el usuario consulta un lote que pertenece a otro tenant
- **THEN** el sistema rechaza con error 404 (el lote no existe para este tenant)

### Requirement: Usuario puede consultar estado de comunicaciones por materia
El sistema SHALL permitir al usuario con permiso `comunicacion:enviar` consultar las comunicaciones asociadas a una materia donde tenga asignación docente.

#### Scenario: Consultar comunicaciones por materia
- **WHEN** el usuario consulta las comunicaciones de una materia_id específica
- **THEN** el sistema retorna una lista paginada de comunicaciones de esa materia con: id, destinatario (enmascarado), asunto, estado, created_at, enviado_at

#### Scenario: Consultar materia sin comunicaciones
- **WHEN** el usuario consulta una materia que no tiene comunicaciones
- **THEN** el sistema retorna una lista vacía

#### Scenario: Consultar materia sin asignación
- **WHEN** el usuario (PROFESOR) consulta comunicaciones de una materia a la que no está asignado
- **THEN** el sistema retorna una lista vacía (scope de datos)

### Requirement: Sistema expone distribución de estados agregados
El sistema SHALL exponer un resumen agregado de estados de comunicación para un dashboard o vista general.

#### Scenario: Distribución global por materia
- **WHEN** el usuario consulta la distribución de estados para una materia
- **THEN** el sistema retorna un objeto con conteos: {pendiente: N, enviando: N, enviado: N, error: N, cancelado: N}

#### Scenario: Distribución vacía
- **WHEN** no hay comunicaciones para la materia consultada
- **THEN** el sistema retorna todos los conteos en 0

### Requirement: Usuario puede ver detalle de una comunicación individual
El sistema SHALL permitir al usuario con permiso `comunicacion:enviar` ver el detalle completo de una comunicación específica.

#### Scenario: Ver detalle de comunicación
- **WHEN** el usuario consulta una comunicación por su ID
- **THEN** el sistema retorna: destinatario (enmascarado parcialmente, ej: "alum***@test.com"), asunto, cuerpo, estado, materia_id, created_at, enviado_at, y error_msg si estado es Error

#### Scenario: Consultar comunicación inexistente
- **WHEN** el usuario consulta un ID de comunicación que no existe
- **THEN** el sistema rechaza con error 404
