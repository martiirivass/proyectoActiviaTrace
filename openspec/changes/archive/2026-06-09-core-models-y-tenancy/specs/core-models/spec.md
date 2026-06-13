## ADDED Requirements

### Requirement: User model with UUID identity
The system SHALL provide a User model with UUID primary key, unique email, unique legajo, full name, Argon2id password hash, and timestamps (created_at, updated_at, deleted_at).

#### Scenario: Create user with valid data
- **WHEN** a User is created with valid email, legajo, name and password
- **THEN** the user SHALL have a UUID id, hashed password, and auto-set timestamps

#### Scenario: User email uniqueness
- **WHEN** two users are created with the same email
- **THEN** the second creation SHALL raise an integrity error

#### Scenario: User soft delete
- **WHEN** a user is deleted via soft delete
- **THEN** `is_deleted` SHALL be True and `deleted_at` SHALL be set

### Requirement: Tenant model
The system SHALL provide a Tenant model with UUID primary key, unique name, code, and active status.

#### Scenario: Create tenant
- **WHEN** a Tenant is created with valid name and code
- **THEN** the tenant SHALL exist with an active status by default

#### Scenario: Tenant code uniqueness
- **WHEN** two tenants are created with the same code
- **THEN** the second creation SHALL raise an integrity error

### Requirement: Role model
The system SHALL provide a Role model with UUID primary key, unique name per tenant, and description.

#### Scenario: Create role for tenant
- **WHEN** a Role is created with a name and tenant_id
- **THEN** the role SHALL be associated with that tenant

#### Scenario: Role name unique per tenant
- **WHEN** two roles with the same name are created under the same tenant
- **THEN** the second creation SHALL raise an integrity error

### Requirement: Permission model
The system SHALL provide a Permission model with UUID primary key and unique name in `modulo:accion` format.

#### Scenario: Create permission
- **WHEN** a Permission is created with name `alumnos:read`
- **THEN** the permission SHALL be stored with that exact name

#### Scenario: Permission name uniqueness
- **WHEN** two permissions with the same name are created
- **THEN** the second creation SHALL raise an integrity error

### Requirement: UserRole association
The system SHALL provide a UserRole model linking User, Tenant, and Role with timestamps.

#### Scenario: Assign role to user in tenant
- **WHEN** a UserRole is created with user, tenant, and role
- **THEN** the association SHALL be stored with created_at timestamp

### Requirement: UserTenant association
The system SHALL provide a UserTenant model linking User and Tenant with active status and timestamps.

#### Scenario: Associate user with tenant
- **WHEN** a UserTenant is created with user and tenant
- **THEN** the user SHALL be associated with that tenant as active by default
