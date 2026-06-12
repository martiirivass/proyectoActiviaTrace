## ADDED Requirements

### Requirement: Obtener estadísticas de confirmación de un aviso
El sistema SHALL exponer `GET /api/v1/avisos/{id}/stats` para que usuarios con permiso `avisos:publicar` (COORDINADOR, ADMIN) consulten las estadísticas de confirmación de un aviso específico.

**Campos del response:**
- `aviso_id` (UUID)
- `total_usuarios_alcanzados` (integer) — cantidad estimada de usuarios que deberían ver este aviso según alcance y asignaciones activas al momento de la consulta
- `total_acknowledgments` (integer) — count de registros en `AcknowledgmentAviso` para este aviso
- `porcentaje_confirmacion` (float, 0-100) — `(total_acknowledgments / total_usuarios_alcanzados) * 100`, redondeado a 2 decimales. Si `total_usuarios_alcanzados = 0`, devuelve 0.

#### Scenario: Obtener stats de aviso global
- **WHEN** un ADMIN envía `GET /api/v1/avisos/{id}/stats` de un aviso Global con 100 usuarios alcanzados y 75 acknowledges
- **THEN** el sistema devuelve `total_usuarios_alcanzados: 100`, `total_acknowledgments: 75`, `porcentaje_confirmacion: 75.0`

#### Scenario: Stats de aviso sin acknowledges
- **WHEN** un COORDINADOR envía `GET /api/v1/avisos/{id}/stats` de un aviso recién creado sin confirms
- **THEN** el sistema devuelve `total_acknowledgments: 0`, `porcentaje_confirmacion: 0.0`

#### Scenario: Stats sin permiso avisos:publicar
- **WHEN** un ALUMNO autenticado envía `GET /api/v1/avisos/{id}/stats`
- **THEN** el sistema devuelve HTTP 403 Forbidden

#### Scenario: Stats de aviso inexistente
- **WHEN** un ADMIN envía `GET /api/v1/avisos/{uuid-inexistente}/stats`
- **THEN** el sistema devuelve HTTP 404 Not Found

---

### Requirement: Listar usuarios que confirmaron un aviso
El sistema SHALL exponer `GET /api/v1/avisos/{id}/acks` para que usuarios con permiso `avisos:publicar` consulten el listado de usuarios que confirmaron la lectura de un aviso.

**Paginación**: default 20, máximo 100.
**Respuesta**: lista de `{usuario_id, nombre, apellidos, email, confirmado_at}`.

#### Scenario: Listar acknowledges de aviso
- **WHEN** un COORDINADOR envía `GET /api/v1/avisos/{id}/acks`
- **THEN** el sistema devuelve HTTP 200 con la lista paginada de usuarios que confirmaron

#### Scenario: Listar acknowledges sin data
- **WHEN** un ADMIN envía `GET /api/v1/avisos/{id}/acks` de un aviso sin confirms
- **THEN** el sistema devuelve HTTP 200 con lista vacía
