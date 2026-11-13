import { api, ApiError } from '@/lib/api'
import { digitsOnly } from '@/lib/card'
import type { CardInput } from '@/lib/card'

export type OrderStatus = 'processing' | 'in-transit' | 'delivered' | 'cancelled'

export interface OrderItem {
  id: number
  productId: string
  productName: string
  quantity: number
  unitPrice: number
  /** 0 to 1 (discounts arrive in a later sprint; 0 for now). */
  discountRate: number
  total: number
}

export interface Order {
  id: number
  status: OrderStatus
  address: string
  total: number
  items: OrderItem[]
  createdAt: string
}

interface ApiOrder {
  id: number
  status: OrderStatus
  address: string
  total_price: string
  created_at: string
  items: {
    id: number
    product: number
    product_name: string
    quantity: number
    unit_price: string
    discount_rate: string | number | null
    total_price: string
  }[]
}

function toOrder(o: ApiOrder): Order {
  return {
    id: o.id,
    status: o.status,
    address: o.address,
    total: Number(o.total_price),
    createdAt: o.created_at,
    items: o.items.map((i) => ({
      id: i.id,
      productId: String(i.product),
      productName: i.product_name,
      quantity: i.quantity,
      unitPrice: Number(i.unit_price),
      discountRate: Number(i.discount_rate ?? 0),
      total: Number(i.total_price),
    })),
  }
}

export interface OrdersPage {
  count: number
  next: string | null
  orders: Order[]
}

export async function getOrders(page = 1): Promise<OrdersPage> {
  const data = await api<{ count: number; next: string | null; results: ApiOrder[] }>(`/api/orders?page=${page}`)
  return { count: data.count, next: data.next, orders: data.results.map(toOrder) }
}

export async function getOrder(id: string): Promise<Order> {
  return toOrder(await api<ApiOrder>(`/api/orders/${encodeURIComponent(id)}`))
}

export interface StockProblem {
  productName: string
  requested: number
  available: number
}

export class CheckoutProblem extends Error {
  problems: StockProblem[]

  constructor(message: string, problems: StockProblem[]) {
    super(message)
    this.name = 'CheckoutProblem'
    this.problems = problems
  }
}

/**
 * Pays with the mock bank, then turns the server cart into an order.
 * The card number and CVV are only sent to the payment endpoint and are not kept anywhere.
 */
export async function placeOrder(card: CardInput, address: string): Promise<Order> {
  const payment = await api<{ payment_token: string }>('/api/payments/mock', {
    method: 'POST',
    json: { card_number: digitsOnly(card.number), expiry: card.expiry, cvv: card.cvv, holder: card.holder.trim() },
  })
  try {
    const order = await api<ApiOrder>('/api/checkout', {
      method: 'POST',
      json: { payment_token: payment.payment_token, address },
    })
    return toOrder(order)
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      const body = e.data as { detail?: string; problems?: { product_name: string; requested: number; available: number }[] }
      throw new CheckoutProblem(
        body.detail ?? 'Not enough stock for some items.',
        (body.problems ?? []).map((p) => ({ productName: p.product_name, requested: p.requested, available: p.available })),
      )
    }
    throw e
  }
}

export const STATUS_LABEL: Record<OrderStatus, string> = {
  processing: 'Processing',
  'in-transit': 'In transit',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
}

/** Invoice number shown on the invoice. Derived from the order (the backend has no invoice model yet). */
export function invoiceNumber(order: Pick<Order, 'id' | 'createdAt'>): string {
  return `BN-${new Date(order.createdAt).getFullYear()}-${String(order.id).padStart(6, '0')}`
}
