import { Badge } from '@/components/ui/badge'
import { stockState, type StockState } from '@/lib/stock'
import { cn } from '@/lib/utils'

const styles: Record<StockState, string> = {
  out: 'border-destructive/30 bg-destructive/10 text-destructive',
  low: 'border-warning/30 bg-warning/10 text-warning',
  in: 'border-success/30 bg-success/10 text-success',
}

/**
 * Stock level for a product (Req 9: customers see the quantity in stock).
 * Out-of-stock products stay visible but cannot be added to the cart.
 */
export function StockBadge({ stock, className }: { stock: number; className?: string }) {
  const state = stockState(stock)
  const label = state === 'out' ? 'Out of stock' : state === 'low' ? `Only ${stock} left` : `In stock: ${stock}`

  return (
    <Badge variant="outline" className={cn(styles[state], className)} data-testid="stock-badge" data-state={state}>
      {label}
    </Badge>
  )
}
