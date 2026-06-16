## ADDED Requirements

### Requirement: COORDINADOR can run setup de cuatrimestre wizard (FL-03)
The system SHALL provide a multi-step wizard for the full FL-03 flow: crear cohorte, clonar equipo, ajustar asignaciones, modificar vigencia, cargar programas, cargar fechas, publicar aviso.

#### Scenario: Wizard step navigation
- **WHEN** the user completes a step and clicks "Siguiente"
- **THEN** the wizard advances to the next step while preserving previous state
- **WHEN** the user clicks "Anterior"
- **THEN** the wizard returns to the previous step with data preserved

#### Scenario: Wizard completes full flow
- **WHEN** the user completes all wizard steps and clicks "Finalizar"
- **THEN** the system applies all changes and shows a success summary

### Requirement: Wizard step 1 — Crear nueva cohorte
The system SHALL allow defining cohorte identifier, name, vigencia dates.

#### Scenario: Create cohorte within wizard
- **WHEN** the user enters cohorte data and confirms
- **THEN** the system creates the cohorte and stores it for the flow

### Requirement: Wizard step 2 — Clonar equipo docente
The system SHALL let the user select origin equipo and target cohorte to clone assignments.

#### Scenario: Clone within wizard
- **WHEN** the user selects origin and target
- **THEN** the system clones the equipo assignments

### Requirement: Wizard step 3 — Ajustar asignaciones
The system SHALL let the user complete missing assignments via the mass assignment interface.

### Requirement: Wizard step 4 — Cargar programas
The system SHALL allow uploading program documents per materia × cohorte.

### Requirement: Wizard step 5 — Cargar fechas
The system SHALL allow registering evaluation dates for the new period.

### Requirement: Wizard step 6 — Publicar aviso de bienvenida
The system SHALL allow creating and publishing a welcome aviso scoped to the new cohorte.
