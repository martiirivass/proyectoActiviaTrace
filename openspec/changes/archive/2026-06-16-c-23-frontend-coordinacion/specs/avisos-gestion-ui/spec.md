## ADDED Requirements

### Requirement: COORDINADOR/ADMIN can CRUD avisos (F3.5)
The system SHALL provide a full ABM interface for avisos with fields: titulo, contenido, alcance (Global/PorMateria/PorCohorte/PorRol), severidad, vigencia inicio/fin, orden, requiere_ack.

#### Scenario: Create aviso
- **WHEN** the user fills the aviso form and submits
- **THEN** the system creates the aviso and shows it in the list

#### Scenario: Edit aviso
- **WHEN** the user edits an existing aviso and saves
- **THEN** the system updates the aviso and reflects changes in the list

#### Scenario: Delete aviso
- **WHEN** the user confirms deletion of an aviso
- **THEN** the system soft-deletes the aviso and removes it from the list

### Requirement: COORDINADOR/ADMIN can view acknowledgment stats
The system SHALL display derived acknowledgment metrics per aviso: total destinatarios, acknowledgments count, acknowledgment rate.

#### Scenario: View ack stats
- **WHEN** the user opens an aviso detail
- **THEN** the system shows acknowledgment statistics

### Requirement: Aviso form has scope configuration
The system SHALL allow configuring alcance with dynamic fields depending on scope type (materia selector for PorMateria, cohorte selector for PorCohorte, role selector for PorRol).

#### Scenario: Scope type changes available selectors
- **WHEN** the user changes alcance to "PorMateria"
- **THEN** the form shows a materia selector
- **WHEN** the user changes alcance to "PorCohorte"
- **THEN** the form shows a cohorte selector
- **WHEN** the user changes alcance to "PorRol"
- **THEN** the form shows a role selector
