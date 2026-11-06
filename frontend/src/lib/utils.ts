import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Brewnook prices are in Turkish lira (TRY).
const currency = new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' })

export function formatPrice(value: number) {
  return currency.format(value)
}
