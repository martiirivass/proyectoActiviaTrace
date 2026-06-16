## ADDED Requirements

### Requirement: HTTP client has auth request interceptor

The Axios instance SHALL have a request interceptor that attaches the current access token to every request as a `Bearer` token in the `Authorization` header.

#### Scenario: Access token exists
- **WHEN** a request is made
- **AND** an access token is available in memory
- **THEN** the interceptor adds header `Authorization: Bearer <access_token>`

#### Scenario: No access token
- **WHEN** a request is made
- **AND** no access token is available
- **THEN** the request is sent without an Authorization header

### Requirement: HTTP client has transparent refresh response interceptor

The Axios instance SHALL have a response interceptor that, on receiving a 401 response, attempts to refresh the access token transparently and retries the original request.

#### Scenario: Single 401 triggers refresh and retry
- **WHEN** any API call returns a 401 status
- **THEN** the interceptor attempts to refresh the token via `POST /api/v1/auth/refresh`
- **AND** if refresh succeeds, retries the original request with the new token
- **AND** the original caller receives the successful response as if nothing happened

#### Scenario: Multiple concurrent 401s trigger only one refresh
- **WHEN** multiple API calls return 401 simultaneously
- **THEN** only one refresh request is sent
- **AND** all other requests are queued
- **AND** when the refresh completes, all queued requests are retried with the new token

#### Scenario: Refresh failure logs out user
- **WHEN** the refresh request itself returns a 401 or fails
- **THEN** the interceptor clears all tokens from memory and localStorage
- **AND** all queued requests are rejected
- **AND** the user is redirected to `/login`

### Requirement: HTTP client handles 403 errors

The Axios instance SHALL handle 403 (Forbidden) responses and surface the permission error to the caller.

#### Scenario: 403 received
- **WHEN** a request returns a 403 status
- **THEN** the interceptor rejects the promise with the error
- **AND** the calling code can handle the "Sin permisos suficientes" scenario

### Requirement: HTTP client configuration

The Axios instance SHALL be configured with a base URL, default headers, timeout, and response type.

#### Scenario: Base URL is configurable
- **WHEN** the Axios instance is created
- **THEN** the base URL reads from environment variable `VITE_API_BASE_URL`
- **AND** defaults to `http://localhost:8000/api/v1` in development

#### Scenario: Default headers
- **WHEN** any request is made
- **THEN** the `Content-Type` header is set to `application/json`
- **AND** the `Accept` header is set to `application/json`

#### Scenario: Timeout
- **WHEN** a request exceeds the timeout limit (30 seconds)
- **THEN** the request is automatically cancelled

### Requirement: HTTP client exposes typed API helpers

The Axios instance SHALL export typed helper functions for common HTTP methods (get, post, put, patch, delete) that preserve TypeScript generics for request and response types.

#### Scenario: Typed POST request
- **WHEN** a feature service calls `api.post<LoginResponse>('/auth/login', body)`
- **THEN** the return type is `Promise<LoginResponse>`
- **AND** TypeScript validates the response shape

#### Scenario: Typed GET request
- **WHEN** a feature service calls `api.get<UserProfile>('/auth/me')`
- **THEN** the return type is `Promise<UserProfile>`
