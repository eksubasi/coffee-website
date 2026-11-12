import { Badge } from '@/components/ui/badge'
import { STATUS_LABEL, type OrderStatus } from '@/lib/orders'
import { cn } from '@/lib/utils'

const STYLE: Record<OrderStatus, string> = {
  processing: 'border-accent/40 bg-accent/10 text-foreground',
  'in-transit': 'border-primary/30 bg-primary/10 text-primary',
  delivered: 'border-success/30 bg-success/10 text-success',
  cancelled: 'border-destructive/30 bg-destructive/10 text-destructive',
}

export function OrderStatusChip({ status }: { status: OrderStatus }) {
  return (
    <Badge variant="outline" className={cn(STYLE[status])} data-testid="order-status">
      {STATUS_LABEL[status]}
    </Badge>
  )
}
