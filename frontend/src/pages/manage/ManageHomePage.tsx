import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAuth } from '@/context/auth-context'
import { isStaff, ROLE_LABELS, sectionsFor } from '@/lib/manage-nav'

/** /manage — landing page of the manager area: one card per section the user's role can use. */
export function ManageHomePage() {
  const { user } = useAuth()
  const sections = sectionsFor(user?.role)
  const firstName = user?.fullName.split(' ')[0]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="type-title">{firstName ? `Welcome back, ${firstName}` : 'Overview'}</h1>
        {user && isStaff(user.role) && (
          <p className="type-caption">Signed in as {ROLE_LABELS[user.role].toLowerCase()}.</p>
        )}
      </div>

      <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {sections.map(({ path, label, description, icon: Icon }) => (
          <li key={path}>
            <Link
              to={`/manage/${path}`}
              className="group flex h-full items-start gap-4 rounded-xl border bg-card p-5 transition-shadow hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            >
              <span className="rounded-lg bg-secondary p-2.5 text-primary">
                <Icon className="size-5" aria-hidden="true" />
              </span>
              <span className="flex-1 space-y-1">
                <span className="flex items-center gap-1 font-medium group-hover:text-primary">
                  {label}
                  <ArrowRight
                    className="size-4 opacity-0 transition-opacity group-hover:opacity-100"
                    aria-hidden="true"
                  />
                </span>
                <span className="block text-sm text-muted-foreground">{description}</span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
