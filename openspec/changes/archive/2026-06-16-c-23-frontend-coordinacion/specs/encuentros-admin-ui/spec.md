## ADDED Requirements

### Requirement: COORDINADOR/ADMIN can view all encuentros (F6.5)
The system SHALL display a transversal table of all encuentros across the tenant regardless of creating docente, filterable by materia, docente, and fecha.

#### Scenario: Load encuentros admin view
- **WHEN** the user navigates to "Encuentros" in coordinacion
- **THEN** the system fetches all encuentros from the tenant

#### Scenario: Filter encuentros
- **WHEN** the user applies filters by materia, docente or date
- **THEN** the system updates the encuentros table
