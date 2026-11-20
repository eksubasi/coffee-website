import { afterEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError, describeError, setAccessToken } from '@/lib/api'

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

afterEach(() => {
  vi.unstubAllGlobals()
  setAccessToken(null)
})

describe('describeError', () => {
  it('uses the detail message', () => {
    expect(describeError({ detail: 'Nope' }, 'fallback')).toBe('Nope')
  })

  it('joins field errors', () => {
    expect(describeError({ email: ['Already used.'] }, 'fallback')).toBe('email: Already used.')
  })

  it('falls back when the body is unusable', () => {
    expect(describeError(undefined, 'fallback')).toBe('fallback')
  })
})

describe('api()', () => {
  it('sends the access token as a Bearer header', async () => {
    const fetchMock = vi.fn().mockResolvedValue(json(200, { ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    setAccessToken('abc')
    await api('/api/cart')
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer abc')
  })

  it('refreshes the token once and retries after a 401', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(json(401, { detail: 'expired' }))
      .mockResolvedValueOnce(json(200, { access: 'new-token' }))
      .mockResolvedValueOnce(json(200, { items: [] }))
    vi.stubGlobal('fetch', fetchMock)
    setAccessToken('old')
    expect(await api('/api/cart')).toEqual({ items: [] })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/auth/refresh')
  })

  it('throws an ApiError with the status for failed requests', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json(404, { detail: 'Not found.' })))
    await expect(api('/api/products/999/')).rejects.toMatchObject({ status: 404, message: 'Not found.' })
  })

  it('reports an unreachable server as status 0', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network')))
    const error = await api('/api/health').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).status).toBe(0)
  })
})
