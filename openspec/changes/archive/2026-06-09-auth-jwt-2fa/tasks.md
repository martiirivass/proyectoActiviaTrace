## 1. JWT and Token Infrastructure

- [x] 1.1 Add `python-jose[cryptography]`, `pyotp`, `qrcode[pil]` to pyproject.toml dependencies
- [x] 1.2 Add JWT settings to core/config.py (SECRET_KEY, JWT_ALGORITHM=HS256, ACCESS_TOKEN_EXPIRE_MINUTES=15, REFRESH_TOKEN_EXPIRE_DAYS=30, 2FA_TOKEN_EXPIRE_MINUTES=5)
- [x] 1.3 Implement JWT utility functions in core/security.py: `create_access_token()`, `create_refresh_token()`, `create_2fa_token()`, `verify_token()`, `decode_token()`
- [x] 1.4 Implement rate limiter class in core/rate_limiter.py: sliding window counter per IP+email, configurable max_attempts and window_seconds

## 2. Data Models and Migrations

- [x] 2.1 Create model `RefreshToken` in app/models/refresh_token.py (id UUID, user_id FK, token_hash SHA-256, expires_at, revoked_at nullable, created_at)
- [x] 2.2 Create model `RecoveryToken` in app/models/recovery_token.py (id UUID, user_id FK, token_hash SHA-256, expires_at, used_at nullable, created_at)
- [x] 2.3 Add `totp_secret` column (encrypted text, nullable) and `is_2fa_enabled` (boolean, default false) to User model
- [x] 2.4 Create Alembic migration adding refresh_tokens, recovery_tokens tables and User columns

## 3. Auth Service

- [x] 3.1 Implement `AuthService.authenticate(email, password)` — verify credentials, check soft-delete, resolve tenant
- [x] 3.2 Implement `AuthService.create_session(user)` — generate access + refresh tokens, store refresh hash
- [x] 3.3 Implement `AuthService.refresh_session(refresh_token)` — verify, rotate, revoke old, detect reuse (revoke ALL if reuse detected)
- [x] 3.4 Implement `AuthService.revoke_session(refresh_token)` — logout, mark revoked
- [x] 3.5 Implement `AuthService.enrol_2fa(user)` — generate TOTP secret, encrypt and store, return URI+QR
- [x] 3.6 Implement `AuthService.verify_2fa(user_id, totp_code)` — validate TOTP against stored secret
- [x] 3.7 Implement `AuthService.disable_2fa(user, password)` — verify password, remove secret, disable flag
- [x] 3.8 Implement `AuthService.create_recovery_token(email)` — generate single-use token, store hash
- [x] 3.9 Implement `AuthService.reset_password(token, new_password)` — verify token single-use, update password, mark token used

## 4. FastAPI Dependencies

- [x] 4.1 Implement `get_current_user` dependency in core/dependencies.py — extract Bearer token, verify JWT, resolve User from DB, reject if soft-deleted
- [x] 4.2 Implement `get_tenant` dependency — extract tenant_id from current_user, return Tenant object
- [x] 4.3 Implement `get_rate_limiter` dependency — singleton instance of RateLimiter

## 5. Auth Router

- [x] 5.1 Create router `api/v1/routers/auth.py` with `POST /api/auth/login` (with rate limiting, returns requires_2fa if 2FA enabled)
- [x] 5.2 Add `POST /api/auth/refresh` endpoint
- [x] 5.3 Add `POST /api/auth/logout` endpoint (authenticated)
- [x] 5.4 Add `POST /api/auth/2fa/enrol` endpoint (authenticated)
- [x] 5.5 Add `POST /api/auth/2fa/verify` endpoint (with 2fa_token)
- [x] 5.6 Add `POST /api/auth/2fa/disable` endpoint (authenticated, requires password)
- [x] 5.7 Add `POST /api/auth/forgot` endpoint (email, generates token)
- [x] 5.8 Add `POST /api/auth/reset` endpoint (token + new password)
- [x] 5.9 Register auth router in app's main.py with /api/v1 prefix

## 6. Tests

- [x] 6.1 Test login flow: success, invalid password, non-existent email, soft-deleted user, 2FA gate
- [x] 6.2 Test refresh rotation: success, reuse detection revokes all, expired token
- [x] 6.3 Test logout: revokes refresh token
- [x] 6.4 Test 2FA: enrol, verify during login, disable with password, invalid code
- [x] 6.5 Test forgot/reset: generate token, reset password, reuse token fails, expired token
- [x] 6.6 Test rate limiting: under limit passes, over limit returns 429, reset after window
- [x] 6.7 Test get_current_user: valid token, expired, invalid signature, soft-deleted user, missing header
- [x] 6.8 Full integration: login → 2FA verify → access protected endpoint → refresh → logout → refresh fails
