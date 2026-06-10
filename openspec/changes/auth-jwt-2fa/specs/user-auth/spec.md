## ADDED Requirements

### Requirement: User can log in with email and password
The system SHALL authenticate users via `POST /api/auth/login` accepting `email` and `password`. The password SHALL be verified against the stored Argon2id hash. On success, the system SHALL return an access token (JWT, 15 min expiry) and a refresh token. The JWT SHALL contain claims: `sub` (user UUID), `tenant_id`, `roles` (list of role names), `type` ("access"), and `exp`. The refresh token SHALL be a random string, hashed (SHA-256) before storage in the `refresh_tokens` table.

#### Scenario: Successful login
- **WHEN** user submits valid email and password via `POST /api/auth/login`
- **THEN** system returns HTTP 200 with `access_token` (JWT), `refresh_token` (opaque), `token_type` ("bearer"), and `expires_in` (900)

#### Scenario: Login with invalid password
- **WHEN** user submits valid email but incorrect password
- **THEN** system returns HTTP 401 with error detail "Invalid email or password"

#### Scenario: Login with non-existent email
- **WHEN** user submits an email that does not exist in the tenant
- **THEN** system returns HTTP 401 with error detail "Invalid email or password" (mismo mensaje para no revelar qué emails existen)

#### Scenario: Login for soft-deleted user
- **WHEN** a soft-deleted user attempts to log in
- **THEN** system returns HTTP 401 with error detail "Invalid email or password"

#### Scenario: Login when 2FA is enabled
- **WHEN** user submits valid credentials and has 2FA TOTP enabled
- **THEN** system returns HTTP 200 with `requires_2fa: true` and a `2fa_token` (short-lived JWT, 5 min) — NO access/refresh tokens yet

---

### Requirement: User can refresh their session
The system SHALL accept `POST /api/auth/refresh` with a valid refresh token in the request body. On success, the system SHALL:
1. Verify the refresh token exists in DB, is not revoked, and is not expired
2. Mark the used refresh token as revoked (`revoked_at = now()`)
3. Issue a new access token and a new refresh token (rotation)
4. Store the new refresh token hash in DB

#### Scenario: Successful refresh with rotation
- **WHEN** user submits a valid, non-expired, non-revoked refresh token via `POST /api/auth/refresh`
- **THEN** system returns HTTP 200 with new `access_token` and `refresh_token`; the old refresh token is marked as revoked

#### Scenario: Refresh with already-revoked token (reuse detection)
- **WHEN** user submits a refresh token that was already revoked
- **THEN** system returns HTTP 401 and revokes ALL refresh tokens for that user (session hijacking detected)

#### Scenario: Refresh with expired token
- **WHEN** user submits an expired refresh token
- **THEN** system returns HTTP 401 with error detail "Refresh token expired"

---

### Requirement: User can log out
The system SHALL accept `POST /api/auth/logout` with a valid refresh token. The system SHALL revoke the refresh token.

#### Scenario: Successful logout
- **WHEN** user submits a valid refresh token via `POST /api/auth/logout`
- **THEN** system returns HTTP 204 and marks the refresh token as revoked

---

### Requirement: System resolves identity from JWT via dependency
The system SHALL provide a FastAPI dependency `get_current_user` that:
1. Extracts the Bearer token from the `Authorization` header
2. Verifies the JWT signature and expiry
3. Extracts `sub`, `tenant_id`, `roles` from claims
4. Resolves the full User object from DB (to confirm user still exists and is not soft-deleted)
5. Returns a `CurrentUser` object with `id`, `email`, `tenant_id`, `roles`

#### Scenario: Valid JWT in Authorization header
- **WHEN** a request includes a valid `Authorization: Bearer <jwt>` header
- **THEN** `get_current_user` returns the `CurrentUser` object with user's id, email, tenant_id and roles

#### Scenario: Expired JWT
- **WHEN** a request includes an expired JWT
- **THEN** `get_current_user` raises HTTP 401 with error detail "Token expired"

#### Scenario: Invalid JWT signature
- **WHEN** a request includes a JWT with invalid signature
- **THEN** `get_current_user` raises HTTP 401 with error detail "Invalid token"

#### Scenario: User was soft-deleted after token issuance
- **WHEN** the JWT is valid but the user has been soft-deleted in DB
- **THEN** `get_current_user` raises HTTP 401 with error detail "User inactive or deleted"

#### Scenario: Missing Authorization header
- **WHEN** a request has no `Authorization` header
- **THEN** `get_current_user` raises HTTP 401 with error detail "Not authenticated"
