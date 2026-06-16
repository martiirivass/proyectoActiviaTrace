## ADDED Requirements

### Requirement: Cerrar liquidación (hacerla inmutable)

El frontend SHALL permitir a usuarios con permiso `liquidaciones:cerrar` cerrar una liquidación en estado Abierta.

#### Scenario: Cerrar liquidación exitosamente
- **WHEN** el usuario hace clic en "Cerrar" en una liquidación con estado "Abierta"
- **THEN** el frontend muestra un modal de confirmación: "¿Estás seguro de cerrar esta liquidación? Esta acción es irreversible."
- **AND** si el usuario confirma, llama a `POST /api/v1/liquidaciones/{id}/cerrar`
- **AND** muestra un toast de éxito
- **AND** refresca la lista de liquidaciones

#### Scenario: Error 409 — liquidación ya cerrada
- **WHEN** el usuario intenta cerrar una liquidación que ya está en estado "Cerrada"
- **THEN** el frontend muestra un mensaje de error: "La liquidación ya está cerrada"

#### Scenario: Error 403 — sin permiso
- **WHEN** el usuario no tiene permiso `liquidaciones:cerrar`
- **THEN** el botón "Cerrar" no se muestra en la tabla

#### Scenario: Estado de carga durante cierre
- **WHEN** la mutación de cierre está en curso
- **THEN** el botón de confirmación muestra un spinner y se deshabilita
