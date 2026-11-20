export interface Category {
  id: string
  name: string
  description: string
}

/** Product as the UI uses it. Mapped from the Django API in `lib/catalog.ts`. */
export interface Product {
  id: string
  categoryId: string
  categoryName: string
  name: string
  model: string
  serialNumber: string
  description: string
  stock: number
  /** Price in TRY. */
  price: number
  /** e.g. "Under warranty (24 months)" or "No warranty". */
  warranty: string
  /** e.g. "Duskberry Roasters (supply@duskberry.example)". */
  distributor: string
  /** Path or URL of the product image; may not exist yet, the UI falls back to a placeholder. */
  imageUrl?: string

  // Optional, mostly for coffee products (empty for equipment)
  brand?: string
  origin?: string
  roastDate?: string
  expiryDate?: string
  weightCapacity?: string
}

export interface HealthStatus {
  status: string
  /** Whether the backend could reach its database (`false` = API up, DB down). */
  db?: boolean
}
