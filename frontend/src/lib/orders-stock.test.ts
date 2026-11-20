import { describe, expect, it } from 'vitest'

import { invoiceNumber, STATUS_LABEL } from '@/lib/orders'
import { LOW_STOCK_THRESHOLD, stockState } from '@/lib/stock'

describe('invoiceNumber', () => {
  it('pads the order id and uses the year of the order', () => {
    expect(invoiceNumber({ id: 42, createdAt: '2026-11-20T10:00:00Z' })).toBe('BN-2026-000042')
  })
})

describe('order status labels', () => {
  it('has a readable label for every status', () => {
    expect(STATUS_LABEL['in-transit']).toBe('In transit')
    expect(Object.keys(STATUS_LABEL).sort()).toEqual(['cancelled', 'delivered', 'in-transit', 'processing'])
  })
})

describe('stockState', () => {
  it('is out at zero, low up to the threshold, otherwise in', () => {
    expect(stockState(0)).toBe('out')
    expect(stockState(LOW_STOCK_THRESHOLD)).toBe('low')
    expect(stockState(LOW_STOCK_THRESHOLD + 1)).toBe('in')
  })
})
