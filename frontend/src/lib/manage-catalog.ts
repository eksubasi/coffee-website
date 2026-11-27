/**
 * Product-manager API (KAN-50 / KAN-59, backend in catalog/manage_views.py). Product manager only.
 *
 *   GET    /api/manage/products               all products incl. cost (not paginated)
 *   POST   /api/manage/products               add a product (price + stock only settable here)
 *   PATCH  /api/manage/products/{id}          edit; price and stock are read-only after creation
 *   DELETE /api/manage/products/{id}          409 if the product was ever ordered
 *   PATCH  /api/manage/products/{id}/stock    {"quantity_in_stock": n} or {"change": ±n}
 *   GET    /api/manage/categories             with product_count
 *   POST / PATCH / DELETE /api/manage/categories[/{id}]   DELETE: 409 while it has products
 */
import { api } from '@/lib/api'

export type WarrantyStatus = 'No warranty' | 'Under warranty'

/** A product as the manager sees it (includes cost; price is a number in TRY). */
export interface ManagedProduct {
  id: number
  name: string
  model: string
  serialNumber: string
  description: string
  stock: number
  price: number
  /** Purchase cost; null means "use 50% of price" for profit/loss (Req 11). */
  cost: number | null
  effectiveCost: number
  warrantyStatus: WarrantyStatus
  warrantyMonths: number
  distributorName: string
  distributorContact: string
  categoryId: number
  categoryName: string
  /** Relative path like "products/db-eth-250.webp" (served from frontend/public). */
  image: string
  brand: string
  origin: string
  /** "YYYY-MM-DD" or "" */
  roastDate: string
  expiryDate: string
  weightCapacity: string
  popularity: number
}

export interface ManagedCategory {
  id: number
  name: string
  description: string
  productCount: number
}

/** Values of the add / edit form. Strings, as typed into the inputs. */
export interface ProductFormValues {
  name: string
  model: string
  serialNumber: string
  description: string
  categoryId: string
  price: string
  stock: string
  cost: string
  warrantyStatus: WarrantyStatus
  warrantyMonths: string
  distributorName: string
  distributorContact: string
  image: string
  brand: string
  origin: string
  roastDate: string
  expiryDate: string
  weightCapacity: string
}

type Raw = Record<string, unknown>
const str = (v: unknown) => (v === null || v === undefined ? '' : String(v))
const num = (v: unknown) => Number(v ?? 0)

function toProduct(raw: Raw): ManagedProduct {
  return {
    id: num(raw.id),
    name: str(raw.name),
    model: str(raw.model),
    serialNumber: str(raw.serial_number),
    description: str(raw.description),
    stock: num(raw.quantity_in_stock),
    price: num(raw.price),
    cost: raw.cost === null || raw.cost === undefined || raw.cost === '' ? null : num(raw.cost),
    effectiveCost: num(raw.effective_cost),
    warrantyStatus: raw.warranty_status === 'Under warranty' ? 'Under warranty' : 'No warranty',
    warrantyMonths: num(raw.warranty_months),
    distributorName: str(raw.distributor_name),
    distributorContact: str(raw.distributor_contact),
    categoryId: num(raw.category),
    categoryName: str(raw.category_name),
    image: str(raw.image),
    brand: str(raw.brand),
    origin: str(raw.origin),
    roastDate: str(raw.roast_date),
    expiryDate: str(raw.expiry_date),
    weightCapacity: str(raw.weight_capacity),
    popularity: num(raw.popularity),
  }
}

function toCategory(raw: Raw): ManagedCategory {
  return {
    id: num(raw.id),
    name: str(raw.name),
    description: str(raw.description),
    productCount: num(raw.product_count),
  }
}

/** Maps backend field names to form field names, to show 400 errors next to the right input. */
export const PRODUCT_FIELD_MAP: Record<string, keyof ProductFormValues> = {
  name: 'name',
  model: 'model',
  serial_number: 'serialNumber',
  description: 'description',
  category: 'categoryId',
  price: 'price',
  quantity_in_stock: 'stock',
  cost: 'cost',
  warranty_status: 'warrantyStatus',
  warranty_months: 'warrantyMonths',
  distributor_name: 'distributorName',
  distributor_contact: 'distributorContact',
  image: 'image',
  brand: 'brand',
  origin: 'origin',
  roast_date: 'roastDate',
  expiry_date: 'expiryDate',
  weight_capacity: 'weightCapacity',
}

