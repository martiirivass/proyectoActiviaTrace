import { describe, it, expect } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders, mockUser } from '@/test/test-utils'
import { LiquidacionesView } from '@/features/finanzas/components/LiquidacionesView'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthContext } from '@/shared/providers/AuthProvider'

function renderWithAuth() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return renderWithProviders(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={{
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        permissions: ['liquidaciones:ver', 'liquidaciones:cerrar'],
        login: async () => {},
        logout: async () => {},
        getAccessToken: () => 'mock-token',
      }}>
        <LiquidacionesView />
      </AuthContext.Provider>
    </QueryClientProvider>,
  )
}

describe('LiquidacionesView', () => {
  it('renders filters and title', () => {
    renderWithAuth()
    expect(screen.getByText('Liquidaciones')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ingrese ID de cohorte')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('2026-06')).toBeInTheDocument()
  })

  it('loads and displays liquidaciones data when filters are applied', async () => {
    renderWithAuth()
    const user = userEvent.setup()

    await user.type(screen.getByPlaceholderText('Ingrese ID de cohorte'), 'coh-1')
    await user.type(screen.getByPlaceholderText('2026-06'), '2026-06')

    await user.click(screen.getByRole('button', { name: /cargar/i }))

    await waitFor(() => {
      expect(screen.getByText('Pérez, Juan')).toBeInTheDocument()
      expect(screen.getByText('García, María')).toBeInTheDocument()
    })

    expect(screen.getByText('$60.000')).toBeInTheDocument()
  })

  it('segments by NEXO tab correctly', async () => {
    renderWithAuth()
    const user = userEvent.setup()

    await user.type(screen.getByPlaceholderText('Ingrese ID de cohorte'), 'coh-1')
    await user.type(screen.getByPlaceholderText('2026-06'), '2026-06')
    await user.click(screen.getByRole('button', { name: /cargar/i }))

    await waitFor(() => {
      expect(screen.getByText('NEXO')).toBeInTheDocument()
    })

    await user.click(screen.getByText('NEXO'))

    await waitFor(() => {
      expect(screen.getByText('García, María')).toBeInTheDocument()
    })
  })

  it('shows KPI cards', async () => {
    renderWithAuth()
    const user = userEvent.setup()

    await user.type(screen.getByPlaceholderText('Ingrese ID de cohorte'), 'coh-1')
    await user.type(screen.getByPlaceholderText('2026-06'), '2026-06')
    await user.click(screen.getByRole('button', { name: /cargar/i }))

    await waitFor(() => {
      expect(screen.getByText('Total Facturante')).toBeInTheDocument()
      expect(screen.getByText('Total No Facturante')).toBeInTheDocument()
    })
  })
})
