import { describe, expect, it } from 'vitest'

import { digitsOnly, formatCardNumber, formatExpiry, luhnValid, validateCard } from '@/lib/card'

const good = { number: '4242 4242 4242 4242', expiry: '12/30', cvv: '123', holder: 'Ada Lovelace' }
const now = new Date('2026-11-20')

describe('card helpers', () => {
  it('keeps only digits', () => {
    expect(digitsOnly('4242-4242 abcd')).toBe('42424242')
  })

  it('accepts a Luhn-valid number and rejects a typo', () => {
    expect(luhnValid('4242424242424242')).toBe(true)
    expect(luhnValid('4242424242424243')).toBe(false)
  })

  it('handles digits that become two-digit numbers when doubled', () => {
    // 79927398713 is the textbook Luhn example; 4539578763621486 is a valid Visa test number.
    expect(luhnValid('79927398713')).toBe(true)
    expect(luhnValid('4539578763621486')).toBe(true)
    expect(luhnValid('4539578763621487')).toBe(false)
  })

  it('groups the card number in fours while typing', () => {
    expect(formatCardNumber('4242424242424242')).toBe('4242 4242 4242 4242')
  })

  it('inserts the slash in the expiry date', () => {
    expect(formatExpiry('1230')).toBe('12/30')
    expect(formatExpiry('12')).toBe('12')
  })

  it('accepts the demo card', () => {
    expect(validateCard(good, now)).toEqual({})
  })

  it('rejects a number that fails the Luhn check', () => {
    expect(validateCard({ ...good, number: '1234 5678 9012 3456' }, now).number).toMatch(/not valid/)
  })

  it('rejects an expired card and a bad month', () => {
    expect(validateCard({ ...good, expiry: '01/20' }, now).expiry).toMatch(/expired/)
    expect(validateCard({ ...good, expiry: '13/30' }, now).expiry).toBe('Use MM/YY.')
  })

  it('requires a 3 or 4 digit CVV and a card holder', () => {
    const errors = validateCard({ ...good, cvv: '12', holder: '  ' }, now)
    expect(errors.cvv).toBeDefined()
    expect(errors.holder).toBeDefined()
  })
})
