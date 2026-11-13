import { CircleCheck } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { ErrorState } from '@/components/ErrorState'
import { Invoice } from '@/components/Invoice'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { getOrder, invoiceNumber } from '@/lib/orders'
import { useAsync } from '@/lib/use-async'

export function OrderConfirmationPage() {
  const { id = '' } = useParams()
  const { data: order, error, loading, reload: retry } = useAsync(() => getOrder(id), [id])

  if (loading) return <Skeleton className="h-64 w-full" aria-label="Loading your order" />
  if (error || !order) return <ErrorState message="We couldn't load your order." onRetry={retry} />

  return (
    <div className="space-y-6">
      <Alert data-testid="order-success">
        <CircleCheck />
        <AlertTitle>Thank you! Your order #{order.id} is confirmed.</AlertTitle>
        <AlertDescription>Your invoice number is {invoiceNumber(order)}. You can follow the delivery status in your orders.</AlertDescription>
      </Alert>

      <Invoice order={order} />

      <div className="flex flex-wrap gap-2 print:hidden">
        <Button asChild>
          <Link to="/orders">View my orders</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/">Continue shopping</Link>
        </Button>
      </div>
    </div>
  )
}
