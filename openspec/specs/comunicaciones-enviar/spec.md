## ADDED Requirements

### Requirement: Usuario puede previsualizar una comunicación antes de enviarla
El sistema SHALL permitir al usuario con permiso `comunicacion:enviar` previsualizar el asunto y cuerpo de un mensaje antes de confirmar su envío (RN-16).

#### Scenario: Preview de comunicación individual
- **WHEN** el usuario envía un asunto, cuerpo, materia_id y lista de destinatarios al endpoint de preview
- **THEN** el sistema valida los datos y retorna una representación del mensaje tal como se enviará (asunto, cuerpo renderizado, cantidad de destinatarios)

#### Scenario: Preview con datos inválidos
- **WHEN** el usuario envía un preview con asunto vacío
- **THEN** el sistema rechaza con error 422 indicando que el asunto es requerido

#### Scenario: Preview con materia inexistente
- **WHEN** el usuario envía un preview con un materia_id que no existe o no corresponde a su tenant
- **THEN** el sistema rechaza con error 404

### Requirement: Usuario puede enviar una comunicación individual a un alumno
El sistema SHALL permitir al usuario con permiso `comunicacion:enviar` enviar una comunicación individual a un alumno de una materia donde tenga asignación docente.

#### Scenario: Enviar comunicación individual exitosamente
- **WHEN** el usuario confirma el envío de una comunicación individual con asunto, cuerpo, materia_id y destinatario_email
- **THEN** el sistema crea un registro de `Comunicacion` con estado Pendiente, destinatario cifrado, sin lote_id asociado, y retorna el ID de la comunicación creada

#### Scenario: Enviar comunicación a alumno no existente en el padrón
- **WHEN** el usuario envía una comunicación a un destinatario que no existe en el padrón activo de la materia
- **THEN** el sistema rechaza con error 422 indicando que el destinatario no pertenece a la materia

#### Scenario: Enviar comunicación sin preview previo
- **WHEN** el usuario intenta enviar una comunicación sin haber realizado el preview primero
- **THEN** el sistema rechaza con error 400 (el preview es obligatorio — RN-16)

### Requirement: Usuario puede enviar comunicaciones masivas agrupadas en lote
El sistema SHALL permitir al usuario con permiso `comunicacion:enviar` crear un lote de comunicaciones masivas a múltiples destinatarios de una misma materia.

#### Scenario: Enviar lote de comunicaciones exitosamente
- **WHEN** el usuario confirma un envío masivo con asunto, cuerpo, materia_id, y una lista de 10 destinatarios
- **THEN** el sistema crea un `LoteComunicacion` con estado Pendiente, 10 registros de `Comunicacion` con estado Pendiente y lote_id asociado, y retorna el ID del lote y la cantidad de mensajes creados

#### Scenario: Lote con destinatarios duplicados
- **WHEN** el usuario envía un lote donde el mismo email de alumno aparece dos veces en la lista de destinatarios
- **THEN** el sistema crea un solo mensaje por destinatario (deduplica por email dentro del mismo lote)

#### Scenario: Lote sin destinatarios
- **WHEN** el usuario intenta crear un lote con lista de destinatarios vacía
- **THEN** el sistema rechaza con error 422 indicando que debe haber al menos un destinatario

### Requirement: Destinatario se cifra en reposo
El sistema SHALL almacenar el campo `destinatario` de `Comunicacion` cifrado con AES-256 usando el type decorator `EncryptedString`.

#### Scenario: Destinatario almacenado cifrado
- **WHEN** el usuario envía una comunicación al email "alumno@test.com"
- **THEN** el sistema almacena el campo `destinatario` cifrado en la base de datos (no legible en texto plano)

#### Scenario: Lectura desencripta automáticamente
- **WHEN** el sistema lee una comunicación existente
- **THEN** el campo `destinatario` se retorna desencriptado para uso del worker o la API

### Requirement: Envío de comunicación genera registro de auditoría
El sistema SHALL crear un registro de auditoría con acción `COMUNICACION_ENVIAR` cada vez que se crea una comunicación (individual o masiva).

#### Scenario: Auditoría de envío individual
- **WHEN** el usuario envía una comunicación individual
- **THEN** el sistema registra en audit_log: acción COMUNICACION_ENVIAR, materia_id, cantidad de destinatarios (1), actor_id

#### Scenario: Auditoría de envío masivo
- **WHEN** el usuario crea un lote de 10 comunicaciones
- **THEN** el sistema registra en audit_log: acción COMUNICACION_ENVIAR, materia_id, lote_id, cantidad de destinatarios (10), actor_id

### Requirement: Envío respeta aislamiento por tenant
El sistema SHALL garantizar que las comunicaciones de un tenant no sean accesibles por usuarios de otro tenant.

#### Scenario: Comunicaciones aisladas por tenant
- **WHEN** un usuario del Tenant A envía una comunicación a un alumno
- **THEN** solo se crean registros con tenant_id del Tenant A, y usuarios del Tenant B no pueden acceder a esos datos
