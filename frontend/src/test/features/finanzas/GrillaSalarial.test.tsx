import { describe, it, expect } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders, mockUser } from '@/test/test-utils'
import { GrillaSalarialView } from '@/features/finanzas/components/GrillaSalarialView'
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
        permissions: ['grilla-salarial:ver'],
        login: async () => {},
        logout: async () => {},
        getAccessToken: () => 'mock-token',
      }}>
        <GrillaSalarialView />
      </AuthContext.Provider>
    </QueryClientProvider>,
  )
}

describe('GrillaSalarial', () => {
  it('renders tabs and loads salario base data', async () => {
    renderWithAuth()

    expect(screen.getByText('Salario Base')).toBeInTheDocument()
    expect(screen.getByText('Salario Plus')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('PROFESOR')).toBeInTheDocument()
      expect(screen.getByText('$50.000')).toBeInTheDocument()
    })
  })

  it('shows create modal on "Nuevo Salario Base" click', async () => {
    renderWithAuth()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Nuevo Salario Base')).toBeInTheDocument()
    })

    const buttons = screen.getAllByText('Nuevo Salario Base')
    await user.click(buttons[0]!)

    await waitFor(() => {
      const headings = screen.getAllByText('Nuevo Salario Base')
      expect(headings.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('switches to Salario Plus tab', async () => {
    renderWithAuth()
    const user = userEvent.setup()

    await user.click(screen.getByText('Salario Plus'))

    await waitFor(() => {
      expect(screen.getByText('Nuevo Salario Plus')).toBeInTheDocument()
    })
  })
})
