import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { FormField } from '@/components/FormField'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/context/auth-context'
import { ApiError } from '@/lib/api'
import { formatCardNumber, formatExpiry, validateCard, type CardErrors, type CardInput } from '@/lib/card'
import { loadServerCart } from '@/lib/cart-sync'
import { CheckoutProblem, placeOrder, type StockProblem } from '@/lib/orders'
import { formatPrice } from '@/lib/utils'
import { selectSubtotal, useCart } from '@/store/cart'

const EMPTY_CARD: CardInput = { number: '', expiry: '', cvv: '', holder: '' }

export function CheckoutPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const items = useCart((s) => s.items)
  const subtotal = useCart(selectSubtotal)

  const [address, setAddress] = useState(user?.homeAddress ?? '') // prefilled from the profile
  const [card, setCard] = useState<CardInput>(EMPTY_CARD)
  const [errors, setErrors] = useState<CardErrors & { address?: string }>({})
  const [formError, setFormError] = useState<string>()
  const [stockProblems, setStockProblems] = useState<StockProblem[]>([])
  const [busy, setBusy] = useState(false)

  if (items.length === 0 && !busy) {
    return (
      <div className="space-y-4 py-10 text-center" data-testid="checkout-empty">
        <h1 className="text-2xl font-bold">Checkout</h1>
        <p className="text-muted-foreground">Your cart is empty.</p>
        <Button asChild>
          <Link to="/">Start shopping</Link>
        </Button>
      </div>
    )
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(undefined)
    setStockProblems([])
    const found: CardErrors & { address?: string } = validateCard(card)
    if (!address.trim()) found.address = 'Enter a delivery address.'
    setErrors(found)
    if (Object.keys(found).length > 0) return

    setBusy(true)
    try {
      const order = await placeOrder(card, address.trim())
      setCard(EMPTY_CARD) // never keep card data around
      useCart.setState({ items: [] }) // the server emptied the cart when it created the order
      navigate(`/checkout/success/${order.id}`, { replace: true })
    } catch (e) {
      if (e instanceof CheckoutProblem) {
        setStockProblems(e.problems)
        setFormError(e.message)
        void loadServerCart().catch(() => undefined) // show the live stock in the summary
      } else if (e instanceof ApiError && e.status === 400 && e.data && typeof e.data === 'object') {
        const data = e.data as Record<string, unknown>
        const fieldErrors: CardErrors & { address?: string } = {}
        const map: Record<string, keyof typeof fieldErrors> = { card_number: 'number', expiry: 'expiry', cvv: 'cvv', holder: 'holder', address: 'address' }
        for (const [key, field] of Object.entries(map)) {
          const value = data[key]
          if (value) fieldErrors[field] = Array.isArray(value) ? value.join(' ') : String(value)
        }
        setErrors(fieldErrors)
        if (Object.keys(fieldErrors).length === 0) setFormError(e.message)
      } else {
        setFormError(e instanceof ApiError && e.status !== 0 ? e.message : 'Could not reach the server. Try again.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Checkout</h1>

      <form onSubmit={onSubmit} className="grid gap-6 lg:grid-cols-[1fr_20rem]" noValidate>
        <div className="space-y-6">
          {formError && (
            <Alert variant="destructive" data-testid="checkout-error">
              <AlertTitle>{formError}</AlertTitle>
              {stockProblems.length > 0 && (
                <AlertDescription>
                  <ul className="list-disc pl-5">
                    {stockProblems.map((p) => (
                      <li key={p.productName}>
                        {p.productName}: you asked for {p.requested}, only {p.available} available.
                      </li>
                    ))}
                  </ul>
                  <Button asChild variant="outline" size="sm" className="mt-2">
                    <Link to="/cart">Review your cart</Link>
                  </Button>
                </AlertDescription>
              )}
            </Alert>
          )}

          <fieldset className="space-y-4 rounded-xl border bg-card p-5">
            <legend className="px-2 font-semibold">Delivery address</legend>
            <div className="space-y-1.5">
              <Label htmlFor="address">Address</Label>
              <textarea
                id="address"
                rows={3}
                autoComplete="street-address"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                aria-invalid={errors.address ? true : undefined}
                aria-describedby={errors.address ? 'address-error' : undefined}
                className="w-full min-w-0 rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive md:text-sm"
              />
              {errors.address && (
                <p id="address-error" className="text-xs text-destructive">
                  {errors.address}
                </p>
              )}
            </div>
          </fieldset>

          <fieldset className="space-y-4 rounded-xl border bg-card p-5">
            <legend className="px-2 font-semibold">Payment</legend>
            <FormField
              id="card-number"
              label="Card number"
              inputMode="numeric"
              autoComplete="cc-number"
              placeholder="1234 5678 9012 3456"
              value={card.number}
              onChange={(e) => setCard({ ...card, number: formatCardNumber(e.target.value) })}
              error={errors.number}
            />
            <div className="grid grid-cols-2 gap-4">
              <FormField
                id="card-expiry"
                label="Expiry (MM/YY)"
                inputMode="numeric"
                autoComplete="cc-exp"
                placeholder="MM/YY"
                value={card.expiry}
                onChange={(e) => setCard({ ...card, expiry: formatExpiry(e.target.value) })}
                error={errors.expiry}
              />
              <FormField
                id="card-cvv"
                label="CVV"
                inputMode="numeric"
                autoComplete="cc-csc"
                maxLength={4}
                type="password"
                value={card.cvv}
                onChange={(e) => setCard({ ...card, cvv: e.target.value.replace(/\D/g, '') })}
                error={errors.cvv}
              />
            </div>
            <FormField
              id="card-holder"
              label="Name on card"
              autoComplete="cc-name"
              value={card.holder}
              onChange={(e) => setCard({ ...card, holder: e.target.value })}
              error={errors.holder}
            />
            <p className="text-xs text-muted-foreground">This is a demo shop: no real payment is made.</p>
          </fieldset>
        </div>

        <aside className="h-fit space-y-4 rounded-xl border bg-card p-5" aria-label="Order summary">
          <h2 className="font-semibold">Order summary</h2>
          <ul className="space-y-2 text-sm" data-testid="checkout-items">
            {items.map((item) => (
              <li key={item.productId} className="flex justify-between gap-2">
                <span>
                  {item.quantity} × {item.name}
                </span>
                <span className="tabular-nums">{formatPrice(item.price * item.quantity)}</span>
              </li>
            ))}
          </ul>
          <div className="flex justify-between border-t pt-3 text-base font-semibold">
            <span>Total</span>
            <span data-testid="checkout-total">{formatPrice(subtotal)}</span>
          </div>
          <Button type="submit" className="w-full" disabled={busy} data-testid="place-order">
            {busy ? 'Placing order…' : `Pay ${formatPrice(subtotal)}`}
          </Button>
          <Button asChild variant="ghost" className="w-full">
            <Link to="/cart">Back to cart</Link>
          </Button>
        </aside>
      </form>
    </div>
  )
}
