## ADDED Requirements

### Requirement: User can view own tasks (F8.1)
The system SHALL display tasks assigned to the current user filtered by academic context.

#### Scenario: Load my tasks
- **WHEN** the user navigates to "Mis Tareas"
- **THEN** the system fetches and displays tasks assigned to the user

### Requirement: PROFESOR/COORDINADOR can delegate tasks (F8.2)
The system SHALL allow a user to delegate a task to another team member with traceability of asignador and asignado.

#### Scenario: Delegate task
- **WHEN** the user selects "Delegar" on a task and picks a target user
- **THEN** the system creates a new task assignment with the delegating user recorded as asignador

### Requirement: COORDINADOR/ADMIN can manage all tasks (F8.3)
The system SHALL provide a global task view for the tenant with filters by docente asignado, asignador, materia, estado and free text search.

#### Scenario: Filter global task list
- **WHEN** the user applies filters in the admin task view
- **THEN** the system updates the task list accordingly

#### Scenario: Change task status
- **WHEN** the user changes estado of a task
- **THEN** the system updates the task estado and records the change

### Requirement: User can add comments to tasks
The system SHALL allow adding comments to tasks as part of the async workflow.

#### Scenario: Add task comment
- **WHEN** the user writes a comment on a task and submits
- **THEN** the system appends the comment to the task thread
