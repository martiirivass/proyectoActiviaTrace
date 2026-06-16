import { describe, it, expect, vi } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test/test-utils'
import { LoginForm } from '@/features/auth/components/LoginForm'

// Mock useLogin for controlled behavior
const mockMutate = vi.fn()
const mockUseLoginRef: { current: { login: { isError: boolean; error: Error | null; isPending: boolean; mutate: typeof mockMutate } } } = {
  current: {
    login: {
      mutate: mockMutate,
      isPending: false,
      isError: false,
      error: null,
    },
  },
}

vi.mock('@/features/auth/hooks/useLogin', () => ({
  useLogin: () => mockUseLoginRef.current,
}))

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseLoginRef.current = {
      login: {
        mutate: mockMutate,
        isPending: false,
        isError: false,
        error: null,
      },
    }
  })

  it('renders the login form', () => {
    renderWithProviders(<LoginForm />)

    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /iniciar sesión/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/¿olvidaste tu contraseña/i),
    ).toBeInTheDocument()
  })

  it('shows validation errors on empty submit', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginForm />)

    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    expect(await screen.findByText('El email es requerido')).toBeInTheDocument()
    expect(
      await screen.findByText('La contraseña es requerida'),
    ).toBeInTheDocument()
    expect(mockMutate).not.toHaveBeenCalled()
  })

  it('shows email validation error for invalid email', async () => {
    renderWithProviders(<LoginForm />)

    // Use fireEvent.change to ensure value is set correctly in jsdom
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'not-an-email' },
    })
    fireEvent.change(screen.getByLabelText('Contraseña'), {
      target: { value: 'password123' },
    })
    fireEvent.submit(screen.getByRole('button', { name: /iniciar sesión/i }).closest('form')!)

    expect(await screen.findByText('Ingrese un email válido')).toBeInTheDocument()
    expect(mockMutate).not.toHaveBeenCalled()
  })

  it('calls login API on valid submit', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginForm />)

    await user.type(screen.getByLabelText('Email'), 'test@example.com')
    await user.type(screen.getByLabelText('Contraseña'), 'password123')
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
    })
  })

  it('displays server error when login fails', async () => {
    mockUseLoginRef.current.login.isError = true
    mockUseLoginRef.current.login.error = new Error('Credenciales inválidas')

    renderWithProviders(<LoginForm />)

    expect(await screen.findByText('Credenciales inválidas')).toBeInTheDocument()
  })
})
