## ADDED Requirements

### Requirement: Permission format modulo:accion
All permissions SHALL use the `modulo:accion` format (e.g., `alumnos:read`, `comunicaciones:send`).

#### Scenario: Permission name format
- **WHEN** a permission is created
- **THEN** its name SHALL follow the `modulo:accion` convention

### Requirement: Role aggregates permissions
A Role SHALL aggregate multiple permissions via a many-to-many relationship.

#### Scenario: Assign permissions to role
- **WHEN** permissions are assigned to a role
- **THEN** the role SHALL contain those permissions

### Requirement: Permission check
The system SHALL provide a `require_permission` mechanism that checks if a user has a specific permission for a given tenant.

#### Scenario: User has permission
- **WHEN** checking a permission the user's role includes
- **THEN** the check SHALL return True

#### Scenario: User lacks permission
- **WHEN** checking a permission the user's role does NOT include
- **THEN** the check SHALL return False (fail-closed)
