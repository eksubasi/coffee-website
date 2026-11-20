/** At or below this many items the UI warns that stock is running out. */
export const LOW_STOCK_THRESHOLD = 5

export type StockState = 'out' | 'low' | 'in'

export function stockState(stock: number): StockState {
  if (stock <= 0) return 'out'
  if (stock <= LOW_STOCK_THRESHOLD) return 'low'
  return 'in'
}
