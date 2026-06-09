## ADDED Requirements

### Requirement: AES-256-GCM encryption for PII
The system SHALL provide an encryption service using AES-256-GCM via the `cryptography` library for PII fields (DNI, CBU).

#### Scenario: Encrypt field
- **WHEN** a plaintext string is encrypted
- **THEN** the result SHALL be a non-empty string different from the input

#### Scenario: Decrypt field
- **WHEN** an encrypted string is decrypted with the correct key
- **THEN** the result SHALL match the original plaintext

#### Scenario: Tampered ciphertext
- **WHEN** a tampered encrypted string is decrypted
- **THEN** the operation SHALL raise an authentication error

### Requirement: Soft delete pattern
All core models SHALL support soft delete with `is_deleted` boolean and `deleted_at` timestamp.

#### Scenario: Soft delete entity
- **WHEN** an entity is soft-deleted
- **THEN** `is_deleted` SHALL be True and `deleted_at` SHALL be set

#### Scenario: Soft-deleted entity excluded from queries
- **WHEN** querying entities
- **THEN** soft-deleted entities SHALL be excluded by default

#### Scenario: Include deleted entities
- **WHEN** querying with explicit `include_deleted()` opt-in
- **THEN** soft-deleted entities SHALL be included in results
