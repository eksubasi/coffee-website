import { useEffect, useState } from 'react'
import { ShoppingBag, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'

import { ProductImage } from '@/components/ProductImage'
import { QuantitySelector } from '@/components/QuantitySelector'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/auth-context'
import { Empty, EmptyContent, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty'
import { getProduct } from '@/lib/catalog'
import { formatPrice } from '@/lib/utils'
import { selectItemCount, selectSubtotal, useCart } from '@/store/cart'

export function CartPage() {
  const items = useCart((s) => s.items)
  const itemCount = useCart(selectItemCount)
  const subtotal = useCart(selectSubtotal)
  const { setQuantity, remove, clear } = useCart.getState()
  const [notice, setNotice] = useState<string>()
  const { user } = useAuth()
  const canCheckout = !user || user.role === 'customer'

  // On open, re-check live stock for the items in the cart so quantities can't exceed what is available.
  useEffect(() => {
    const snapshot = useCart.getState().items
    if (snapshot.length === 0) return

    let cancelled = false
    void Promise.allSettled(snapshot.map((item) => getProduct(item.productId))).then((results) => {
      if (cancelled) return
      const adjusted: string[] = []
      results.forEach((result, index) => {
        if (result.status !== 'fulfilled') return // keep the last known stock if the lookup fails
        const before = snapshot[index]
        if (result.value.stock < before.quantity) adjusted.push(before.name)
        useCart.getState().syncStock(before.productId, result.value.stock)
      })
      if (adjusted.length > 0) {
        setNotice(`Stock changed for ${adjusted.join(', ')}. We updated your cart to match what is available.`)
      }
    })
    return () => {
      cancelled = true
    }
  }, [])

  if (items.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Your cart</h1>
        {notice && (
          <Alert>
            <AlertDescription>{notice}</AlertDescription>
          </Alert>
        )}
        <Empty className="border">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <ShoppingBag />
            </EmptyMedia>
            <EmptyTitle>Your cart is empty</EmptyTitle>
          </EmptyHeader>
          <EmptyContent>
            <Button asChild>
              <Link to="/">Start shopping</Link>
            </Button>
          </EmptyContent>
        </Empty>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <h1 className="text-2xl font-bold">Your cart</h1>
        <Button variant="ghost" size="sm" onClick={clear}>
          Clear cart
        </Button>
      </div>

      {notice && (
          <Alert>
            <AlertDescription>{notice}</AlertDescription>
          </Alert>
        )}

      <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <ul className="divide-y rounded-xl border bg-card" data-testid="cart-items">
          {items.map((item) => (
            <li key={item.productId} className="flex gap-4 p-4" data-testid="cart-item">
              <Link to={`/product/${item.productId}`} className="shrink-0">
                <ProductImage src={item.imageUrl} alt={item.name} className="size-20 rounded-lg sm:size-24" />
              </Link>

              <div className="flex min-w-0 flex-1 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <Link to={`/product/${item.productId}`} className="font-medium hover:text-primary">
                    {item.name}
                  </Link>
                  <p className="text-sm text-muted-foreground">{formatPrice(item.price)} each</p>
                  {item.quantity >= item.stock && (
                    <p className="text-xs text-muted-foreground">Maximum available ({item.stock}) in your cart</p>
                  )}
                </div>

                <div className="flex items-center justify-between gap-4 sm:justify-end">
                  <QuantitySelector
                    size="sm"
                    label={`quantity of ${item.name}`}
                    value={item.quantity}
                    max={item.stock}
                    onChange={(value) => setQuantity(item.productId, value)}
                  />
                  <p className="w-20 text-right font-semibold tabular-nums" data-testid="line-total">
                    {formatPrice(item.price * item.quantity)}
                  </p>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => remove(item.productId)}
                    aria-label={`Remove ${item.name} from cart`}
                  >
                    <Trash2 />
                  </Button>
                </div>
              </div>
            </li>
          ))}
        </ul>

        <aside className="h-fit space-y-4 rounded-xl border bg-card p-5" aria-label="Order summary">
          <h2 className="font-semibold">Summary</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Items</dt>
              <dd>{itemCount}</dd>
            </div>
            <div className="flex justify-between text-base font-semibold">
              <dt>Subtotal</dt>
              <dd data-testid="subtotal">{formatPrice(subtotal)}</dd>
            </div>
          </dl>
          <p className="text-xs text-muted-foreground">Shipping and taxes are calculated at checkout.</p>
          {canCheckout ? (
            <Button asChild className="w-full" data-testid="checkout-button">
              {/* Guests are sent to log in first; their cart is merged into their account. */}
              <Link to={user ? '/checkout' : '/login'} state={user ? undefined : { from: '/checkout' }}>
                {user ? 'Proceed to checkout' : 'Log in to check out'}
              </Link>
            </Button>
          ) : (
            <p className="text-xs text-muted-foreground">Only customer accounts can check out.</p>
          )}
          <Button asChild variant="outline" className="w-full">
            <Link to="/">Continue shopping</Link>
          </Button>
        </aside>
      </div>
    </div>
  )
}
