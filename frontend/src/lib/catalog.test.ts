import { describe, expect, it } from 'vitest'

import { normaliseProduct, parseSort } from '@/lib/catalog'

const raw = {
  id: 3,
  name: 'Brazil Cerrado',
  price: '1350.00',
  quantity_in_stock: 29,
  category: { id: 1, name: 'Coffee Beans' },
  warranty_months: 0,
  warranty_status: 'No warranty',
  distributor_name: 'Duskberry',
  distributor_contact: 'supply@duskberry.example',
  image: 'products/db-bra-1000.webp',
  average_rating: 4.5,
  rating_count: 2,
}

describe('normaliseProduct', () => {
  it('converts the decimal price string and stock to numbers', () => {
    const p = normaliseProduct(raw)
    expect(p.price).toBe(1350)
    expect(p.stock).toBe(29)
  })

  it('serves relative image paths from the site root', () => {
    expect(normaliseProduct(raw).imageUrl).toBe('/products/db-bra-1000.webp')
  })

  it('maps the rating average and count', () => {
    const p = normaliseProduct(raw)
    expect(p.averageRating).toBe(4.5)
    expect(p.ratingCount).toBe(2)
  })

  it('keeps "no ratings yet" as null instead of 0', () => {
    expect(normaliseProduct({ ...raw, average_rating: null, rating_count: 0 }).averageRating).toBeNull()
  })

  it('shows the warranty length only when there is a warranty', () => {
    expect(normaliseProduct({ ...raw, warranty_status: 'Under warranty', warranty_months: 24 }).warranty).toBe('Under warranty (24 months)')
    expect(normaliseProduct(raw).warranty).toBe('No warranty')
  })

  it('puts the distributor contact in brackets', () => {
    expect(normaliseProduct(raw).distributor).toBe('Duskberry (supply@duskberry.example)')
  })
})

describe('parseSort', () => {
  it('falls back to the default for unknown values', () => {
    expect(parseSort('price-asc')).toBe('price-asc')
    expect(parseSort('banana')).toBe('')
    expect(parseSort(null)).toBe('')
  })
})
