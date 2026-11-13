/**
 * Thin fetch wrapper. The base URL comes from VITE_API_BASE_URL (default: "" = same origin,
 * which the Vite dev server proxies to the Django backend).
 *
 * Auth: the short-lived access token is kept in memory only (never in localStorage); the refresh token
 * is an httpOnly cookie managed by the backend, so requests are sent with credentials.
 */
const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  status: number
  /** Parsed JSON error body from the backend, if any. */
  data?: unknown

  constructor(message: string, status: number, data?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

let accessToken: string | null = null
let refreshing: Promise<string | null> | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

/** Turns a DRF error body ({"detail": "..."} or {"field": ["msg"]}) into one readable string. */
export function describeError(data: unknown, fallback: string): string {
  if (data && typeof data === 'object') {
    const body = data as Record<string, unknown>
    if (typeof body.detail === 'string') return body.detail
    const parts = Object.entries(body).flatMap(([field, value]) => {
      const messages = Array.isArray(value) ? value : [value]
      return messages.filter((m): m is string => typeof m === 'string').map((m) => (field === 'non_field_errors' ? m : `${field}: ${m}`))
    })
    if (parts.length > 0) return parts.join(' ')
  }
  return fallback
}

/** Asks the backend for a new access token using the refresh cookie. One call at a time. */
export function refreshAccessToken(): Promise<string | null> {
  refreshing ??= fetch(`${BASE_URL}/api/auth/refresh`, { method: 'POST', credentials: 'include' })
    .then(async (response) => {
      if (!response.ok) return null
      const data = (await response.json()) as { access?: string }
      accessToken = data.access ?? null
      return accessToken
    })
    .catch(() => null)
    .finally(() => {
      refreshing = null
    })
  return refreshing
}

async function send(path: string, init: RequestInit | undefined, json: unknown): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (json !== undefined) headers['Content-Type'] = 'application/json'
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`
  try {
    return await fetch(`${BASE_URL}${path}`, {
      ...init,
      credentials: 'include',
      headers: { ...headers, ...init?.headers },
      body: json !== undefined ? JSON.stringify(json) : init?.body,
    })
  } catch {
    throw new ApiError('Could not reach the server.', 0)
  }
}

export async function api<T>(path: string, init?: RequestInit & { json?: unknown }): Promise<T> {
  const { json, ...rest } = init ?? {}
  let response = await send(path, rest, json)

  // Access token expired: refresh once and retry (not for the auth endpoints themselves).
  if (response.status === 401 && accessToken && !path.startsWith('/api/auth/')) {
    if (await refreshAccessToken()) response = await send(path, rest, json)
  }

  if (!response.ok) {
    const data = await response.json().catch(() => undefined)
    throw new ApiError(describeError(data, `Request failed (${response.status})`), response.status, data)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