export function emptyProductForm(): ProductFormValues {
  return {
    name: '',
    model: '',
    serialNumber: '',
    description: '',
    categoryId: '',
    price: '',
    stock: '0',
    cost: '',
    warrantyStatus: 'No warranty',
    warrantyMonths: '0',
    distributorName: '',
    distributorContact: '',
    image: '',
    brand: '',
    origin: '',
    roastDate: '',
    expiryDate: '',
    weightCapacity: '',
  }
}

export function productToForm(p: ManagedProduct): ProductFormValues {
  return {
    name: p.name,
    model: p.model,
    serialNumber: p.serialNumber,
    description: p.description,
    categoryId: String(p.categoryId),
    price: String(p.price),
    stock: String(p.stock),
    cost: p.cost === null ? '' : String(p.cost),
    warrantyStatus: p.warrantyStatus,
    warrantyMonths: String(p.warrantyMonths),
    distributorName: p.distributorName,
    distributorContact: p.distributorContact,
    image: p.image,
    brand: p.brand,
    origin: p.origin,
    roastDate: p.roastDate,
    expiryDate: p.expiryDate,
    weightCapacity: p.weightCapacity,
  }
}

/** Builds the JSON body. `creating` adds price and stock, which the backend accepts only on create. */
function formToBody(v: ProductFormValues, creating: boolean): Raw {
  const body: Raw = {
    name: v.name.trim(),
    model: v.model.trim(),
    serial_number: v.serialNumber.trim(),
    description: v.description.trim(),
    category: Number(v.categoryId),
    cost: v.cost.trim() === '' ? null : v.cost.trim(),
    warranty_status: v.warrantyStatus,
    warranty_months: v.warrantyStatus === 'Under warranty' ? Number(v.warrantyMonths || 0) : 0,
    distributor_name: v.distributorName.trim(),
    distributor_contact: v.distributorContact.trim(),
    image: v.image.trim(),
    brand: v.brand.trim(),
    origin: v.origin.trim(),
    roast_date: v.roastDate || null,
    expiry_date: v.expiryDate || null,
    weight_capacity: v.weightCapacity.trim(),
  }
  if (creating) {
    body.price = v.price.trim()
    body.quantity_in_stock = Number(v.stock || 0)
  }
  return body
}

// --- products -------------------------------------------------------------------------------

export async function listManagedProducts(): Promise<ManagedProduct[]> {
  const data = await api<Raw[]>('/api/manage/products')
  return data.map(toProduct)
}

export async function getManagedProduct(id: number | string): Promise<ManagedProduct> {
  return toProduct(await api<Raw>(`/api/manage/products/${id}`))
}

export async function createProduct(values: ProductFormValues): Promise<ManagedProduct> {
  return toProduct(await api<Raw>('/api/manage/products', { method: 'POST', json: formToBody(values, true) }))
}

export async function updateProduct(id: number, values: ProductFormValues): Promise<ManagedProduct> {
  return toProduct(await api<Raw>(`/api/manage/products/${id}`, { method: 'PATCH', json: formToBody(values, false) }))
}

/** Throws ApiError 409 when the product has orders (it must then be kept, with stock 0). */
export async function deleteProduct(id: number): Promise<void> {
  await api<void>(`/api/manage/products/${id}`, { method: 'DELETE' })
}

/** Stock change for KAN-59: either set an absolute value or add / remove some. */
export async function updateStock(
  id: number,
  update: { set: number } | { change: number },
): Promise<ManagedProduct> {
  const json = 'set' in update ? { quantity_in_stock: update.set } : { change: update.change }
  return toProduct(await api<Raw>(`/api/manage/products/${id}/stock`, { method: 'PATCH', json }))
}

// --- categories -----------------------------------------------------------------------------

export async function listManagedCategories(): Promise<ManagedCategory[]> {
  const data = await api<Raw[]>('/api/manage/categories')
  return data.map(toCategory)
}

export async function createCategory(values: { name: string; description: string }): Promise<ManagedCategory> {
  return toCategory(await api<Raw>('/api/manage/categories', { method: 'POST', json: values }))
}

export async function updateCategory(
  id: number,
  values: { name: string; description: string },
): Promise<ManagedCategory> {
  return toCategory(await api<Raw>(`/api/manage/categories/${id}`, { method: 'PATCH', json: values }))
}

/** Throws ApiError 409 while the category still has products. */
export async function deleteCategory(id: number): Promise<void> {
  await api<void>(`/api/manage/categories/${id}`, { method: 'DELETE' })
}
