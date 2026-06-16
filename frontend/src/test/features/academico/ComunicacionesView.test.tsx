import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, render, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ComunicacionesView } from '@/features/academico/components/ComunicacionesView'

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/comision/mat-1/coh-1/comunicaciones']}>
        <Routes>
          <Route path="/comision/:materiaId/:cohorteId/comunicaciones" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ComunicacionesView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders redaction form', async () => {
    renderWithProviders(<ComunicacionesView />)

    await waitFor(() => {
      expect(screen.getByText(/redactar comunicación/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/tracking de comunicaciones/i)).toBeInTheDocument()
  })

  it('shows tracking table', async () => {
    renderWithProviders(<ComunicacionesView />)

    await waitFor(() => {
      expect(screen.getByText(/Aviso importante/)).toBeInTheDocument()
    })
  })
})
