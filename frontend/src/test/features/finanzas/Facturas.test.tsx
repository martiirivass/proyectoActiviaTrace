import { describe, it, expect } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders, mockUser } from '@/test/test-utils'
import { FacturasView } from '@/features/finanzas/components/FacturasView'
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
        permissions: ['facturas:gestionar'],
        login: async () => {},
        logout: async () => {},
        getAccessToken: () => 'mock-token',
      }}>
        <FacturasView />
      </AuthContext.Provider>
    </QueryClientProvider>,
  )
}

describe('Facturas', () => {
  it('renders list with facturas data', async () => {
    renderWithAuth()

    await waitFor(() => {
      expect(screen.getByText('Facturas')).toBeInTheDocument()
      expect(screen.getByText('Pérez, Juan')).toBeInTheDocument()
      expect(screen.getByText('Honorarios junio')).toBeInTheDocument()
    })
  })

  it('opens create modal on "Nueva Factura" click', async () => {
    renderWithAuth()
    const user = userEvent.setup()

    await user.click(screen.getByText('Nueva Factura'))

    await waitFor(() => {
      const headings = screen.getAllByText('Nueva Factura')
      expect(headings.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('shows Abonar button for Pendiente facturas', async () => {
    renderWithAuth()

    await waitFor(() => {
      const abonarButtons = screen.getAllByText('Abonar')
      expect(abonarButtons.length).toBeGreaterThan(0)
    })
  })
})
