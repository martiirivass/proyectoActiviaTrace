## ADDED Requirements

### Requirement: COORDINADOR/ADMIN can view coloquio metrics panel (F7.1)
The system SHALL display aggregate metrics: total alumnos cargados, instancias activas, reservas activas, notas registradas.

#### Scenario: Load metrics
- **WHEN** the user navigates to "Coloquios"
- **THEN** the system shows the metrics panel with current data

### Requirement: COORDINADOR/ADMIN can create convocatoria (F7.3)
The system SHALL allow creating a new coloquio convocatoria with materia, instancia, days and cupos.

#### Scenario: Create convocatoria
- **WHEN** the user fills the convocatoria form and submits
- **THEN** the system creates the convocatoria and shows it in the list

### Requirement: COORDINADOR/ADMIN can view convocatorias list (F7.4)
The system SHALL display a table of all convocatorias with metrics: materia, instancia, days, convocados, reservas activas, cupos libres.

#### Scenario: Load convocatorias list
- **WHEN** the user navigates to the convocatorias tab
- **THEN** the system fetches and displays all convocatorias with their metrics

### Requirement: ADMIN can manage coloquios globally (F7.5)
The system SHALL provide admin with convocatoria CRUD, consolidated academic results view, and active reservations agenda.

#### Scenario: Admin edits convocatoria
- **WHEN** the ADMIN edits an existing convocatoria
- **THEN** the system applies the changes and refreshes the list

#### Scenario: Admin views results
- **WHEN** the ADMIN navigates to "Resultados"
- **THEN** the system shows consolidated resultados per convocatoria
