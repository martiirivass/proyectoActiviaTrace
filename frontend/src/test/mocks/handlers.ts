import { http, HttpResponse } from 'msw'

const API_BASE = 'http://localhost:8000/api/v1'

export const handlers = [
  // POST /auth/login — succeeds
  http.post(`${API_BASE}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email?: string; password?: string }

    if (body.email === 'test@example.com' && body.password === 'password123') {
      return HttpResponse.json({
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        requires_2fa: false,
      })
    }

    if (
      body.email === '2fa@example.com' &&
      body.password === 'password123'
    ) {
      return HttpResponse.json({
        access_token: '',
        refresh_token: '',
        requires_2fa: true,
        two_fa_token: 'mock-two-fa-token',
      })
    }

    return HttpResponse.json(
      { detail: 'Credenciales inválidas' },
      { status: 401 },
    )
  }),

  // POST /auth/2fa/verify
  http.post(`${API_BASE}/auth/2fa/verify`, async ({ request }) => {
    const body = (await request.json()) as {
      two_fa_token?: string
      code?: string
    }

    if (body.code === '123456') {
      return HttpResponse.json({
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
      })
    }

    return HttpResponse.json(
      { detail: 'Código de verificación inválido' },
      { status: 401 },
    )
  }),

  // POST /auth/refresh
  http.post(`${API_BASE}/auth/refresh`, async ({ request }) => {
    const body = (await request.json()) as { refresh_token?: string }

    if (body.refresh_token === 'valid-refresh-token') {
      return HttpResponse.json({
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
      })
    }

    return HttpResponse.json(
      { detail: 'Token inválido o expirado' },
      { status: 401 },
    )
  }),

  // POST /auth/logout
  http.post(`${API_BASE}/auth/logout`, () => {
    return new HttpResponse(null, { status: 204 })
  }),

  // POST /auth/forgot
  http.post(`${API_BASE}/auth/forgot`, () => {
    return new HttpResponse(null, { status: 204 })
  }),

  // POST /auth/reset
  http.post(`${API_BASE}/auth/reset`, async ({ request }) => {
    const body = (await request.json()) as {
      token?: string
      password?: string
    }

    if (body.token === 'valid-reset-token') {
      return new HttpResponse(null, { status: 204 })
    }

    return HttpResponse.json(
      { detail: 'Token inválido o expirado' },
      { status: 400 },
    )
  }),

  // GET /auth/me
  http.get(`${API_BASE}/auth/me`, () => {
    return HttpResponse.json({
      id: 'user-1',
      email: 'test@example.com',
      nombre: 'Test',
      apellido: 'User',
      roles: ['ADMIN'],
      permisos: ['admin:all', 'academica:read', 'usuarios:read'],
    })
  }),
]
