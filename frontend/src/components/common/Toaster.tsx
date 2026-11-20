import { CircleAlert, CircleCheck, Info, X } from 'lucide-react'

import { useToasts, type ToastVariant } from '@/lib/toast'
import { cn } from '@/lib/utils'

const icons: Record<ToastVariant, typeof Info> = { default: Info, success: CircleCheck, error: CircleAlert }
const iconColor: Record<ToastVariant, string> = {
  default: 'text-accent-strong',
  success: 'text-success',
  error: 'text-destructive',
}

/** Renders the toasts created with `toast(...)`. Mount once, in the Layout. */
export function Toaster() {
  const toasts = useToasts((state) => state.toasts)
  const dismiss = useToasts((state) => state.dismiss)

  return (
    // Live region: screen readers announce new toasts. Errors use role="alert" to interrupt.
    <div
      aria-live="polite"
      className="pointer-events-none fixed inset-x-4 bottom-4 z-50 flex flex-col items-center gap-2 sm:inset-x-auto sm:right-4 sm:items-end"
    >
      {toasts.map((t) => {
        const Icon = icons[t.variant]
        return (
          <div
            key={t.id}
            role={t.variant === 'error' ? 'alert' : 'status'}
            data-testid="toast"
            data-variant={t.variant}
            className={cn(
              'pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border bg-card px-4 py-3 text-sm text-card-foreground shadow-lg',
              'animate-in fade-in slide-in-from-bottom-2',
            )}
          >
            <Icon className={cn('mt-0.5 size-4 shrink-0', iconColor[t.variant])} aria-hidden="true" />
            <p className="flex-1">{t.message}</p>
            <button
              type="button"
              onClick={() => dismiss(t.id)}
              className="-m-1 rounded p-1 text-muted-foreground hover:text-foreground"
              aria-label="Dismiss notification"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
