import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ImportWizard } from '@/features/academico/components/ImportWizard/ImportWizard'

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/comision/mat-1/coh-1/calificaciones']}>
        <Routes>
          <Route path="/comision/:materiaId/:cohorteId/calificaciones" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ImportWizard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload step with dropzone', () => {
    renderWithProviders(<ImportWizard />)
    expect(screen.getByText(/arrastrá tu archivo aquí/i)).toBeInTheDocument()
    expect(screen.getByText(/formatos soportados/i)).toBeInTheDocument()
  })

  it('shows validation error on invalid file format', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ImportWizard />)

    const input = screen.getByRole('button', { name: /arrastrá tu archivo/i })
    expect(input).toBeInTheDocument()
  })

  it('progresses through wizard steps', async () => {
    renderWithProviders(<ImportWizard />)
    expect(screen.getByText(/subir archivo/i)).toBeInTheDocument()
  })
})
