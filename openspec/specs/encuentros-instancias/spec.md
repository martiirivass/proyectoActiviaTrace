## ADDED Requirements

### Requirement: Editar instancia de encuentro (F6.3)
El sistema SHALL permitir modificar los siguientes campos de una `InstanciaEncuentro`: `estado`, `meet_url`, `video_url`, `comentario`.
El estado SHALL poder transicionar entre: `Programado → Realizado`, `Programado → Cancelado`, `Realizado → Cancelado`, `Cancelado → Programado` (reabrir).
La transición `Realizado → Programado` NO está permitida (no se puede "des-realizar").
`video_url` SOLO puede establecerse cuando `estado = Realizado`.
Solo usuarios con permiso `encuentros:gestionar` y rol PROFESOR o COORDINADOR pueden editar instancias.
El `meet_url` se hereda del slot al crearse la instancia, pero puede modificarse por instancia.

#### Scenario: Marcar instancia como realizada con video_url
- **WHEN** un PROFESOR envía PATCH `/api/v1/encuentros/instancias/{id}` con `estado="Realizado"`, `video_url="https://vimeo.com/123"`
- **THEN** el sistema actualiza la instancia con estado "Realizado" y video_url
- **AND** audita la operación como `ENCUENTRO_EDITAR`

#### Scenario: Cancelar instancia programada
- **WHEN** un PROFESOR envía PATCH `/api/v1/encuentros/instancias/{id}` con `estado="Cancelado"`
- **THEN** el sistema cambia el estado a "Cancelado"
- **AND** el video_url existente (si lo había) se mantiene (no se borra)

#### Scenario: Rechazar transición Realizado → Programado
- **WHEN** un usuario envía PATCH `/api/v1/encuentros/instancias/{id}` con `estado="Programado"` en una instancia con estado "Realizado"
- **THEN** el sistema responde 409 Conflict: no se puede revertir una instancia realizada

#### Scenario: Rechazar video_url si estado no es Realizado
- **WHEN** un usuario envía PATCH `/api/v1/encuentros/instancias/{id}` con `estado="Programado"` y `video_url="https://vimeo.com/123"`
- **THEN** el sistema responde 422: video_url solo permitido cuando estado = Realizado

### Requirement: Obtener instancias de un slot
El sistema SHALL exponer un endpoint GET para listar todas las instancias de un slot dado.

#### Scenario: Listar instancias de slot recurrente
- **WHEN** un PROFESOR envía GET `/api/v1/encuentros/slots/{slot_id}/instancias`
- **THEN** el sistema devuelve todas las instancias del slot ordenadas por fecha ascendente
