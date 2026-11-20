import { getHealth } from '@/lib/catalog'
import { useAsync } from '@/lib/use-async'

/** Calls the health endpoint once and shows the result (KAN-19 acceptance: `/api/health` succeeds from the UI). */
export function ApiStatus() {
  const { data, error, loading } = useAsync(getHealth, [])

  let label = 'Checking API…'
  let dot = 'bg-muted-foreground'
  if (!loading && data) {
    label = `API: ${data.status}`
    dot = 'bg-success'
    if (data.db === false) {
      label += ' · database unreachable'
      dot = 'bg-accent'
    }
  } else if (!loading && error) {
    label = 'API unreachable'
    dot = 'bg-destructive'
  }

  return (
    <p className="flex items-center gap-2" role="status" data-testid="api-status">
      <span className={`size-2 rounded-full ${dot}`} aria-hidden="true" />
      {label}
    </p>
  )
}
