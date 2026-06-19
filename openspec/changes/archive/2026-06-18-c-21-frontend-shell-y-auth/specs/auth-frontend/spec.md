## ADDED Requirements

### Requirement: User can log in with email and password

The system SHALL provide a login form that collects email and password, sends them to `POST /api/v1/auth/login`, and on success establishes an authenticated session.

#### Scenario: Successful login without 2FA
- **WHEN** the user submits valid email and password
- **AND** the user does not have 2FA enabled
- **THEN** the system stores the access token in memory
- **AND** the system stores the refresh token in localStorage
- **AND** the system redirects to the main dashboard

#### Scenario: Login with 2FA required
- **WHEN** the user submits valid email and password
- **AND** the user has 2FA enabled
- **THEN** the system displays the 2FA verification screen
- **AND** the system stores the `two_fa_token` from the response

#### Scenario: Invalid credentials
- **WHEN** the user submits invalid email or password
- **THEN** the system displays an error message "Credenciales inválidas"
- **AND** the system does NOT redirect

#### Scenario: Rate-limited login
- **WHEN** the user exceeds the maximum login attempts
- **THEN** the system displays a rate limit error message with retry time

#### Scenario: Field validation on login form
- **WHEN** the user submits an empty email or password
- **THEN** the system displays validation errors on the respective fields
- **AND** the form is NOT submitted

### Requirement: User can verify 2FA with TOTP code

The system SHALL provide a 2FA verification form that collects a 6-digit TOTP code, sends it to `POST /api/v1/auth/2fa/verify`, and on success completes authentication.

#### Scenario: Valid TOTP code
- **WHEN** the user enters a valid TOTP code
- **THEN** the system stores the access token and refresh token
- **AND** the system redirects to the main dashboard

#### Scenario: Invalid TOTP code
- **WHEN** the user enters an invalid TOTP code
- **THEN** the system displays an error message "Código de verificación inválido"
- **AND** the system stays on the 2FA page

#### Scenario: Expired 2FA session
- **WHEN** the user attempts to verify an expired `two_fa_token`
- **THEN** the system displays "Sesión de verificación expirada, inicie sesión nuevamente"
- **AND** the system redirects to the login page

### Requirement: User can request password recovery

The system SHALL provide a form to request password recovery, sending the email to `POST /api/v1/auth/forgot`.

#### Scenario: Existing email
- **WHEN** the user submits an email registered in the system
- **THEN** the system displays a success message "Si el email está registrado, recibirás un enlace de recuperación"
- **AND** the system does NOT reveal whether the email exists or not (prevent enumeration)

#### Scenario: Empty email
- **WHEN** the user submits an empty email field
- **THEN** the system displays a validation error

### Requirement: User can reset password with recovery token

The system SHALL provide a form to set a new password using the token from the recovery email, sending to `POST /api/v1/auth/reset`.

#### Scenario: Valid reset token
- **WHEN** the user submits a valid reset token and a new password
- **AND** the password meets the minimum requirements (8+ characters)
- **THEN** the system displays "Contraseña restablecida exitosamente"
- **AND** the system redirects to the login page

#### Scenario: Invalid or expired reset token
- **WHEN** the user submits an invalid or expired reset token
- **THEN** the system displays "Token inválido o expirado"

#### Scenario: Weak password
- **WHEN** the user submits a password shorter than 8 characters
- **THEN** the system displays a validation error

### Requirement: User can log out

The system SHALL provide a logout action that sends `POST /api/v1/auth/logout` with the current refresh token, clears all local session data, and redirects to login.

#### Scenario: Successful logout
- **WHEN** the logged-in user clicks the logout button
- **THEN** the system sends the refresh token to `/logout`
- **AND** the system clears the access token from memory
- **AND** the system clears the refresh token from localStorage
- **AND** the system redirects to the login page

#### Scenario: Logout when offline (API unreachable)
- **WHEN** the logged-in user clicks logout
- **AND** the backend is unreachable
- **THEN** the system clears local session data anyway
- **AND** the system redirects to the login page
- **AND** the system does NOT block the user from logging out due to network error

### Requirement: AuthProvider manages session lifecycle

The system SHALL have an AuthProvider that manages authentication state globally, including silent refresh on mount.

#### Scenario: Silent refresh on mount with valid refresh token
- **WHEN** the application loads
- **AND** a refresh token exists in localStorage
- **THEN** the system attempts to refresh the access token via `POST /api/v1/auth/refresh`
- **AND** if successful, fetches user data via `GET /api/v1/auth/me`
- **AND** the system renders the authenticated app

#### Scenario: Silent refresh on mount with expired refresh token
- **WHEN** the application loads
- **AND** the stored refresh token is expired or invalid
- **THEN** the system clears all stored tokens
- **AND** the system redirects to the login page

#### Scenario: No stored refresh token on mount
- **WHEN** the application loads
- **AND** no refresh token exists in localStorage
- **THEN** the system renders the login page directly

### Requirement: Login page is accessible at /login

The system SHALL serve the login page at the `/login` route as a publicly accessible page.

#### Scenario: Navigate to /login
- **WHEN** an unauthenticated user navigates to `/login`
- **THEN** the system renders the login form

#### Scenario: Authenticated user visits /login
- **WHEN** an authenticated user navigates to `/login`
- **THEN** the system redirects to the main dashboard

### Requirement: 2FA page is accessible at /2fa

The system SHALL serve the 2FA verification page at the `/2fa` route.

#### Scenario: Navigate to /2fa with two_fa_token
- **WHEN** the user is redirected to `/2fa` after a login that requires 2FA
- **THEN** the system renders the TOTP code input
- **AND** the `two_fa_token` is available from navigation state

#### Scenario: Navigate to /2fa without two_fa_token
- **WHEN** an unauthenticated user navigates directly to `/2fa`
- **THEN** the system redirects to `/login`

### Requirement: Recovery page is accessible at /recuperar

The system SHALL serve the password recovery request form at the `/recuperar` route.

#### Scenario: Navigate to /recuperar
- **WHEN** a user navigates to `/recuperar`
- **THEN** the system renders the email input form

### Requirement: Reset password page is accessible at /restablecer

The system SHALL serve the password reset form at the `/restablecer` route, accepting the token from query parameters.

#### Scenario: Navigate to /restablecer with token
- **WHEN** a user navigates to `/restablecer?token=abc123`
- **THEN** the system renders the new password form
- **AND** the token is extracted from the URL query parameter

#### Scenario: Navigate to /restablecer without token
- **WHEN** a user navigates to `/restablecer` without a token query parameter
- **THEN** the system shows an error message "Token de recuperación no encontrado"
- **AND** the system provides a link to `/recuperar`
