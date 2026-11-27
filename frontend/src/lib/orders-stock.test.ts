import { describe, expect, it } from 'vitest'

import { invoiceNumber, type InvoiceSnapshot, STATUS_LABEL } from '@/lib/orders'
import { LOW_STOCK_THRESHOLD, stockState } from '@/lib/stock'

describe('invoiceNumber', () => {
  it('shows the number stored on the invoice', () => {
    const invoice = { number: 'BN-544177F133594F6B' } as InvoiceSnapshot
    expect(invoiceNumber({ invoice })).toBe('BN-544177F133594F6B')
  })

  it('says "Not issued" when the order has no invoice', () => {
    expect(invoiceNumber({ invoice: null })).toBe('Not issued')
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
