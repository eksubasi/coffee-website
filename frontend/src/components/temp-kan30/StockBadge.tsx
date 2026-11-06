import { Badge } from '@/components/ui/badge'

export function StockBadge({ stock }: { stock: number }) {
  return stock > 0 ? (
    <Badge variant="outline" className="border-success/30 bg-success/10 text-success" data-testid="stock-badge">
      In stock: {stock}
    </Badge>
  ) : (
    <Badge variant="outline" className="border-destructive/30 bg-destructive/10 text-destructive" data-testid="stock-badge">
      Out of stock
    </Badge>
  )
}
