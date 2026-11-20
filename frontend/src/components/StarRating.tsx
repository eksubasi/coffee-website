import { Star } from 'lucide-react'
import { useState } from 'react'

import { cn } from '@/lib/utils'

/** Read-only stars. Fractions are rounded to the nearest whole star for display. */
export function StarDisplay({ value, className }: { value: number; className?: string }) {
  const filled = Math.round(value)
  return (
    <span className={cn('inline-flex items-center gap-0.5', className)} aria-hidden="true">
      {[1, 2, 3, 4, 5].map((n) => (
        <Star key={n} className={cn('size-4', n <= filled ? 'fill-accent-strong text-accent-strong' : 'text-muted-foreground/40')} />
      ))}
    </span>
  )
}

interface StarInputProps {
  value: number | null
  onChange: (score: number) => void
  disabled?: boolean
  label: string
}

/** Five buttons in a radio group: clickable, keyboard accessible, hover preview. */
export function StarInput({ value, onChange, disabled, label }: StarInputProps) {
  const [hover, setHover] = useState<number | null>(null)
  const shown = hover ?? value ?? 0
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex items-center gap-0.5" onMouseLeave={() => setHover(null)}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          role="radio"
          aria-checked={value === n}
          aria-label={`${n} star${n === 1 ? '' : 's'}`}
          disabled={disabled}
          data-testid={`rate-${n}`}
          onMouseEnter={() => setHover(n)}
          onFocus={() => setHover(n)}
          onBlur={() => setHover(null)}
          onClick={() => onChange(n)}
          className="rounded p-0.5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring disabled:opacity-50"
        >
          <Star className={cn('size-6', n <= shown ? 'fill-accent-strong text-accent-strong' : 'text-muted-foreground/40')} aria-hidden="true" />
        </button>
      ))}
    </div>
  )
}
