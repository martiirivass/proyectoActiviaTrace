## ADDED Requirements

### Requirement: Alumno reserva turno de coloquio (HU-47)
El sistema SHALL exponer `POST /api/v1/evaluaciones/reservas` para que un ALUMNO (con permiso `coloquios:reservar`) reserve un turno en una convocatoria.
El body SHALL incluir: `evaluacion_id`, `dia_convocatoria_id`.
El servicio SHALL: validar que el alumno esté en el padrón de convocados, validar `dia_convocatoria_id` pertenezca a la evaluacion, verificar `cupos_ocupados < cupo_maximo` con `SELECT ... FOR UPDATE`, incrementar cupos_ocupados, crear la ReservaEvaluacion con estado Activa.
Si el alumno ya tiene una reserva Activa en la misma convocatoria, SHALL responder 409.
Si no hay cupo, SHALL responder 409 con mensaje "Sin cupo disponible".

#### Scenario: Reserva exitosa con cupo disponible
- **WHEN** un ALUMNO convocado envía POST `/api/v1/evaluaciones/reservas` con evaluacion_id y dia_convocatoria_id válidos
- **THEN** el sistema crea la reserva
- **AND** decrementa el cupo disponible del día
- **AND** responde 201 con los datos de la reserva

#### Scenario: Reserva duplicada en misma convocatoria
- **WHEN** un ALUMNO con reserva Activa existente intenta reservar otra vez en la misma convocatoria
- **THEN** el sistema responde 409 Conflict

#### Scenario: Reserva sin cupo disponible
- **WHEN** todos los cupos del día están ocupados
- **THEN** el sistema responde 409 con mensaje "Sin cupo disponible"

#### Scenario: ALUMNO no convocado intenta reservar
- **WHEN** un ALUMNO que no está en el padrón de la convocatoria intenta reservar
- **THEN** el sistema responde 403 Forbidden

### Requirement: Alumno cancela su reserva (HU-47)
El sistema SHALL exponer `POST /api/v1/evaluaciones/reservas/{id}/cancelar` para que un ALUMNO cancele su propia reserva.
Solo el ALUMNO titular de la reserva puede cancelarla (validado por user_id de sesión).
Al cancelar: estado pasa a Cancelada, cupos_ocupados del día se decrementa.
Si la reserva ya está Cancelada, SHALL responder 409.

#### Scenario: Cancelación exitosa libera cupo
- **WHEN** un ALUMNO cancela su reserva Activa
- **THEN** el sistema marca la reserva como Cancelada
- **AND** libera el cupo del día correspondiente
- **AND** responde 200

#### Scenario: Cancelar reserva ajena
- **WHEN** un ALUMNO intenta cancelar una reserva de otro alumno
- **THEN** el sistema responde 403 Forbidden

### Requirement: Agenda consolidada de reservas (HU-32)
El sistema SHALL exponer `GET /api/v1/evaluaciones/reservas` para COORDINADOR y ADMIN (permiso `coloquios:gestionar`).
Filtros opcionales: `evaluacion_id`, `materia_id`, `fecha_desde`, `fecha_hasta`, `estado` (Activa|Cancelada), `alumno_id`.
La respuesta SHALL ser paginada e incluir datos del alumno (nombre, apellido), materia, fecha, hora.

#### Scenario: Consultar agenda consolidada
- **WHEN** un COORDINADOR envía GET `/api/v1/evaluaciones/reservas?fecha_desde=2026-06-01&fecha_hasta=2026-06-30`
- **THEN** el sistema devuelve todas las reservas del tenant en ese rango paginadas

#### Scenario: ALUMNO consulta sus propias reservas
- **WHEN** un ALUMNO envía GET `/api/v1/evaluaciones/reservas/mis-reservas`
- **THEN** el sistema devuelve solo las reservas del alumno autenticado
