import { useState } from 'react'
import { PackageOpen } from 'lucide-react'
import { Link } from 'react-router-dom'

import { ErrorState } from '@/components/ErrorState'
import { OrderStatusChip } from '@/components/OrderStatusChip'
import { EmptyState } from '@/components/temp-kan30/EmptyState'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { getOrders, type Order } from '@/lib/orders'
import { useAsync } from '@/lib/use-async'
import { formatPrice } from '@/lib/utils'

export function OrdersPage() {
  // Always fetched fresh when the page opens, so a status change by the product manager shows up on refresh.
  const first = useAsync(() => getOrders(1), [])
  const [more, setMore] = useState<Order[]>([])
  const [nextPage, setNextPage] = useState<number | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)
  const [moreError, setMoreError] = useState(false)

  if (first.loading) return <Skeleton className="h-48 w-full" aria-label="Loading your orders" />
  if (first.error || !first.data) return <ErrorState message="We couldn't load your orders." onRetry={first.reload} />

  const orders = [...first.data.orders, ...more]
  const hasMore = nextPage === null ? first.data.next !== null : nextPage !== -1
  const pageToLoad = nextPage ?? 2

  async function loadMore() {
    setLoadingMore(true)
    setMoreError(false)
    try {
      const page = await getOrders(pageToLoad)
      setMore((current) => [...current, ...page.orders])
      setNextPage(page.next ? pageToLoad + 1 : -1)
    } catch {
      setMoreError(true)
    } finally {
      setLoadingMore(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">My orders</h1>

      {orders.length === 0 ? (
        <EmptyState title="You have no orders yet" hint="Orders you place will show up here with their delivery status." />
      ) : (
        <ul className="space-y-3" data-testid="order-list">
          {orders.map((order) => (
            <li key={order.id}>
              <Link
                to={`/orders/${order.id}`}
                data-testid="order-row"
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-card p-4 hover:border-primary focus-visible:outline-2 focus-visible:outline-ring"
              >
                <div className="flex items-center gap-3">
                  <PackageOpen className="size-5 text-muted-foreground" aria-hidden="true" />
                  <div>
                    <p className="font-medium">Order #{order.id}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(order.createdAt).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })} ·{' '}
                      {order.items.reduce((n, i) => n + i.quantity, 0)} items
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <OrderStatusChip status={order.status} />
                  <span className="w-28 text-right font-semibold tabular-nums">{formatPrice(order.total)}</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}

      {moreError && <p role="alert" className="text-sm text-destructive">Could not load more orders.</p>}
      {hasMore && (
        <Button variant="outline" onClick={() => void loadMore()} disabled={loadingMore}>
          {loadingMore ? 'Loading…' : 'Load more'}
        </Button>
      )}
    </div>
  )
}
