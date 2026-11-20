import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/context/auth-context'
import type { Role } from '@/lib/auth'

/** Only logged-in users get through; others are sent to /login and come back afterwards. */
export function ProtectedRoute() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <Skeleton className="h-40 w-full" aria-label="Loading" />
  if (status === 'anonymous') return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  return <Outlet />
}

/** Logged-in users with one of the given roles get through; others see a "no access" message. */
export function RoleRoute({ roles }: { roles: Role[] }) {
  const { user } = useAuth()
  if (user && !roles.includes(user.role)) {
    return (
      <div role="alert" className="space-y-2 py-10 text-center" data-testid="no-access">
        <h1 className="text-2xl font-bold">No access</h1>
        <p className="text-muted-foreground">This page is not available for your account type.</p>
      </div>
    )
  }
  return <Outlet />
}
