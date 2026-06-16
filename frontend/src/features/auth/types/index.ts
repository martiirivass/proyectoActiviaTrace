// ── Auth API request types ─────────────────────────────────────────────
export interface LoginRequest {
  email: string
  password: string
}

export interface TwoFAVerifyRequest {
  two_fa_token: string
  code: string
}

export interface RefreshRequest {
  refresh_token: string
}

export interface ForgotRequest {
  email: string
}

export interface ResetRequest {
  token: string
  password: string
}

// ── Auth API response types ────────────────────────────────────────────
export interface AuthTokens {
  access_token: string
  refresh_token: string
  requires_2fa?: boolean
  two_fa_token?: string
}

export type LoginResponse = AuthTokens
export type TwoFAVerifyResponse = AuthTokens
export interface RefreshResponse {
  access_token: string
  refresh_token: string
}

// ── User profile ───────────────────────────────────────────────────────
export interface UserProfile {
  id: string
  email: string
  nombre: string
  apellido: string
  roles: string[]
  permisos: string[]
}

// ── API error response ─────────────────────────────────────────────────
export interface ApiError {
  detail: string
  status_code?: number
}
