/** Client-side card format checks (the backend repeats them; these just give instant feedback). */

export function digitsOnly(value: string): string {
  return value.replace(/\D/g, '')
}

export function luhnValid(number: string): boolean {
  let sum = 0
  let double = false
  for (let i = number.length - 1; i >= 0; i--) {
    let digit = Number(number[i])
    if (double) {
      digit *= 2
      if (digit > 9) digit -= 9
    }
    sum += digit
    double = !double
  }
  return sum % 10 === 0
}

export function formatCardNumber(value: string): string {
  return digitsOnly(value).slice(0, 19).replace(/(.{4})/g, '$1 ').trim()
}

/** "1230" -> "12/30" while typing. */
export function formatExpiry(value: string): string {
  const digits = digitsOnly(value).slice(0, 4)
  return digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits
}

export interface CardInput {
  number: string
  expiry: string
  cvv: string
  holder: string
}

export type CardErrors = Partial<Record<keyof CardInput, string>>

export function validateCard(card: CardInput, now = new Date()): CardErrors {
  const errors: CardErrors = {}
  const number = digitsOnly(card.number)
  if (number.length < 12 || number.length > 19) errors.number = 'Card number must have 12 to 19 digits.'
  else if (!luhnValid(number)) errors.number = 'Card number is not valid.'

  const match = /^(\d{2})\/(\d{2})$/.exec(card.expiry)
  if (!match || Number(match[1]) < 1 || Number(match[1]) > 12) errors.expiry = 'Use MM/YY.'
  else {
    const year = 2000 + Number(match[2])
    const month = Number(match[1])
    if (year < now.getFullYear() || (year === now.getFullYear() && month < now.getMonth() + 1)) errors.expiry = 'This card has expired.'
  }

  if (!/^\d{3,4}$/.test(card.cvv)) errors.cvv = 'CVV must be 3 or 4 digits.'
  if (!card.holder.trim()) errors.holder = 'Enter the name on the card.'
  return errors
}
