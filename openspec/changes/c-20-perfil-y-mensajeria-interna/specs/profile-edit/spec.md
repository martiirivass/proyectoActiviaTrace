## ADDED Requirements

### Requirement: Authenticated user can read own profile

The system SHALL provide an endpoint `GET /api/v1/perfil` that returns the authenticated user's profile data, accessible by any user with a valid JWT (no special permission required).

The response SHALL include: `id`, `tenant_id`, `email`, `legajo`, `nombre`, `apellido`, `dni`, `cuil`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo_profesional`, `facturador`, `estado`, `sexo`, `is_2fa_enabled`, `is_deleted`, `created_at`, `updated_at`.

The response SHALL NOT expose: `password_hash`, `totp_secret`.

The schema `PerfilResponse` SHALL use `from_attributes=True` and `extra='forbid'`.

#### Scenario: successful profile read

- **WHEN** an authenticated user sends `GET /api/v1/perfil`
- **THEN** the system returns 200 with the user's profile data including `sexo`

#### Scenario: profile read without auth

- **WHEN** an unauthenticated request sends `GET /api/v1/perfil`
- **THEN** the system returns 401

### Requirement: Authenticated user can update own editable fields

The system SHALL provide an endpoint `PUT /api/v1/perfil` that allows the authenticated user to update their own editable profile fields.

Editable fields: `nombre`, `apellido`, `dni`, `sexo`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo_profesional`, `facturador`, `email`.

Non-editable fields (MUST be rejected): `cuil`, `legajo`.

The schema `PerfilUpdate` SHALL use `extra='forbid'` and SHALL include all editable fields as optional.

#### Scenario: successful profile update

- **WHEN** an authenticated user sends `PUT /api/v1/perfil` with valid editable fields
- **THEN** the system updates the profile and returns 200 with the updated `PerfilResponse`

#### Scenario: reject cuil modification

- **WHEN** an authenticated user sends `PUT /api/v1/perfil` with `cuil` in the body
- **THEN** the system returns 422 with an error message indicating CUIL is not modifiable

#### Scenario: reject legajo modification

- **WHEN** an authenticated user sends `PUT /api/v1/perfil` with `legajo` in the body
- **THEN** the system returns 422 with an error message indicating legajo is not modifiable

#### Scenario: reject email already in use

- **WHEN** an authenticated user sends `PUT /api/v1/perfil` with an email already registered by another user in the same tenant
- **THEN** the system returns 409 with an error message indicating the email is already in use

#### Scenario: partial update only modifies specified fields

- **WHEN** an authenticated user sends `PUT /api/v1/perfil` with only `nombre` and `apellido`
- **THEN** the system updates only those fields and returns 200 with the updated profile (other fields unchanged)

#### Scenario: update without auth returns 401

- **WHEN** an unauthenticated request sends `PUT /api/v1/perfil`
- **THEN** the system returns 401
