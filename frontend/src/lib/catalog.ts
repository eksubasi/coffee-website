/**
 * Catalog data access: all endpoint paths and the API -> UI field mapping live here.
 *
 * Backend contract (eksubasi/coffee-website, backend/catalog + backend/core):
 *   GET /api/health                                -> { status: "ok", db: true }
 *   GET /api/categories/                           -> Category[]  (not paginated)
 *   GET /api/products/?category=<id>&page_size=100 -> { count, next, previous, results: Product[] }
 *       optional: &search=<text> (name OR description), &ordering=price|-price|popularity|-popularity
 *   GET /api/products/<id>/                        -> Product     (404 if unknown)
 *
 * API product fields: id, name, model, serial_number, description, quantity_in_stock, in_stock,
 * price (decimal string, TRY), warranty_status, warranty_months, distributor_name,
 * distributor_contact, category {id, name}, image (relative path), brand, origin, roast_date,
 * expiry_date, weight_capacity, popularity.
 */
import { api } from '@/lib/api'
import type { Category, HealthStatus, Product } from '@/types'

/** The API caps page_size at 100; a category holds far fewer products than that. */
const PAGE_SIZE = 100

type Raw = Record<string, unknown>
interface Paginated<T> {
  results: T[]
}

const str = (value: unknown): string => (value === null || value === undefined ? '' : String(value))
const optional = (value: unknown): string | undefined => str(value).trim() || undefined

function normaliseCategory(raw: Raw): Category {
  return { id: str(raw.id), name: str(raw.name), description: str(raw.description) }
}

/** Image paths from the API are relative (e.g. "products/db-ken-250.webp"); serve them from the site root. */
function imageUrl(path: unknown): string | undefined {
  const value = str(path).trim()
  if (!value) return undefined
  if (/^(https?:)?\/\//.test(value) || value.startsWith('/')) return value
  return `/${value}`
}

export function normaliseProduct(raw: Raw): Product {
  const category = (raw.category ?? {}) as Raw
  const warrantyMonths = Number(raw.warranty_months ?? 0)
  const warrantyStatus = str(raw.warranty_status) || 'No warranty'
  const contact = str(raw.distributor_contact).trim()

  return {
    id: str(raw.id),
    categoryId: str(category.id),
    categoryName: str(category.name),
    name: str(raw.name),
    model: str(raw.model),
    serialNumber: str(raw.serial_number),
    description: str(raw.description),
    stock: Number(raw.quantity_in_stock ?? 0),
    price: Number(raw.price ?? 0), // API sends a decimal string such as "590.00"
    warranty: warrantyMonths > 0 ? `${warrantyStatus} (${warrantyMonths} months)` : warrantyStatus,
    distributor: contact ? `${str(raw.distributor_name)} (${contact})` : str(raw.distributor_name),
    imageUrl: imageUrl(raw.image),
    brand: optional(raw.brand),
    origin: optional(raw.origin),
    roastDate: optional(raw.roast_date),
    expiryDate: optional(raw.expiry_date),
    weightCapacity: optional(raw.weight_capacity),
  }
}

export const getHealth = () => api<HealthStatus>('/api/health')

export async function getCategories(): Promise<Category[]> {
  const data = await api<Raw[]>('/api/categories/')
  return data.map(normaliseCategory)
}

/**
 * Sort choices as they appear in the URL (`?sort=`). '' means the API default (name A–Z).
 * The backend only accepts price | -price | popularity | -popularity in `?ordering=` (KAN-25).
 */
export const SORT_OPTIONS = [
  { value: '', label: 'Name (A–Z)', ordering: undefined },
  { value: 'price-asc', label: 'Price: low to high', ordering: 'price' },
  { value: 'price-desc', label: 'Price: high to low', ordering: '-price' },
  { value: 'popularity', label: 'Most popular', ordering: '-popularity' },
] as const

export type SortKey = (typeof SORT_OPTIONS)[number]['value']

/** Turns any `?sort=` value (missing, unknown, hand-typed) into a valid SortKey. */
export function parseSort(value: string | null): SortKey {
  return SORT_OPTIONS.find((option) => option.value === value)?.value ?? ''
}

export interface ProductQuery {
  categoryId?: string
  search?: string
  sort?: SortKey
}

export async function getProducts({ categoryId, search, sort = '' }: ProductQuery = {}): Promise<Product[]> {
  const params = new URLSearchParams({ page_size: String(PAGE_SIZE) })
  if (categoryId) params.set('category', categoryId)
  if (search?.trim()) params.set('search', search.trim())
  const ordering = SORT_OPTIONS.find((option) => option.value === sort)?.ordering
  if (ordering) params.set('ordering', ordering)

  const data = await api<Paginated<Raw>>(`/api/products/?${params}`)
  return data.results.map(normaliseProduct)
}

export async function getProduct(id: string): Promise<Product> {
  return normaliseProduct(await api<Raw>(`/api/products/${encodeURIComponent(id)}/`))
}
