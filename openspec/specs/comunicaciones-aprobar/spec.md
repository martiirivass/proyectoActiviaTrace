## ADDED Requirements

### Requirement: Usuario puede listar lotes pendientes de aprobación
El sistema SHALL permitir al usuario con permiso `comunicacion:aprobar` listar los lotes de comunicaciones en estado Pendiente de aprobación.

#### Scenario: Listar lotes pendientes
- **WHEN** el usuario con permiso `comunicacion:aprobar` consulta los lotes pendientes
- **THEN** el sistema retorna una lista de lotes con: id, materia_id, enviado_por, total_mensajes, created_at

#### Scenario: Sin lotes pendientes
- **WHEN** no hay lotes en estado Pendiente
- **THEN** el sistema retorna una lista vacía

#### Scenario: Usuario sin permiso no puede listar
- **WHEN** un usuario sin permiso `comunicacion:aprobar` intenta listar lotes pendientes
- **THEN** el sistema rechaza con error 403

### Requirement: Usuario puede aprobar un lote de comunicaciones
El sistema SHALL permitir al usuario con permiso `comunicacion:aprobar` aprobar un lote completo de comunicaciones. Los mensajes del lote pasan a estar disponibles para que el worker los procese.

#### Scenario: Aprobar lote exitosamente
- **WHEN** el usuario aprueba un lote en estado Pendiente
- **THEN** el sistema actualiza el lote a estado Aprobado, registra aprobado_por (ID del aprobador) y aprobado_en (timestamp), y los mensajes del lote quedan disponibles para el worker

#### Scenario: Aprobar lote ya aprobado
- **WHEN** el usuario intenta aprobar un lote que ya está en estado Aprobado
- **THEN** el sistema rechaza con error 409 (conflicto — el lote ya fue aprobado)

#### Scenario: Aprobar lote rechazado
- **WHEN** el usuario intenta aprobar un lote en estado Rechazado
- **THEN** el sistema rechaza con error 409 (el lote no puede revertirse)

### Requirement: Usuario puede rechazar un lote de comunicaciones
El sistema SHALL permitir al usuario con permiso `comunicacion:aprobar` rechazar un lote completo de comunicaciones. Los mensajes del lote se cancelan.

#### Scenario: Rechazar lote exitosamente
- **WHEN** el usuario rechaza un lote en estado Pendiente
- **THEN** el sistema actualiza el lote a estado Rechazado, registra rechazado_en (timestamp), actualiza todos los mensajes del lote a estado Cancelado, y retorna la cantidad de mensajes cancelados

#### Scenario: Rechazar lote ya procesado
- **WHEN** el usuario intenta rechazar un lote que ya fue aprobado y algunos mensajes ya están en estado Enviado
- **THEN** el sistema rechaza con error 409 (el lote ya está en proceso)

### Requirement: Aprobación o rechazo genera registro de auditoría
El sistema SHALL registrar en audit_log las acciones de aprobación y rechazo de lotes.

#### Scenario: Auditoría de aprobación
- **WHEN** el usuario aprueba un lote
- **THEN** el sistema registra en audit_log: acción COMUNICACION_ENVIAR, detalle con tipo "aprobacion_lote", lote_id, materia_id, total_mensajes, actor_id

#### Scenario: Auditoría de rechazo
- **WHEN** el usuario rechaza un lote
- **THEN** el sistema registra en audit_log: acción COMUNICACION_ENVIAR, detalle con tipo "rechazo_lote", lote_id, materia_id, total_mensajes, actor_id
