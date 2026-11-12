import { Link, useParams } from 'react-router-dom'

import { ErrorState } from '@/components/ErrorState'
import { Invoice } from '@/components/Invoice'
import { OrderStatusChip } from '@/components/OrderStatusChip'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ApiError } from '@/lib/api'
import { getOrder } from '@/lib/orders'
import { useAsync } from '@/lib/use-async'
import { formatPrice } from '@/lib/utils'

export function OrderDetailPage() {
  const { id = '' } = useParams()
  const { data: order, error, loading, reload: retry } = useAsync(() => getOrder(id), [id])

  if (loading) return <Skeleton className="h-64 w-full" aria-label="Loading the order" />
  if (error instanceof ApiError && error.status === 404) {
    return (
      <div className="space-y-4 py-10 text-center" data-testid="order-not-found">
        <h1 className="text-2xl font-bold">Order not found</h1>
        <Button asChild>
          <Link to="/orders">Back to my orders</Link>
        </Button>
      </div>
    )
  }
  if (error || !order) return <ErrorState message="We couldn't load this order." onRetry={retry} />

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <h1 className="text-2xl font-bold">Order #{order.id}</h1>
        <OrderStatusChip status={order.status} />
      </div>

      <section className="space-y-3 rounded-xl border bg-card p-5 print:hidden" aria-label="Order items">
        <ul className="divide-y" data-testid="order-items">
          {order.items.map((item) => (
            <li key={item.id} className="flex justify-between gap-3 py-2 text-sm">
              <Link to={`/product/${item.productId}`} className="hover:text-primary">
                {item.quantity} × {item.productName}
              </Link>
              <span className="tabular-nums">{formatPrice(item.total)}</span>
            </li>
          ))}
        </ul>
        <p className="flex justify-between border-t pt-3 font-semibold">
          <span>Total</span>
          <span>{formatPrice(order.total)}</span>
        </p>
        <p className="text-sm text-muted-foreground">
          Delivery address: <span className="whitespace-pre-line text-foreground">{order.address}</span>
        </p>
      </section>

      <Invoice order={order} />

      <Button asChild variant="outline" className="print:hidden">
        <Link to="/orders">Back to my orders</Link>
      </Button>
    </div>
  )
}
