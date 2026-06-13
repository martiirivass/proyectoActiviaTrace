# security-encryption Specification

## Purpose
TBD - created by archiving change core-models-y-tenancy. Update Purpose after archive.
## Requirements
### Requirement: AES-256-GCM encryption for PII fields at rest
The system SHALL encrypt sensitive PII fields (email, dni, cuil, cbu, alias_cbu) using AES-256-GCM before persisting to database:
- Algorithm: AES-256-GCM (authenticated encryption)
- Key: 32 bytes derived from `ENCRYPTION_KEY` env var (base64-encoded)
- Nonce: 12 bytes, randomly generated per encryption operation
- Ciphertext format: base64(nonce || ciphertext || auth_tag)
- Integrity: auth_tag validated on decrypt; tampering raises `InvalidTag`

#### Scenario: Encrypt + decrypt round-trip preserves plaintext
- **WHEN** `encrypt_field("dato sensible")` then `decrypt_field(ciphertext)`
- **THEN** result equals "dato sensible"

#### Scenario: Same plaintext produces different ciphertexts each time
- **WHEN** `encrypt_field("dato")` called twice
- **THEN** ciphertexts differ (unique nonce per operation)

#### Scenario: Decrypt with wrong key fails authentication
- **WHEN** `decrypt_field(ciphertext, wrong_key)`
- **THEN** raises `cryptography.exceptions.InvalidTag`

#### Scenario: Tampered ciphertext fails authentication
- **WHEN** ciphertext modified then `decrypt_field`
- **THEN** raises `InvalidTag` (auth_tag validation fails)

#### Scenario: Empty string encrypts/decrypts correctly
- **WHEN** `encrypt_field("")` then `decrypt_field`
- **THEN** returns ""

#### Scenario: Unicode strings encrypt/decrypt correctly
- **WHEN** `encrypt_field("ñoño 🎓")` then `decrypt_field`
- **THEN** returns "ñoño 🎓"

### Requirement: EncryptedString SQLAlchemy TypeDecorator for transparent column encryption
The system SHALL provide `EncryptedString` TypeDecorator that automatically encrypts on write and decrypts on read:
- `process_bind_param`: encrypts plaintext before INSERT/UPDATE
- `process_result_value`: decrypts ciphertext after SELECT
- `impl`: Text (stores base64 ciphertext)
- Column definition: `Column(EncryptedString, nullable=True)`

#### Scenario: Model with EncryptedString column stores ciphertext in DB
- **WHEN** User(email="user@test.com") is saved
- **THEN** database row shows base64 ciphertext in email column

#### Scenario: Loading model returns decrypted plaintext
- **WHEN** User is loaded from database
- **THEN** user.email == "user@test.com" (plaintext)

#### Scenario: Encrypted values never appear in logs or repr
- **WHEN** model with EncryptedString is logged or repr'd
- **THEN** shows masked value (e.g., `<encrypted>`) not plaintext or ciphertext

### Requirement: Argon2id password hashing
The system SHALL hash passwords using Argon2id (memory-hard, GPU-resistant):
- Library: `argon2-cffi` with `PasswordHasher`
- Default params: time_cost=3, memory_cost=65536, parallelism=4
- `hash_password(plaintext) -> str` returns encoded hash (includes params + salt)
- `verify_password(hash, plaintext) -> bool` validates

#### Scenario: Password hash is Argon2id format
- **WHEN** `hash_password("secret123")`
- **THEN** result starts with `$argon2id$v=19$m=65536,t=3,p=4$`

#### Scenario: Verify correct password returns True
- **WHEN** `verify_password(hash, "secret123")`
- **THEN** True

#### Scenario: Verify incorrect password returns False
- **WHEN** `verify_password(hash, "wrong")`
- **THEN** False (no exception)

#### Scenario: Hash differs each time for same password
- **WHEN** `hash_password("secret")` called twice
- **THEN** two different hashes (unique salt per hash)

#### Scenario: Empty password handled correctly
- **WHEN** `hash_password("")` then `verify_password(hash, "")`
- **THEN** True

### Requirement: Encryption key from environment with validation
The system SHALL derive encryption key from `ENCRYPTION_KEY` environment variable:
- Format: base64-encoded 32 bytes (256 bits)
- Validation at startup: missing or wrong length → ConfigurationError before accepting requests

#### Scenario: Missing ENCRYPTION_KEY fails at startup
- **WHEN** app starts without ENCRYPTION_KEY
- **THEN** ConfigurationError raised during Settings initialization

#### Scenario: Invalid ENCRYPTION_KEY length fails at startup
- **WHEN** ENCRYPTION_KEY decodes to != 32 bytes
- **THEN** ConfigurationError raised

