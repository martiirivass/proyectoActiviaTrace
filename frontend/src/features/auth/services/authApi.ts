import { post, get } from '@/shared/api/api'
import type {
  LoginRequest,
  LoginResponse,
  TwoFAVerifyRequest,
  TwoFAVerifyResponse,
  RefreshRequest,
  RefreshResponse,
  ForgotRequest,
  ResetRequest,
  UserProfile,
  AuthTokens,
} from '@/features/auth/types'

export type { UserProfile, AuthTokens }

export const authApi = {
  login: (data: LoginRequest): Promise<LoginResponse> =>
    post<LoginResponse>('/auth/login', data),

  verify2fa: (data: TwoFAVerifyRequest): Promise<TwoFAVerifyResponse> =>
    post<TwoFAVerifyResponse>('/auth/2fa/verify', data),

  refresh: (refreshToken: string): Promise<RefreshResponse> =>
    post<RefreshResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    } satisfies RefreshRequest),

  logout: (refreshToken: string): Promise<void> =>
    post<void>('/auth/logout', {
      refresh_token: refreshToken,
    } satisfies RefreshRequest),

  forgot: (data: ForgotRequest): Promise<void> =>
    post<void>('/auth/forgot', data),

  reset: (data: ResetRequest): Promise<void> =>
    post<void>('/auth/reset', data),

  me: (): Promise<UserProfile> => get<UserProfile>('/auth/me'),
}
