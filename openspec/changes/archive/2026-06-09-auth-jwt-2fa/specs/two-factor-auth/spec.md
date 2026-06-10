## ADDED Requirements

### Requirement: User can enrol in 2FA TOTP
The system SHALL provide `POST /api/auth/2fa/enrol` (authenticated). On success, the system SHALL generate a TOTP secret using RFC 6238, store it encrypted (AES-256-GCM) on the user record, and return the secret and a `otpauth://` URI for QR code generation.

#### Scenario: Enrol in 2FA for the first time
- **WHEN** an authenticated user without 2FA configured calls `POST /api/auth/2fa/enrol`
- **THEN** system returns HTTP 200 with `secret` (base32), `uri` (otpauth://), and `qr_code` (base64 PNG)

#### Scenario: Enrol when 2FA is already active
- **WHEN** an authenticated user with 2FA already enabled calls `POST /api/auth/2fa/enrol`
- **THEN** system returns HTTP 409 with error detail "2FA already configured"

---

### Requirement: User can verify 2FA during login
The system SHALL provide `POST /api/auth/2fa/verify` accepting a `2fa_token` (from the login step) and a `totp_code`. If the TOTP code is valid for the user's secret, the system SHALL issue the access and refresh tokens (completing the login flow).

#### Scenario: Verify with valid TOTP code
- **WHEN** user submits valid `2fa_token` and correct `totp_code` via `POST /api/auth/2fa/verify`
- **THEN** system returns HTTP 200 with `access_token` (JWT), `refresh_token`, `token_type` ("bearer"), and `expires_in` (900)

#### Scenario: Verify with invalid TOTP code
- **WHEN** user submits valid `2fa_token` but incorrect `totp_code`
- **THEN** system returns HTTP 401 with error detail "Invalid verification code"

#### Scenario: Verify with expired 2fa_token
- **WHEN** user submits an expired `2fa_token` (older than 5 min)
- **THEN** system returns HTTP 401 with error detail "Verification session expired, please log in again"

---

### Requirement: User can disable 2FA
The system SHALL provide `POST /api/auth/2fa/disable` (authenticated, requires password confirmation). On success, the system SHALL remove the TOTP secret and mark 2FA as disabled.

#### Scenario: Disable 2FA with correct password
- **WHEN** an authenticated user with 2FA enabled submits their password via `POST /api/auth/2fa/disable`
- **THEN** system returns HTTP 200 and 2FA is disabled for that user

#### Scenario: Disable 2FA with incorrect password
- **WHEN** an authenticated user submits an incorrect password
- **THEN** system returns HTTP 401 with error detail "Invalid password"
