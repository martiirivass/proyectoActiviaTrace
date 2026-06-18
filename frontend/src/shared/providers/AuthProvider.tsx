import {
  createContext,
  useCallback,
  useMemo,
  useState,
  useEffect,
  type ReactNode,
} from 'react'
import {
  setAccessToken,
  getAccessToken,
  getStoredRefreshToken,
  setStoredRefreshToken,
  clearTokens,
} from '@/shared/api/api'
import { authApi } from '@/features/auth/services/authApi'
import type { UserProfile, AuthTokens } from '@/features/auth/services/authApi'

// ── Context type ───────────────────────────────────────────────────────
export interface AuthContextType {
  user: UserProfile | null
  isAuthenticated: boolean
  isLoading: boolean
  permissions: string[]
  login: (tokens: AuthTokens) => Promise<void>
  logout: () => Promise<void>
  getAccessToken: () => string | null
}

// ── Context ────────────────────────────────────────────────────────────
export const AuthContext = createContext<AuthContextType | undefined>(undefined)

// ── Provider ──────────────────────────────────────────────────────────
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const permissions = useMemo(() => user?.permisos ?? [], [user])

  const setSession = useCallback(async (tokens: AuthTokens) => {
    setAccessToken(tokens.access_token)
    if (tokens.refresh_token) {
      setStoredRefreshToken(tokens.refresh_token)
    }
    try {
      const profile = await authApi.me()
      setUser(profile)
    } catch {
      // If /me fails, we still have the session but no profile
      setUser(null)
    }
  }, [])

  const login = useCallback(
    async (tokens: AuthTokens) => {
      await setSession(tokens)
      window.location.href = '/'
    },
    [setSession],
  )

  const logout = useCallback(async () => {
    try {
      const refreshToken = getStoredRefreshToken()
      if (refreshToken) {
        await authApi.logout(refreshToken)
      }
    } catch {
      // If logout API fails (offline), still clear local session
    } finally {
      clearTokens()
      setUser(null)
      window.location.href = '/login'
    }
  }, [])

  // Load session on mount
  useEffect(() => {
    const loadSession = async () => {
      const storedRefresh = getStoredRefreshToken()
      if (!storedRefresh) {
        setIsLoading(false)
        return
      }

      try {
        const response = await authApi.refresh(storedRefresh)
        setAccessToken(response.access_token)
        if (response.refresh_token) {
          setStoredRefreshToken(response.refresh_token)
        }
        const profile = await authApi.me()
        setUser(profile)
      } catch {
        clearTokens()
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    loadSession()
  }, [])

  const value = useMemo<AuthContextType>(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      permissions,
      login,
      logout,
      getAccessToken,
    }),
    [user, isLoading, permissions, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
