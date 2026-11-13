import { PackageOpen, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty'

interface EmptyStateProps {
  title: string
  hint?: string
  /** Defaults to an open box. */
  icon?: LucideIcon
  /** Optional call to action, e.g. a "Continue shopping" button. */
  action?: ReactNode
}

/** "Nothing here" message for empty lists: no products, empty cart, no orders yet... */
export function EmptyState({ title, hint, icon: Icon = PackageOpen, action }: EmptyStateProps) {
  return (
    <Empty className="border" data-testid="empty-state">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <Icon />
        </EmptyMedia>
        <EmptyTitle>{title}</EmptyTitle>
        {hint && <EmptyDescription>{hint}</EmptyDescription>}
      </EmptyHeader>
      {action && <EmptyContent>{action}</EmptyContent>}
    </Empty>
  )
}
