import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '@/test/test-utils'
import { AuthGuard } from '@/shared/components/guards/AuthGuard'
import { Routes, Route } from 'react-router-dom'
import { mockUser } from '@/test/test-utils'

describe('AuthGuard', () => {
  it('redirects to /login when not authenticated', () => {
    renderWithProviders(
      <Routes>
        <Route element={<AuthGuard />}>
          <Route path="/" element={<p>Protected content</p>} />
        </Route>
        <Route path="/login" element={<p>Login page</p>} />
      </Routes>,
      { initialEntries: ['/'] },
    )

    expect(screen.getByText('Login page')).toBeInTheDocument()
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    renderWithProviders(
      <Routes>
        <Route element={<AuthGuard />}>
          <Route path="/" element={<p>Protected content</p>} />
        </Route>
        <Route path="/login" element={<p>Login page</p>} />
      </Routes>,
      {
        initialEntries: ['/'],
        authContext: {
          user: mockUser,
          isAuthenticated: true,
          isLoading: false,
        },
      },
    )

    expect(screen.getByText('Protected content')).toBeInTheDocument()
    expect(screen.queryByText('Login page')).not.toBeInTheDocument()
  })

  it('shows loading spinner while checking auth', () => {
    renderWithProviders(
      <Routes>
        <Route element={<AuthGuard />}>
          <Route path="/" element={<p>Protected content</p>} />
        </Route>
        <Route path="/login" element={<p>Login page</p>} />
      </Routes>,
      {
        initialEntries: ['/'],
        authContext: {
          user: null,
          isAuthenticated: false,
          isLoading: true,
        },
      },
    )

    expect(screen.getByRole('status', { name: /cargando/i })).toBeInTheDocument()
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument()
    expect(screen.queryByText('Login page')).not.toBeInTheDocument()
  })
})
