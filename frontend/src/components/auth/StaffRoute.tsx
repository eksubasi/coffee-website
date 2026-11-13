import { useEffect } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/context/auth-context'
import { isStaff, type StaffRole } from '@/lib/manage-nav'
import { toast } from '@/lib/toast'

/**
 * Guards the /manage area (KAN-49).
 * - not logged in  -> /login, then back here afterwards
 * - customer       -> back to the store, with a short explanation
 * - staff          -> through; pass `roles` to limit a page to some staff roles
 *
 * This only hides the UI. The backend enforces the same roles on every /api/manage endpoint.
 */
export function StaffRoute({ roles }: { roles?: StaffRole[] }) {
  const { status, user } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <Skeleton className="m-6 h-40" aria-label="Loading" />
  if (status === 'anonymous' || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  }
  if (!isStaff(user.role)) return <RedirectHome message="The management area is only for Brewnook staff." />
  if (roles && !roles.includes(user.role)) {
    // Staff, but this page belongs to another role: back to their own overview.
    return <Navigate to="/manage" replace />
  }
  return <Outlet />
}

function RedirectHome({ message }: { message: string }) {
  // The toast is a side effect, so it runs in an effect rather than during render.
  useEffect(() => {
    toast(message)
  }, [message])
  return <Navigate to="/" replace />
}
