import { api } from '@/lib/api'
import { useCart, type CartItem } from '@/store/cart'

/** Cart as returned by GET/PUT /api/cart and POST /api/cart/merge. */
interface ApiCart {
  items: {
    product: number
    product_name: string
    unit_price: string
    quantity: number
    stock: number
    image: string | null
  }[]
}

type Body = { items: { product: number; quantity: number }[] }

function toBody(items: CartItem[]): Body {
  return { items: items.map((i) => ({ product: Number(i.productId), quantity: i.quantity })) }
}

function toItems(cart: ApiCart): CartItem[] {
  return cart.items.map((i) => ({
    productId: String(i.product),
    name: i.product_name,
    price: Number(i.unit_price),
    stock: i.stock,
    quantity: i.quantity,
    imageUrl: i.image ? `/${i.image.replace(/^\//, '')}` : undefined,
  }))
}

/** Set while we write the server's cart into the store, so the store->server sync ignores that change. */
let applyingServerCart = false

export function isApplyingServerCart() {
  return applyingServerCart
}

function applyServerCart(cart: ApiCart) {
  applyingServerCart = true
  useCart.setState({ items: toItems(cart) })
  applyingServerCart = false
}

/** After login: add the guest cart to the user's server cart (Req 4), then show the merged server cart. */
export async function mergeGuestCartIntoServer(): Promise<void> {
  const guest = useCart.getState().items
  const cart = await api<ApiCart>('/api/cart/merge', { method: 'POST', json: toBody(guest) })
  applyServerCart(cart)
}

/** On page load with an existing session: show the server cart. */
export async function loadServerCart(): Promise<void> {
  applyServerCart(await api<ApiCart>('/api/cart'))
}

/** Sends the current cart to the server (replaces it). */
export async function pushCartToServer(items: CartItem[]): Promise<void> {
  applyServerCart(await api<ApiCart>('/api/cart', { method: 'PUT', json: toBody(items) }))
}
