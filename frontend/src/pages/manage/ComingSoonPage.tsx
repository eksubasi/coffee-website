import { Hammer } from 'lucide-react'

import { EmptyState } from '@/components/common/EmptyState'
import type { ManageSection } from '@/lib/manage-nav'

/** Placeholder for a manager section whose page is built in a later ticket. */
export function ComingSoonPage({ section }: { section: ManageSection }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="type-title">{section.label}</h1>
        <p className="type-caption">{section.description}</p>
      </div>
      <EmptyState icon={Hammer} title="This page is being built" hint={`Planned in ${section.ticket}.`} />
    </div>
  )
}
