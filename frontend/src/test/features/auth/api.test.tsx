import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/setup'
import {
  setAccessToken,
  getAccessToken,
  setStoredRefreshToken,
  getStoredRefreshToken,
  clearTokens,
  get,
} from '@/shared/api/api'

const API_BASE = 'http://localhost:8000/api/v1'

describe('api client', () => {
  beforeEach(() => {
    clearTokens()
  })

  afterEach(() => {
    clearTokens()
  })

  it('attaches auth header when token exists', async () => {
    setAccessToken('test-access-token')

    let capturedAuthHeader: string | undefined

    server.use(
      http.get(`${API_BASE}/test`, ({ request }) => {
        capturedAuthHeader = request.headers.get('Authorization') ?? undefined
        return HttpResponse.json({ ok: true })
      }),
    )

    await get('/test')

    expect(capturedAuthHeader).toBe('Bearer test-access-token')
  })

  it('does not attach auth header when no token', async () => {
    let capturedAuthHeader: string | undefined

    server.use(
      http.get(`${API_BASE}/test`, ({ request }) => {
        capturedAuthHeader = request.headers.get('Authorization') ?? undefined
        return HttpResponse.json({ ok: true })
      }),
    )

    await get('/test')

    expect(capturedAuthHeader).toBeUndefined()
  })

  it('transparently refreshes on 401 and retries', async () => {
    setAccessToken('expired-token')
    setStoredRefreshToken('valid-refresh-token')

    let callCount = 0
    let refreshCalled = false

    // Intercept /auth/refresh endpoint
    server.use(
      http.post(`${API_BASE}/auth/refresh`, () => {
        refreshCalled = true
        return HttpResponse.json({
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
        })
      }),
    )

    // First call returns 401, retry returns 200
    server.use(
      http.get(`${API_BASE}/test-data`, () => {
        callCount++
        if (callCount === 1) {
          return HttpResponse.json(null, { status: 401 })
        }
        return HttpResponse.json({ data: 'success' })
      }),
    )

    const result = await get<{ data: string }>('/test-data')

    expect(refreshCalled).toBe(true)
    expect(callCount).toBe(2)
    expect(result).toEqual({ data: 'success' })
  })

  it('clears tokens and throws on failed refresh', async () => {
    setAccessToken('expired-token')
    setStoredRefreshToken('expired-refresh-token')

    server.use(
      http.post(`${API_BASE}/auth/refresh`, () => {
        return HttpResponse.json(
          { detail: 'Token inválido o expirado' },
          { status: 401 },
        )
      }),
      http.get(`${API_BASE}/test-fail`, () => {
        return HttpResponse.json(null, { status: 401 })
      }),
    )

    await expect(get('/test-fail')).rejects.toThrow()

    // Tokens should be cleared after failed refresh
    expect(getAccessToken()).toBeNull()
    expect(getStoredRefreshToken()).toBeNull()
  })
})
