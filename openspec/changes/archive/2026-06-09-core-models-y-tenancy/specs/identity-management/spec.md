## ADDED Requirements

### Requirement: UUID primary keys
All core models SHALL use UUID as primary key, generated via `uuid4()` by default.

#### Scenario: Auto-generate UUID
- **WHEN** a new entity is created
- **THEN** its id SHALL be a UUID

#### Scenario: UUID uniqueness
- **WHEN** multiple entities are created
- **THEN** each SHALL have a unique UUID

### Requirement: Argon2id password hashing
The system SHALL hash passwords using Argon2id via `argon2-cffi` with secure defaults.

#### Scenario: Hash password
- **WHEN** a password is hashed
- **THEN** the hash SHALL be a non-empty string starting with `$argon2id$`

#### Scenario: Verify correct password
- **WHEN** verifying a password against its hash
- **THEN** a correct password SHALL return True

#### Scenario: Reject incorrect password
- **WHEN** verifying an incorrect password against its hash
- **THEN** the verification SHALL return False

### Requirement: Legajo as business attribute
The User model SHALL have a `legajo` field that is unique and indexed, used as a business identifier only (not as a credential).

#### Scenario: Legajo uniqueness
- **WHEN** two users are created with the same legajo
- **THEN** the second creation SHALL raise an integrity error
