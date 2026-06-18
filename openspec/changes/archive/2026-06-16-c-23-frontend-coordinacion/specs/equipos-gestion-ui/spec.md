## ADDED Requirements

### Requirement: COORDINADOR/ADMIN can view own teams (F4.2)
The system SHALL display the user's assigned comisiones and materias with role, carrera, cohorte, vigencia and estado.

#### Scenario: Load teams for current user
- **WHEN** the user navigates to "Mis Equipos"
- **THEN** the system fetches and displays all comisiones where the user is assigned

#### Scenario: Filter team list
- **WHEN** the user applies a filter by estado, materia, rol, carrera or cohorte
- **THEN** the system updates the table to show only matching entries

### Requirement: COORDINADOR/ADMIN can query all assignments (F4.3)
The system SHALL display all active assignments in the tenant with filters by materia, carrera, cohorte, usuario, role and report relation.

#### Scenario: Load global assignments
- **WHEN** the user navigates to "Asignaciones"
- **THEN** the system fetches all tenant assignments and renders them in a table with searchable filters

### Requirement: COORDINADOR/ADMIN can mass-assign teachers (F4.4)
The system SHALL allow selecting multiple docentes and assigning them to a materia × carrera × cohorte × rol combination with vigencia.

#### Scenario: Submit mass assignment
- **WHEN** the user selects docentes, a target (materia/carrera/cohorte), a role and vigencia dates
- **THEN** the system creates all assignments in a single operation

### Requirement: COORDINADOR/ADMIN can clone team between periods (F4.5)
The system SHALL duplicate all assignments from an origin equipo (materia × carrera × cohorte) to a new target cohorte.

#### Scenario: Clone equipo
- **WHEN** the user selects origin equipo and target cohorte
- **THEN** the system clones all assignments with dates of the new period

### Requirement: COORDINADOR/ADMIN can modify team vigencia (F4.6)
The system SHALL allow bulk updating the vigencia (desde/hasta) of all assignments in a selected equipo.

#### Scenario: Bulk update vigencia
- **WHEN** the user selects an equipo and sets new desde/hasta dates
- **THEN** the system updates vigencia on all assignments in that equipo

### Requirement: COORDINADOR/ADMIN can export equipo (F4.7)
The system SHALL provide a downloadable file with all equipo assignments detail.

#### Scenario: Export assignments
- **WHEN** the user clicks "Exportar" on an equipo view
- **THEN** the system downloads a file (CSV/XLSX) with all assignment details
