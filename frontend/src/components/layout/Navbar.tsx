import { Coffee, LayoutDashboard, ShoppingCart } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'

import { Container } from '@/components/layout/Container'
import { SearchBar } from '@/components/SearchBar'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/auth-context'
import { isStaff } from '@/lib/manage-nav'
import { selectItemCount, useCart } from '@/store/cart'

export function Navbar() {
  const count = useCart(selectItemCount)
  const { status, user, logout } = useAuth()

  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
      <Container className="flex h-16 items-center justify-between">
        <Link to="/" className="flex shrink-0 items-center gap-2 text-lg font-semibold text-primary">
          <Coffee className="size-6 text-accent" aria-hidden="true" />
          <span className="hidden min-[420px]:inline">Brewnook</span>
        </Link>

        <SearchBar className="mx-2 min-w-0 max-w-md flex-1 sm:mx-3" />

        <nav aria-label="Main" className="flex shrink-0 items-center gap-0.5 text-sm font-medium sm:gap-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `hidden rounded-md px-3 py-2 hover:bg-muted sm:block ${isActive ? 'text-primary' : 'text-muted-foreground'}`
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
          {user?.role === 'customer' && (
            <NavLink
              to="/orders"
              className={({ isActive }) =>
                `rounded-md px-2 py-2 hover:bg-muted sm:px-3 ${isActive ? 'text-primary' : 'text-muted-foreground'}`
              }
            >
              Orders
            </NavLink>
          )}
          {isStaff(user?.role) && (
            <NavLink
              to="/manage"
              className="flex items-center gap-1.5 rounded-md px-2 py-2 text-muted-foreground hover:bg-muted sm:px-3"
            >
              <LayoutDashboard className="size-4" aria-hidden="true" />
              <span className="hidden sm:inline">Manage</span>
              <span className="sr-only sm:hidden">Manage</span>
            </NavLink>
          )}
          {status === 'authenticated' && user ? (
            <div className="ml-1 flex items-center gap-2 border-l pl-2 sm:ml-2 sm:pl-3">
              <span className="hidden max-w-40 truncate text-muted-foreground md:inline" data-testid="user-name">
                {user.fullName || user.email}
              </span>
              <Button variant="outline" size="sm" onClick={() => void logout()}>
                Log out
              </Button>
            </div>
          ) : (
            status === 'anonymous' && (
              <div className="ml-1 flex items-center gap-1 border-l pl-2 sm:ml-2 sm:pl-3">
                <Button asChild variant="ghost" size="sm">
                  <Link to="/login">Log in</Link>
                </Button>
                <Button asChild size="sm">
                  <Link to="/register">Sign up</Link>
                </Button>
              </div>
            )
          )}
        </nav>
      </Container>
    </header>
  )
}
