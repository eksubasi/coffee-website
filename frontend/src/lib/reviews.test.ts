import { afterEach, describe, expect, it, vi } from 'vitest'

import { COMMENT_MAX_LENGTH, commentProblem, formatAverage, getComments, getMyRating, postComment, putRating } from '@/lib/reviews'

function mockFetch(status: number, body: unknown) {
  const fn = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }))
  vi.stubGlobal('fetch', fn)
  return fn
}

afterEach(() => vi.unstubAllGlobals())

describe('comment validation', () => {
  it('rejects empty and whitespace-only comments', () => {
    expect(commentProblem('')).toBeDefined()
    expect(commentProblem('   \n ')).toBeDefined()
  })

  it('accepts normal text and rejects text over the limit', () => {
    expect(commentProblem('Smooth and chocolatey.')).toBeUndefined()
    expect(commentProblem('x'.repeat(COMMENT_MAX_LENGTH))).toBeUndefined()
    expect(commentProblem('x'.repeat(COMMENT_MAX_LENGTH + 1))).toBeDefined()
  })
})

describe('formatAverage', () => {
  it('shows one decimal', () => {
    expect(formatAverage(4)).toBe('4.0')
    expect(formatAverage(4.26)).toBe('4.3')
  })
})

describe('reviews API', () => {
  it('maps approved comments and the next-page flag', async () => {
    mockFetch(200, { count: 3, next: 'http://x/?page=2', results: [{ id: 7, author: 'Ada L.', text: 'Great', created_at: '2026-11-01T10:00:00Z' }] })
    const page = await getComments('3')
    expect(page.hasNext).toBe(true)
    expect(page.comments[0]).toEqual({ id: 7, author: 'Ada L.', text: 'Great', createdAt: '2026-11-01T10:00:00Z' })
  })

  it('asks for the requested page', async () => {
    const fetchMock = mockFetch(200, { count: 0, next: null, results: [] })
    await getComments('3', 2)
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/products/3/comments/?page=2')
  })

  it('reads whether the customer may rate', async () => {
    mockFetch(200, { score: null, can_rate: false })
    expect(await getMyRating('3')).toEqual({ score: null, canRate: false })
  })

  it('sends the score with PUT', async () => {
    const fetchMock = mockFetch(201, { score: 5, can_rate: true })
    const result = await putRating('3', 5)
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(init.method).toBe('PUT')
    expect(init.body).toBe(JSON.stringify({ score: 5 }))
    expect(result.score).toBe(5)
  })

  it('posts a comment and returns it as pending', async () => {
    mockFetch(201, { id: 1, product: 3, text: 'Nice', status: 'pending', created_at: '2026-11-20T10:00:00Z' })
    expect((await postComment('3', 'Nice')).status).toBe('pending')
  })

  it('turns a 403 into an error with the backend message', async () => {
    mockFetch(403, { detail: 'You can only rate products that were delivered to you.' })
    await expect(putRating('3', 5)).rejects.toThrow(/delivered/)
  })
})
