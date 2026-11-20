import { beforeEach, describe, expect, it } from 'vitest'

import { selectItemCount, selectSubtotal, useCart } from '@/store/cart'
import type { Product } from '@/types'

const product = (over: Partial<Product> = {}): Product => ({
  id: '1', categoryId: '1', categoryName: 'Beans', name: 'Ethiopia', model: 'M', serialNumber: 'S', description: '',
  stock: 5, price: 100, warranty: 'No warranty', distributor: 'D', averageRating: null, ratingCount: 0, ...over,
})

beforeEach(() => useCart.setState({ items: [] }))

describe('guest cart', () => {
  it('adds a product and counts it', () => {
    expect(useCart.getState().add(product(), 2)).toBe(2)
    expect(selectItemCount(useCart.getState())).toBe(2)
  })

  it('never goes above stock', () => {
    useCart.getState().add(product(), 4)
    expect(useCart.getState().add(product(), 4)).toBe(1)
    expect(useCart.getState().items[0].quantity).toBe(5)
  })

  it('refuses out-of-stock products', () => {
    expect(useCart.getState().add(product({ stock: 0 }))).toBe(0)
    expect(useCart.getState().items).toHaveLength(0)
  })

  it('calculates the subtotal', () => {
    useCart.getState().add(product({ id: '1', price: 100 }), 2)
    useCart.getState().add(product({ id: '2', price: 50 }), 1)
    expect(selectSubtotal(useCart.getState())).toBe(250)
  })

  it('removes a line when the quantity is set to zero', () => {
    useCart.getState().add(product())
    useCart.getState().setQuantity('1', 0)
    expect(useCart.getState().items).toHaveLength(0)
  })

  it('clamps quantity to stock when stock shrinks', () => {
    useCart.getState().add(product(), 5)
    useCart.getState().syncStock('1', 2)
    expect(useCart.getState().items[0].quantity).toBe(2)
  })
})
