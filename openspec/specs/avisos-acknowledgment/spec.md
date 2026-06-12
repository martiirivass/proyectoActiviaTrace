## ADDED Requirements

### Requirement: Confirmar lectura de aviso (acknowledgment)
El sistema SHALL permitir a cualquier usuario autenticado confirmar la lectura de un aviso mediante `POST /api/v1/avisos/{id}/ack`.

**Reglas:**
- Si el aviso no es visible para el usuario (según filtros de alcance), devolver 404
- Si el aviso no requiere ack (`requiere_ack = false`), la confirmación se registra igual (es un no-op útil para tracking)
- La operación es idempotente: si ya existe un ack para ese `(aviso_id, usuario_id)`, el sistema devuelve HTTP 200 sin duplicar el registro
- Se registra `usuario_id`, `aviso_id` y `confirmado_at` (timestamp del servidor)

#### Scenario: Confirmar lectura de aviso que requiere ack
- **WHEN** un ALUMNO autenticado envía `POST /api/v1/avisos/{id}/ack` donde el aviso tiene `requiere_ack = true` y es visible para el alumno
- **THEN** el sistema devuelve HTTP 200 y crea un registro en `AcknowledgmentAviso` con `confirmado_at` igual a la fecha/hora actual

#### Scenario: Confirmar lectura de aviso que no requiere ack
- **WHEN** un PROFESOR autenticado envía `POST /api/v1/avisos/{id}/ack` donde el aviso tiene `requiere_ack = false`
- **THEN** el sistema devuelve HTTP 200 y crea el registro de ack igualmente

#### Scenario: Confirmación duplicada es idempotente
- **WHEN** un COORDINADOR envía `POST /api/v1/avisos/{id}/ack` dos veces seguidas para el mismo aviso
- **THEN** ambas requests devuelven HTTP 200 y existe exactamente un registro en `AcknowledgmentAviso` para ese par `(aviso_id, usuario_id)`

#### Scenario: Confirmar aviso no visible
- **WHEN** un TUTOR envía `POST /api/v1/avisos/{id}/ack` donde el aviso es `PorMateria` y el tutor no está asignado a esa materia
- **THEN** el sistema devuelve HTTP 404 Not Found

---

### Requirement: Indicar si el usuario ya confirmó el aviso
El endpoint `GET /api/v1/avisos` SHALL incluir para cada aviso un campo booleano `acknowledged` que indique si el usuario autenticado ya confirmó la lectura de ese aviso.

#### Scenario: Aviso no confirmado aparece con acknowledged=false
- **WHEN** un ALUMNO envía `GET /api/v1/avisos` y no ha confirmado un aviso visible
- **THEN** el aviso incluye `acknowledged: false`

#### Scenario: Aviso confirmado aparece con acknowledged=true
- **WHEN** un ALUMNO que ya confirmó un aviso envía `GET /api/v1/avisos`
- **THEN** el aviso incluye `acknowledged: true`
