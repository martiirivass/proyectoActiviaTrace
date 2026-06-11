## ADDED Requirements

### Requirement: Crear slot recurrente (F6.1)
El sistema SHALL permitir crear un slot de encuentro recurrente que genere N instancias automáticamente.
Los datos REQUERIDOS son: `materia_id`, `asignacion_id`, `titulo`, `dia_semana`, `hora`, `fecha_inicio`, `cant_semanas`, `meet_url`.
Los datos OPCIONALES son: `meet_url`, `comentario` (a nivel slot).
El slot se crea con `fecha_unica = NULL` y `vig_desde = fecha_inicio`, `vig_hasta = fecha_inicio + cant_semanas semanas`.
El sistema SHALL generar exactamente `cant_semanas` instancias, una por semana, comenzando en `fecha_inicio`, respetando `dia_semana`.
Cada instancia generada SHALL tener estado `Programado`.
Todas las instancias SHALL pertenecer al mismo `tenant_id` y `materia_id` que el slot.
Si `cant_semanas <= 0` el sistema SHALL rechazar la operación con error de validación.
Solo usuarios con permiso `encuentros:gestionar` y rol PROFESOR o COORDINADOR pueden crear slots.

#### Scenario: Creación exitosa de slot recurrente con 4 instancias
- **WHEN** un PROFESOR envía POST `/api/v1/encuentros/slots` con `dia_semana="Lunes"`, `hora="18:00"`, `fecha_inicio="2026-03-02"`, `cant_semanas=4`, `materia_id=UUID`, `titulo="Clase Semanal"`
- **THEN** el sistema crea 1 slot y 4 instancias (2026-03-02, 2026-03-09, 2026-03-16, 2026-03-23) todas con estado "Programado"
- **AND** la respuesta incluye `slot_id` y `instancias_creadas=4`

#### Scenario: Rechazo si cant_semanas <= 0
- **WHEN** un PROFESOR envía POST `/api/v1/encuentros/slots` con `cant_semanas=0` (sin `fecha_unica`)
- **THEN** el sistema responde 422 con error de validación indicando que para modo recurrente `cant_semanas` debe ser > 0

#### Scenario: Aislamiento por tenant
- **WHEN** se crea un slot en tenant A
- **THEN** usuarios del tenant B NO pueden ver ni acceder a ese slot ni sus instancias

### Requirement: Crear encuentro único (F6.2)
El sistema SHALL permitir crear un encuentro puntual sin recurrencia.
Los datos REQUERIDOS son: `materia_id`, `asignacion_id`, `titulo`, `fecha_unica`, `hora`.
El sistema SHALL crear 1 `SlotEncuentro` con `cant_semanas=0`, `fecha_unica=<fecha>`, `dia_semana=NULL`.
El sistema SHALL crear exactamente 1 `InstanciaEncuentro` con esa fecha y hora.
El slot único generado NO debe permitir edición de recurrencia posterior.

#### Scenario: Creación exitosa de encuentro único
- **WHEN** un COORDINADOR envía POST `/api/v1/encuentros/slots` con `fecha_unica="2026-04-15"`, `hora="10:00"`, `cant_semanas=0`, `materia_id=UUID`, `titulo="Consulta Pre-Parcial"`
- **THEN** el sistema crea 1 slot con `cant_semanas=0` y 1 instancia con fecha 2026-04-15
- **AND** la respuesta incluye `slot_id` y `instancias_creadas=1`

#### Scenario: Validación exclusión mutua de modos
- **WHEN** un usuario envía POST `/api/v1/encuentros/slots` con `cant_semanas > 0` Y `fecha_unica` presente
- **THEN** el sistema responde 422: los modos recurrente y único son mutuamente excluyentes
