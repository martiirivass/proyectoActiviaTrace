## ADDED Requirements

### Requirement: Usuario confirma lectura de un aviso (acknowledgment)
El sistema SHALL permitir a cualquier usuario autenticado confirmar la lectura de un aviso que requiere ack, mediante POST /api/avisos/{id}/acknowledge. La confirmación es única por par (aviso, usuario). Si el ack ya existe, retorna 409 Conflict.

#### Scenario: Confirmar lectura de aviso con ack requerido
- **WHEN** ALUMNO envía POST /api/avisos/{id}/acknowledge a un aviso con requiere_ack=true
- **THEN** el sistema retorna 201 y registra la confirmación con timestamp

#### Scenario: Confirmar lectura duplicada retorna 409
- **WHEN** el mismo usuario envía POST /api/avisos/{id}/acknowledge dos veces al mismo aviso
- **THEN** la segunda solicitud retorna 409 Conflict

#### Scenario: Confirmar lectura de aviso sin ack requerido retorna 400
- **WHEN** TUTOR envía POST /api/avisos/{id}/acknowledge a un aviso con requiere_ack=false
- **THEN** el sistema retorna 400 Bad Request (el aviso no requiere confirmación)

### Requirement: Una vez confirmado, el aviso no se muestra como pendiente
El sistema SHALL excluir de la lista visible para el usuario aquellos avisos con requiere_ack=true que ya fueron confirmados por ese usuario.

#### Scenario: Aviso confirmado no aparece en listado del usuario
- **WHEN** PROFESOR confirma un aviso y luego consulta su listado de avisos pendientes
- **THEN** el aviso confirmado no aparece en el listado del usuario
