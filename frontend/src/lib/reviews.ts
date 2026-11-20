/**
 * Ratings and comments (KAN-58). Backend contract (backend/reviews, KAN-56 / KAN-57):
 *   GET  /api/products/<id>/comments/        public, approved comments only, paginated {count, next, results}
 *   POST /api/products/<id>/comments/        customer, {text}; 201 with status "pending"; 403 if not delivered
 *   GET  /api/products/<id>/comments/mine/   the customer's own comments incl. pending / rejected (array)
 *   GET  /api/products/<id>/my-rating/       customer, {score: 1-5 | null, can_rate: boolean}
 *   PUT  /api/products/<id>/my-rating/       customer, {score}; 403 if the product was not delivered
 * The average and number of ratings are on the product itself (see lib/catalog.ts).
 */
import { api } from '@/lib/api'

export const COMMENT_MAX_LENGTH = 1000

export type CommentStatus = 'pending' | 'approved' | 'rejected'

export interface PublicComment {
  id: number
  author: string
  text: string
  createdAt: string
}

export interface MyComment {
  id: number
  text: string
  status: CommentStatus
  createdAt: string
}

export interface MyRating {
  score: number | null
  /** True only when the customer has a delivered order containing this product. */
  canRate: boolean
}

export interface CommentsPage {
  comments: PublicComment[]
  count: number
  hasNext: boolean
}

type Raw = Record<string, unknown>

const productPath = (productId: string) => `/api/products/${encodeURIComponent(productId)}`

export async function getComments(productId: string, page = 1): Promise<CommentsPage> {
  const data = await api<{ count: number; next: string | null; results: Raw[] }>(
    `${productPath(productId)}/comments/?page=${page}`,
  )
  return {
    count: data.count,
    hasNext: data.next !== null,
    comments: data.results.map((c) => ({
      id: Number(c.id),
      author: String(c.author ?? 'Customer'),
      text: String(c.text ?? ''),
      createdAt: String(c.created_at ?? ''),
    })),
  }
}

export async function getMyComments(productId: string): Promise<MyComment[]> {
  const data = await api<Raw[]>(`${productPath(productId)}/comments/mine/`)
  return data.map((c) => ({
    id: Number(c.id),
    text: String(c.text ?? ''),
    status: c.status as CommentStatus,
    createdAt: String(c.created_at ?? ''),
  }))
}

export async function postComment(productId: string, text: string): Promise<MyComment> {
  const c = await api<Raw>(`${productPath(productId)}/comments/`, { method: 'POST', json: { text } })
  return { id: Number(c.id), text: String(c.text), status: c.status as CommentStatus, createdAt: String(c.created_at) }
}

export async function getMyRating(productId: string): Promise<MyRating> {
  const data = await api<{ score: number | null; can_rate: boolean }>(`${productPath(productId)}/my-rating/`)
  return { score: data.score, canRate: data.can_rate }
}

export async function putRating(productId: string, score: number): Promise<MyRating> {
  const data = await api<{ score: number | null; can_rate: boolean }>(`${productPath(productId)}/my-rating/`, {
    method: 'PUT',
    json: { score },
  })
  return { score: data.score, canRate: data.can_rate }
}

/** Validates the comment text the same way the backend does (non-empty after trimming, max 1000). */
export function commentProblem(text: string): string | undefined {
  const trimmed = text.trim()
  if (!trimmed) return 'Write a comment first.'
  if (trimmed.length > COMMENT_MAX_LENGTH) return `Keep it under ${COMMENT_MAX_LENGTH} characters.`
  return undefined
}

/** "4.3" style label for an average; one decimal, never "4.0" noise for whole numbers. */
export function formatAverage(average: number): string {
  return (Math.round(average * 10) / 10).toFixed(1)
}
