## ADDED Requirements

### Requirement: Crear usuario con PII
El sistema SHALL permitir crear un usuario con todos los campos del modelo E4, almacenando los marcados como `[cifrado]` encriptados con AES-256-GCM.

#### Scenario: Crear usuario exitosamente
- **WHEN** se envía POST `/api/v1/admin/usuarios` con `email`, `nombre`, `apellido`, `dni`, `password` y opcionales (`cuil`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo`, `legajo_profesional`, `facturador`)
- **THEN** retorna 201 con el usuario creado
- **AND** `dni`, `cuil`, `cbu`, `alias_cbu` se almacenan cifrados en la DB
- **AND** la respuesta NO incluye `password_hash`, `totp_secret`

#### Scenario: Email duplicado en el mismo tenant
- **WHEN** se crea un usuario con un `email` ya existente en el mismo tenant
- **THEN** retorna 409 Conflict

#### Scenario: Mismo email en distintos tenants
- **WHEN** dos tenants crean usuarios con el mismo email
- **THEN** ambas creaciones son exitosas

#### Scenario: Password se hashea con Argon2id
- **WHEN** se crea un usuario con `password`
- **THEN** el campo `password_hash` se almacena con Argon2id
- **AND** la contraseña original no se almacena en texto plano

### Requirement: Listar y obtener usuarios
El sistema SHALL permitir listar y obtener usuarios del tenant actual.

#### Scenario: Listar usuarios paginado
- **WHEN** se consulta GET `/api/v1/admin/usuarios`
- **THEN** retorna lista paginada de usuarios del tenant actual
- **AND** los campos PII cifrados aparecen desencriptados en la respuesta
- **AND** NO incluye soft-deleted

#### Scenario: Obtener usuario por ID
- **WHEN** se consulta GET `/api/v1/admin/usuarios/{id}`
- **THEN** retorna el usuario con todos sus campos no sensibles

#### Scenario: Usuario soft-deleted no aparece
- **WHEN** se consulta un usuario soft-deleted por ID
- **THEN** retorna 404

### Requirement: Actualizar usuario
El sistema SHALL permitir actualizar datos de un usuario.

#### Scenario: Actualizar datos personales
- **WHEN** se envía PUT `/api/v1/admin/usuarios/{id}` con nuevos valores
- **THEN** retorna el usuario actualizado
- **AND** los campos PII se re-encriptan si fueron modificados

#### Scenario: Actualizar password
- **WHEN** se envía PUT `/api/v1/admin/usuarios/{id}` con `password`
- **THEN** el password se hashea con Argon2id
- **AND** se actualiza `password_hash`

### Requirement: Soft delete usuario
El sistema SHALL permitir soft delete de usuarios.

#### Scenario: Soft delete usuario
- **WHEN** se envía DELETE `/api/v1/admin/usuarios/{id}`
- **THEN** retorna 204
- **AND** el usuario queda con `is_deleted: true`

### Requirement: PII no expuesta
El sistema SHALL garantizar que los campos PII cifrados (`dni`, `cuil`, `cbu`, `alias_cbu`) nunca se expongan en texto plano en logs, errores ni responses no autorizados.

#### Scenario: PII cifrada en DB
- **WHEN** se consulta directamente la tabla `users` en la DB
- **THEN** los campos `dni`, `cuil`, `cbu`, `alias_cbu` se ven como texto cifrado (ilegible)

#### Scenario: PII desencriptada en respuesta autorizada
- **WHEN** un usuario autorizado obtiene un usuario via API
- **THEN** los campos PII se muestran desencriptados correctamente
