import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { Product } from '@/types'

export interface CartItem {
  productId: string
  name: string
  price: number
  /** Last known stock; the cart never lets quantity exceed it. */
  stock: number
  quantity: number
  imageUrl?: string
}

interface CartState {
  items: CartItem[]
  /** Adds `quantity` of a product, capped at stock. Returns how many were actually added. */
  add: (product: Product, quantity?: number) => number
  setQuantity: (productId: string, quantity: number) => void
  remove: (productId: string) => void
  clear: () => void
  /** Refreshes the stock snapshot from the server and clamps quantities / drops sold-out items. */
  syncStock: (productId: string, stock: number) => void
}

export const useCart = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],

      add: (product, quantity = 1) => {
        if (product.stock <= 0 || quantity <= 0) return 0
        const existing = get().items.find((item) => item.productId === product.id)
        const current = existing?.quantity ?? 0
        const next = Math.min(current + quantity, product.stock)
        const added = next - current
        if (added <= 0) return 0

        set((state) => ({
          items: existing
            ? state.items.map((item) =>
                item.productId === product.id
                  ? { ...item, quantity: next, stock: product.stock, price: product.price }
                  : item,
              )
            : [
                ...state.items,
                {
                  productId: product.id,
                  name: product.name,
                  price: product.price,
                  stock: product.stock,
                  quantity: next,
                  imageUrl: product.imageUrl,
                },
              ],
        }))
        return added
      },

      setQuantity: (productId, quantity) =>
        set((state) => ({
          items: state.items
            .map((item) =>
              item.productId === productId
                ? { ...item, quantity: Math.min(Math.floor(quantity), item.stock) }
                : item,
            )
            .filter((item) => item.quantity > 0),
        })),

      remove: (productId) =>
        set((state) => ({ items: state.items.filter((item) => item.productId !== productId) })),

      clear: () => set({ items: [] }),

      syncStock: (productId, stock) =>
        set((state) => ({
          items: state.items
            .map((item) =>
              item.productId === productId
                ? { ...item, stock, quantity: Math.min(item.quantity, stock) }
                : item,
            )
            .filter((item) => item.quantity > 0),
        })),
    }),
    {
      name: 'brewnook-guest-cart',
      version: 1,
      partialize: (state) => ({ items: state.items }),
    },
  ),
)

export const selectItemCount = (state: CartState) =>
  state.items.reduce((sum, item) => sum + item.quantity, 0)

export const selectSubtotal = (state: CartState) =>
  state.items.reduce((sum, item) => sum + item.price * item.quantity, 0)
