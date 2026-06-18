## ADDED Requirements

### Requirement: Vaciar datos de padrón de una materia
El sistema SHALL permitir eliminar (soft delete) todos los datos de padrón de una materia, incluyendo todas las versiones y sus entradas.

#### Scenario: Vaciar materia exitosamente
- **WHEN** se envía DELETE `/api/v1/admin/materias/{id}/vaciar`
- **THEN** retorna 204 No Content
- **AND** todas las `VersionPadron` de la materia quedan con `is_deleted: true`
- **AND** todas las `EntradaPadron` de esas versiones quedan con `is_deleted: true`
- **AND** se registra un audit log con acción `PADRON_VACIAR`

#### Scenario: Vaciar materia sin datos
- **WHEN** se envía DELETE `/api/v1/admin/materias/{id}/vaciar` sobre una materia sin versiones de padrón
- **THEN** retorna 204 No Content
- **AND** no se genera error

#### Scenario: Vaciar solo afecta la materia indicada
- **WHEN** se vacía la materia A
- **THEN** los datos de padrón de la materia B no se modifican

#### Scenario: Docente solo puede vaciar sus propias materias
- **WHEN** un PROFESOR intenta vaciar una materia en la que no tiene asignación
- **THEN** retorna 403 Forbidden

#### Scenario: Coordinador puede vaciar cualquier materia
- **WHEN** un COORDINADOR envía DELETE `/api/v1/admin/materias/{id}/vaciar` para cualquier materia del tenant
- **THEN** retorna 204 No Content

### Requirement: Auditoría de operaciones de padrón
El sistema SHALL registrar en el audit log todas las operaciones de importación y vaciado de padrón.

#### Scenario: Confirmar importación genera audit
- **WHEN** se confirma una importación de padrón
- **THEN** se registra un `AuditLog` con `accion: "PADRON_CARGAR"`
- **AND** el detalle incluye `materia_id`, `cohorte_id`, `version_id` y `filas_afectadas`

#### Scenario: Vaciar materia genera audit
- **WHEN** se vacía una materia
- **THEN** se registra un `AuditLog` con `accion: "PADRON_VACIAR"`
- **AND** el detalle incluye `materia_id` y `versiones_afectadas`
