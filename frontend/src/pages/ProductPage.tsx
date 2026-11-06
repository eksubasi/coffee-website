import { useState } from 'react'
import { Check, ChevronLeft, ShoppingCart } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { ErrorState } from '@/components/ErrorState'
import { ProductImage } from '@/components/ProductImage'
import { QuantitySelector } from '@/components/QuantitySelector'
import { StockBadge } from '@/components/temp-kan30/StockBadge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { ApiError } from '@/lib/api'
import { getProduct } from '@/lib/catalog'
import { useAsync } from '@/lib/use-async'
import { formatPrice } from '@/lib/utils'
import { useCart } from '@/store/cart'
import type { Product } from '@/types'

export function ProductPage() {
  const { id = '' } = useParams()
  const { data: product, error, loading, reload } = useAsync(() => getProduct(id), [id])

  if (loading) {
    return (
      <div className="grid gap-8 md:grid-cols-2" aria-busy="true" aria-label="Loading product">
        <Skeleton className="aspect-square w-full" />
        <div className="space-y-4">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-10 w-48" />
        </div>
      </div>
    )
  }

  if (error || !product) {
    const notFound = error instanceof ApiError && error.status === 404
    return (
      <ErrorState
        message={notFound ? "We couldn't find that product." : "We couldn't load this product."}
        onRetry={notFound ? undefined : reload}
      />
    )
  }

  // key resets the quantity / "added" message when navigating between products.
  return <ProductDetail key={product.id} product={product} />
}

function ProductDetail({ product }: { product: Product }) {
  const inCart = useCart((s) => s.items.find((item) => item.productId === product.id)?.quantity ?? 0)
  const add = useCart((s) => s.add)

  const [requested, setRequested] = useState(1)
  const [justAdded, setJustAdded] = useState(0)

  // How many more can still be added without exceeding stock (counts what is already in the cart).
  const remaining = Math.max(0, product.stock - inCart)
  const outOfStock = product.stock <= 0
  const maxedOut = !outOfStock && remaining === 0
  const quantity = Math.min(Math.max(1, requested), Math.max(1, remaining))

  const details: Array<[string, string]> = [
    ['Product ID', String(product.id)],
    ['Model', product.model],
    ['Serial number', product.serialNumber],
    ['Warranty', product.warranty],
    ['Distributor', product.distributor],
  ]
  // Coffee-specific / optional details are only shown when the product has them.
  const optionalDetails: Array<[string, string | undefined]> = [
    ['Brand', product.brand],
    ['Origin', product.origin],
    ['Weight / capacity', product.weightCapacity],
    ['Roast date', product.roastDate],
    ['Best before', product.expiryDate],
  ]
  for (const [label, value] of optionalDetails) {
    if (value) details.push([label, value])
  }

  const handleAdd = () => {
    setJustAdded(add(product, quantity))
    setRequested(1)
  }

  const addButton = (
    <Button size="lg" onClick={handleAdd} disabled={outOfStock || maxedOut} data-testid="add-to-cart">
      <ShoppingCart aria-hidden="true" />
      Add to cart
    </Button>
  )

  const disabledReason = outOfStock
    ? 'Out of stock — this item can’t be added to your cart right now.'
    : maxedOut
      ? 'You already have all available stock in your cart.'
      : undefined

  return (
    <div className="space-y-6">
      <Link
        to={`/category/${product.categoryId}`}
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary"
      >
        <ChevronLeft className="size-4" aria-hidden="true" /> Back to category
      </Link>

      <div className="grid gap-8 md:grid-cols-2">
        <ProductImage src={product.imageUrl} alt={product.name} className="aspect-square w-full rounded-xl border" />

        <div className="space-y-5">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold leading-tight">{product.name}</h1>
            <p className="text-2xl font-semibold text-primary">{formatPrice(product.price)}</p>
            <StockBadge stock={product.stock} />
          </div>

          <p className="text-muted-foreground">{product.description}</p>

          <dl className="divide-y rounded-xl border bg-card text-sm" data-testid="product-details">
            {details.map(([label, value]) => (
              <div key={label} className="flex justify-between gap-4 px-4 py-3">
                <dt className="text-muted-foreground">{label}</dt>
                <dd className="text-right font-medium">{value || '—'}</dd>
              </div>
            ))}
            <div className="flex justify-between gap-4 px-4 py-3">
              <dt className="text-muted-foreground">Quantity in stock</dt>
              <dd className="font-medium">{product.stock}</dd>
            </div>
          </dl>

          <div className="space-y-3">
            {!outOfStock && !maxedOut && (
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium">Quantity</span>
                <QuantitySelector value={quantity} max={remaining} onChange={setRequested} />
                {inCart > 0 && <span className="text-xs text-muted-foreground">{inCart} already in your cart</span>}
              </div>
            )}

            {disabledReason ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  {/* Disabled buttons don't fire pointer/focus events, so the tooltip hangs off a focusable wrapper. */}
                  <span tabIndex={0} className="inline-block rounded-md" aria-label={disabledReason}>
                    {addButton}
                  </span>
                </TooltipTrigger>
                <TooltipContent>{disabledReason}</TooltipContent>
              </Tooltip>
            ) : (
              addButton
            )}

            <p className="min-h-6 text-sm" role="status" aria-live="polite">
              {justAdded > 0 && (
                <span className="inline-flex items-center gap-1 text-success">
                  <Check className="size-4" aria-hidden="true" />
                  Added {justAdded} to your cart.{' '}
                  <Link to="/cart" className="font-medium underline">
                    View cart
                  </Link>
                </span>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
