import { Coffee, ShoppingCart } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'

import { Container } from '@/components/layout/Container'
import { selectItemCount, useCart } from '@/store/cart'

export function Navbar() {
  const count = useCart(selectItemCount)

  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
      <Container className="flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-primary">
          <Coffee className="size-6 text-accent" aria-hidden="true" />
          Brewnook
        </Link>

        <nav aria-label="Main" className="flex items-center gap-1 text-sm font-medium">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `rounded-md px-3 py-2 hover:bg-muted ${isActive ? 'text-primary' : 'text-muted-foreground'}`
            }
          >
            Shop
          </NavLink>
          <NavLink
            to="/cart"
            className={({ isActive }) =>
              `relative flex items-center gap-2 rounded-md px-3 py-2 hover:bg-muted ${
                isActive ? 'text-primary' : 'text-muted-foreground'
              }`
            }
            aria-label={`Cart, ${count} ${count === 1 ? 'item' : 'items'}`}
          >
            <ShoppingCart className="size-5" aria-hidden="true" />
            <span className="hidden sm:inline">Cart</span>
            {count > 0 && (
              <span
                data-testid="cart-badge"
                className="inline-flex min-w-5 items-center justify-center rounded-full bg-accent px-1.5 text-xs font-bold text-accent-foreground"
              >
                {count}
              </span>
            )}
          </NavLink>
        </nav>
      </Container>
    </header>
  )
}
