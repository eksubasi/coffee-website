import { Coffee, LogOut, Store } from 'lucide-react'
import { Link, NavLink, Outlet, ScrollRestoration } from 'react-router-dom'

import { Toaster } from '@/components/common/Toaster'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/auth-context'
import { isStaff, OVERVIEW_ICON, ROLE_LABELS, sectionsFor } from '@/lib/manage-nav'
import { cn } from '@/lib/utils'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'flex items-center gap-3 whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted hover:text-foreground',
  )

/**
 * Shell for /manage/*: our own UI, not Django admin (General Advice #5).
 * Desktop: fixed sidebar on the left. Mobile: the same menu as a scrollable row under the top bar.
 */
export function ManageLayout() {
  const { user, logout } = useAuth()
  const sections = sectionsFor(user?.role)
  const OverviewIcon = OVERVIEW_ICON

  const menu = (
    <>
      <NavLink to="/manage" end className={linkClass}>
        <OverviewIcon className="size-4 shrink-0" aria-hidden="true" />
        Overview
      </NavLink>
      {sections.map(({ path, label, icon: Icon }) => (
        <NavLink key={path} to={`/manage/${path}`} className={linkClass}>
          <Icon className="size-4 shrink-0" aria-hidden="true" />
          {label}
        </NavLink>
      ))}
    </>
  )

  return (
    <div className="flex min-h-screen flex-col bg-background md:flex-row">
      <a
        href="#manage-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
      >
        Skip to content
      </a>

      <aside className="hidden w-64 shrink-0 flex-col border-r bg-card md:sticky md:top-0 md:flex md:h-screen">
        <Link to="/manage" className="flex h-16 items-center gap-2 border-b px-5 font-semibold text-primary">
          <Coffee className="size-5 text-accent" aria-hidden="true" />
          Brewnook <span className="font-normal text-muted-foreground">Manage</span>
        </Link>
        <nav aria-label="Management" className="flex flex-1 flex-col gap-1 overflow-y-auto p-3">
          {menu}
        </nav>
        <div className="border-t p-3">
          <Button asChild variant="ghost" size="sm" className="w-full justify-start">
            <Link to="/">
              <Store aria-hidden="true" /> Back to store
            </Link>
          </Button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur">
          <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6">
            <Link to="/manage" className="flex items-center gap-2 font-semibold text-primary md:hidden">
              <Coffee className="size-5 text-accent" aria-hidden="true" />
              Manage
            </Link>
            <div className="ml-auto flex items-center gap-3 text-sm">
              {user && (
                <div className="hidden text-right leading-tight sm:block">
                  <p className="font-medium" data-testid="manage-user">
                    {user.fullName || user.email}
                  </p>
                  {isStaff(user.role) && <p className="text-xs text-muted-foreground">{ROLE_LABELS[user.role]}</p>}
                </div>
              )}
              <Button variant="outline" size="sm" onClick={() => void logout()}>
                <LogOut aria-hidden="true" /> Log out
              </Button>
            </div>
          </div>
          <nav aria-label="Management" className="flex gap-1 overflow-x-auto border-t px-3 py-2 md:hidden">
            {menu}
          </nav>
        </header>

        <main id="manage-main" className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>

      <Toaster />
      <ScrollRestoration />
    </div>
  )
}
