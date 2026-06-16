import { type ReactElement } from 'react'
import { render, type RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, type MemoryRouterProps } from 'react-router-dom'
import { AuthContext, type AuthContextType } from '@/shared/providers/AuthProvider'
import type { UserProfile } from '@/features/auth/types'

// ── Mock user for authenticated tests ───────────────────────────────────
export const mockUser: UserProfile = {
  id: 'user-1',
  email: 'test@example.com',
  nombre: 'Test',
  apellido: 'User',
  roles: ['ADMIN'],
  permisos: ['admin:all', 'academica:read', 'usuarios:read'],
}

// ── Default auth context value for testing ──────────────────────────────
function createMockAuthContext(
  overrides: Partial<AuthContextType> = {},
): AuthContextType {
  return {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    permissions: [],
    login: async () => {},
    logout: async () => {},
    getAccessToken: () => null,
    ...overrides,
  }
}

// ── Custom render options ───────────────────────────────────────────────
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  authContext?: Partial<AuthContextType>
  initialEntries?: MemoryRouterProps['initialEntries']
}

// ── renderWithProviders ─────────────────────────────────────────────────
export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {},
) {
  const {
    authContext,
    initialEntries = ['/'],
    ...renderOptions
  } = options

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  const mockAuthValue = createMockAuthContext(authContext)

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider value={mockAuthValue}>
          <MemoryRouter initialEntries={initialEntries}>
            {children}
          </MemoryRouter>
        </AuthContext.Provider>
      </QueryClientProvider>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}
