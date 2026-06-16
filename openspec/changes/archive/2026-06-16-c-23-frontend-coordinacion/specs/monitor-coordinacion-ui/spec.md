## ADDED Requirements

### Requirement: COORDINADOR/ADMIN can use monitor general (F2.7)
The system SHALL provide a transversal view of all alumnos in the tenant with their activity state, filterable by materia, regional, comision, free text search, estado de actividad and criterio de clasificacion.

#### Scenario: Load monitor general
- **WHEN** the user navigates to "Monitor General"
- **THEN** the system fetches all alumnos with activity state from the tenant

#### Scenario: Apply filters
- **WHEN** the user applies one or more filters
- **THEN** the system updates the results accordingly

#### Scenario: Export monitor data
- **WHEN** the user clicks "Exportar"
- **THEN** the system downloads the filtered dataset

#### Scenario: Clear filters
- **WHEN** the user clicks "Limpiar"
- **THEN** all filters reset and the unfiltered dataset is shown

### Requirement: COORDINADOR/ADMIN can use monitor con rango de fechas (F2.9)
The system SHALL extend the monitor view with a date range filter to narrow analysis period.

#### Scenario: Set date range filter
- **WHEN** the user selects a date range in the monitor
- **THEN** the system filters results to the selected period
