# aes256-field-encryption Specification

## Purpose
TBD - created by archiving change core-models-y-tenancy. Update Purpose after archive.
## Requirements
### Requirement: AES-256-GCM field encryption for PII attributes
The system SHALL provide encryption utilities for fields marked `[cifrado]` in the data model (DNI, CUIL, CBU, email, alias_cbu):
- `encrypt_field(plaintext: str, key: bytes) -> str`: Returns base64(nonce + ciphertext + auth_tag)
- `decrypt_field(ciphertext_b64: str, key: bytes) -> str`: Returns original plaintext, validates auth tag
- `EncryptedString` SQLAlchemy TypeDecorator for transparent column encryption

#### Scenario: Encrypt then decrypt returns original value
- **WHEN** plaintext is encrypted with encrypt_field then decrypted with decrypt_field using same key
- **THEN** result equals original plaintext

#### Scenario: Different keys produce different ciphertexts
- **WHEN** same plaintext encrypted with two different keys
- **THEN** ciphertexts are different (nonce ensures uniqueness)

#### Scenario: Decrypt with wrong key raises error
- **WHEN** decrypt_field called with key different from encryption key
- **THEN** raises InvalidTag (authentication tag validation fails)

#### Scenario: EncryptedString column encrypts on write and decrypts on read
- **WHEN** model with Column(EncryptedString) is saved with plaintext value
- **THEN** database stores base64 ciphertext; loading model returns decrypted plaintext

#### Scenario: Encrypted values never appear in logs
- **WHEN** model with EncryptedString is logged (e.g., via __repr__ or debug logging)
- **THEN** the encrypted value is not logged in plaintext; only masked representation shown

### Requirement: Encryption key derived from environment variable
The system SHALL derive the AES-256 key from `ENCRYPTION_KEY` environment variable (32 bytes, base64-encoded).

#### Scenario: Missing ENCRYPTION_KEY raises configuration error at startup
- **WHEN** application starts without ENCRYPTION_KEY set
- **THEN** raises ConfigurationError before accepting requests

#### Scenario: Invalid ENCRYPTION_KEY length raises error
- **WHEN** ENCRYPTION_KEY decodes to != 32 bytes
- **THEN** raises ConfigurationError

### Requirement: PBKDF2 key derivation for additional security
The system SHALL support `derive_key(password: str, salt: bytes) -> bytes` using PBKDF2-HMAC-SHA256 with 100,000 iterations for scenarios requiring password-based keys.

#### Scenario: Derive key produces deterministic output for same inputs
- **WHEN** derive_key called twice with same password and salt
- **THEN** returns identical 32-byte keys

#### Scenario: Different salts produce different keys
- **WHEN** derive_key called with same password but different salts
- **THEN** returns different keys

