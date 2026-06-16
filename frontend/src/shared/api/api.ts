import axios, {
  type AxiosError,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'

// ── In-memory token store ──────────────────────────────────────────────
let accessToken: string | null = null
let refreshPromise: Promise<string | null> | null = null

const REFRESH_TOKEN_KEY = 'trace_refresh_token'

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getAccessToken(): string | null {
  return accessToken
}

export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setStoredRefreshToken(token: string | null): void {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}

export function clearTokens(): void {
  accessToken = null
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

// ── Axios instance ─────────────────────────────────────────────────────
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// ── Request interceptor: attach Bearer token ───────────────────────────
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    return config
  },
  (error: AxiosError) => Promise.reject(error),
)

// ── Failed request queue (for concurrent 401s) ─────────────────────────
interface QueueItem {
  resolve: (value: AxiosResponse | PromiseLike<AxiosResponse>) => void
  reject: (reason: unknown) => void
  config: InternalAxiosRequestConfig
}

let isRefreshing = false
let failedQueue: QueueItem[] = []

function processQueue(error: unknown, token: string | null): void {
  failedQueue.forEach((item) => {
    if (error) {
      item.reject(error)
    } else if (token) {
      if (item.config.headers) {
        item.config.headers.Authorization = `Bearer ${token}`
      }
      item.resolve(api(item.config))
    } else {
      item.reject(new Error('No token available'))
    }
  })
  failedQueue = []
}

// ── Response interceptor: transparent refresh on 401 ───────────────────
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // Don't intercept the refresh request itself
    if (originalRequest.url?.includes('/auth/refresh')) {
      return Promise.reject(error)
    }

    // Handle 401 — attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue this request while refresh is in progress
        return new Promise<AxiosResponse>((resolve, reject) => {
          failedQueue.push({ resolve, reject, config: originalRequest })
        })
      }

      originalRequest._retry = true
      isRefreshing = true
      refreshPromise = doRefresh()

      try {
        const newToken = await refreshPromise
        processQueue(null, newToken)

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        // Redirect to login on refresh failure
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
        refreshPromise = null
      }
    }

    // Handle 403 — reject with typed error
    if (error.response?.status === 403) {
      const forbiddenError = new Error('Sin permisos suficientes') as Error & {
        status: number
        data: unknown
      }
      forbiddenError.status = 403
      forbiddenError.data = error.response.data
      return Promise.reject(forbiddenError)
    }

    return Promise.reject(error)
  },
)

// ── Refresh logic ──────────────────────────────────────────────────────
async function doRefresh(): Promise<string | null> {
  const storedRefresh = getStoredRefreshToken()
  if (!storedRefresh) {
    throw new Error('No refresh token available')
  }

  const response = await axios.post(
    `${api.defaults.baseURL}/auth/refresh`,
    { refresh_token: storedRefresh },
    { headers: { 'Content-Type': 'application/json' } },
  )

  const { access_token, refresh_token } = response.data
  accessToken = access_token
  if (refresh_token) {
    setStoredRefreshToken(refresh_token)
  }

  return access_token
}

// ── Typed helper methods ───────────────────────────────────────────────
export function get<T = unknown>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  return api.get<T>(url, config).then((res) => res.data)
}

export function post<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  return api.post<T>(url, data, config).then((res) => res.data)
}

export function put<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  return api.put<T>(url, data, config).then((res) => res.data)
}

export function patch<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  return api.patch<T>(url, data, config).then((res) => res.data)
}

export function del<T = unknown>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  return api.delete<T>(url, config).then((res) => res.data)
}

export default api
