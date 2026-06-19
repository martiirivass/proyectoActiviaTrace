# Coordinator Audit Scope

## ADDED Requirements

### Requirement: COORDINADOR role has auditoria:ver with scope propio

The system SHALL assign the permission `auditoria:ver` to the COORDINADOR role with scope `propio` via a new Alembic migration. This means COORDINADOR can only see audit data for materias where they have active asignaciones.

#### Scenario: Coordinator sees own materia audit data
- **WHEN** a COORDINADOR user is assigned to materias A and B
- **THEN** they SHALL see audit data for materias A and B when querying audit endpoints

#### Scenario: Coordinator does not see unrelated materias
- **WHEN** a COORDINADOR user queries audit data for materia C (not assigned)
- **THEN** the response SHALL NOT include data from materia C

#### Scenario: Coordinator scope does not affect ADMIN or FINANZAS
- **WHEN** an ADMIN or FINANZAS user queries audit data
- **THEN** they SHALL see ALL materias (global scope), unaffected by the coordinator scope

### Requirement: Migration adds coordinator-auditoria:ver seed

A new Alembic migration SHALL insert the `role_permissions` row that grants `auditoria:ver` to COORDINADOR with scope `propio`, without duplicating existing seed data.

#### Scenario: Migration is idempotent
- **WHEN** the migration runs on a tenant where COORDINADOR already has `auditoria:ver`
- **THEN** the migration SHALL NOT create a duplicate role_permissions row

#### Scenario: Migration does not affect other roles
- **WHEN** the migration runs
- **THEN** no other role's permissions SHALL be modified

### Requirement: Scope resolution is done at the service layer

The audit service SHALL resolve scope `propio` by querying the Asignacion repository to obtain the list of materia_ids assigned to the current user, and passing them as a filter to the audit repository.

#### Scenario: Resolving scope propio
- **WHEN** a user with scope `propio` makes an audit request
- **THEN** the service SHALL call AsignacionRepository to get the user's materias, then filter audit data by those materia_ids

#### Scenario: Resolving scope global
- **WHEN** a user with scope `global` makes an audit request
- **THEN** the service SHALL NOT add any materia_id filter from scope
