## ADDED Requirements

### Requirement: Registrar acción de auditoría
El sistema SHALL permitir registrar una acción de auditoría con todos los campos del modelo E-AUD.

#### Scenario: Registro exitoso sin impersonación
- **WHEN** un usuario realiza una acción auditada
- **THEN** el sistema crea un registro `AuditLog` con `actor_id`, `accion`, `detalle`, `ip`, `user_agent`, `fecha_hora` y `tenant_id`
- **AND** `impersonado_id` es NULL

#### Scenario: Registro exitoso con impersonación
- **WHEN** un usuario ADMIN realiza una acción bajo impersonación
- **THEN** el `actor_id` es el usuario REAL (quien impersona)
- **AND** `impersonado_id` es el usuario impersonado

#### Scenario: Rechazar registro sin actor_id
- **WHEN** se intenta crear un `AuditLog` sin `actor_id`
- **THEN** el sistema rechaza la operación con error de validación

### Requirement: Inmutabilidad del log
Ningún registro `AuditLog` SHALL poder modificarse ni eliminarse una vez creado.

#### Scenario: No se puede actualizar un registro
- **WHEN** se intenta llamar a `update()` en un registro `AuditLog`
- **THEN** el repositorio lanza un error (el método no existe)

#### Scenario: No se puede eliminar un registro
- **WHEN** se intenta llamar a `delete()` en un registro `AuditLog`
- **THEN** el repositorio lanza un error (el método no existe)

### Requirement: Consultar log de auditoría
El sistema SHALL exponer un endpoint GET `/api/v1/audit/log` que permita consultar registros con filtros.

#### Scenario: Consulta paginada sin filtros
- **WHEN** se consulta GET `/api/v1/audit/log`
- **THEN** retorna los registros del tenant actual paginados por fecha descendente
- **AND** `impersonado_id` es incluido cuando presente

#### Scenario: Filtrar por código de acción
- **WHEN** se consulta GET `/api/v1/audit/log?accion=CALIFICACIONES_IMPORTAR`
- **THEN** retorna solo los registros con ese código de acción

#### Scenario: Filtrar por actor
- **WHEN** se consulta GET `/api/v1/audit/log?actor_id=<uuid>`
- **THEN** retorna solo los registros de ese actor

#### Scenario: Filtrar por rango de fechas
- **WHEN** se consulta GET `/api/v1/audit/log?desde=2025-01-01&hasta=2025-12-31`
- **THEN** retorna solo los registros dentro del rango

#### Scenario: Acceso multi-tenant seguro
- **WHEN** el usuario A del tenant 1 consulta el log
- **THEN** solo ve registros de su propio tenant
- **AND** nunca ve registros de otros tenants

### Requirement: Códigos de acción estandarizados
El sistema SHALL definir códigos de acción como constantes tipadas.

#### Scenario: Códigos predefinidos existen
- **WHEN** se importa el módulo de códigos de acción
- **THEN** existen constantes para: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`

### Requirement: Middleware de auditoría opt-in
El sistema SHALL proveer un mecanismo opt-in para auditar requests HTTP automáticamente.

#### Scenario: Decorador marca endpoint para auditoría
- **WHEN** un endpoint usa el decorador/dependency `AuditDependency`
- **THEN** cada request exitoso a ese endpoint genera un registro `AuditLog`

#### Scenario: Endpoint sin decorador no se audita
- **WHEN** un endpoint NO usa `AuditDependency`
- **THEN** no se genera ningún registro de auditoría automático
